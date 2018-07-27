import socket
import sys
import errno
import os
import getopt

#functions
def getHostPortCmd():
    """
    Function: getHostPortCmd()

    Input Paramters:
        None

    Output:
        returns the hostname of the server, data port number, control port number, and command that the user enters as
        command line arguments. Prints an error message showing how the arguments should be entered correctly if the
        arguments are entered incorrectly by the user.
     
    Description:
        See "Output". Uses getopt to parse command line arguments

    Internal Dependencies:    
        None

    External Dependencies:
        python getopt library
    """
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:c:d:lg:")
    except getopt.GetoptError as err:
        print "USAGE:  ./ftclient.py -h [hostname] -d [dataport] -c [controlport] [-l or -g <filename> for list or get] \n"
        sys.exit(1)

    hostName = None
    ctrlPort = None
    dataPort = None
    cmd = None   

    for o, a in opts:
        if o in ("-h"):
            hostName = a
        elif o in ("-c"):
            ctrlPort = a
        elif o in ("-d"):
            dataPort = a
        elif o in ("-l"):
            cmd = "list\n"
        elif o in ("-g"):
            cmd = 'get ' + a
	"""
    if '.engr.oregonstate.edu' not in hostName:
        hostName = hostName + '.engr.oregonstate.edu'
	"""
        
    return hostName, ctrlPort, dataPort, cmd

def createSocket():
    """
    Function: createSocket()

    Input Parameters:
        None

    Output:
        returns a IPv4 TCP socket, or prints an error message if the socket creation fails

    Description:
        Returns a TCP Ipv4 socket, but if the socket cant be created due to an error, an error
        message is printed and the program exits

    Internal Dependencies
        None

    External Dependencies
        python socket API
        python sys API
    """

    try:
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Create the socket
    except socket.error:
        print "Error in socket creation"
        sys.exit(1)

def connectControlSocket(controlSocket, hostName, portNum):
    """
    Function: connectControlSocket()

    Input Parameters:
        controlSocket: the socket for the TCP control connection
        hostName: the hostName of the server to connect the socket to
        portNum: the number of the port to connect the socket to

    Output:
        error messages if the socket connection is refused or some
        other error occurs when connecting the socket

    Description:
        Connects the socket to the hostname and port number provided. Handles
        any exceptions if the connection is refused or doesnt work for a different
        reason.
        
    Internal Dependencies:
        None

    External Dependencies:
        python error library
        python socket API
        python sys API
    """
    try:
        controlSocket.connect((hostName, int(portNum)))
    except socket.error as e:
        if e.errno == errno.ECONNREFUSED: #Handling the exception of the socket connection being refused
            print "error: socket connection refused"
            sys.exit(1)
        else:
            print "Error: a socket exception occured"
            sys.exit(1)

    print 'Sucessfully established TCP control connection\n'        

def receiveListCommand(controlSocket, dataSocket, dataPort):
    """
    Function: receiveListCommand()

    Input Parameters:
        controlSocket: the socket for the TCP control connection
        dataSocket: the socket for the TCP data connection

    Output:
        prints out the listing of files on the servers current working directory

    Description:
        Listens on the data socket for the server to send back the listing of files
        in its current directory and prints them on to the screen. The server
        attaches a "end" to the end of the message so the client knows when the server
        is finished sending. When the end is detected, the last three characters of
        the message received from the server are not printed. This way, only the listing
        of files on the servers current directory is printed.

    Internal Dependencies:
        None

    External Dependencies:
        python socket API
    """
    dataSocket.bind(('',int(dataPort)))
    dataSocket.listen(1)
    controlSocket.send("valid cmd received")

    while 1:
        endRcv = False
        connectionSocket, addr = dataSocket.accept()
        received = connectionSocket.recv(4096)
                
        if 'end' in received:
              print received[:len(received)-3]
              endRcv = True
        else:    
              print received

        if endRcv == True:
              connectionSocket.close()
              controlSocket.close()
              break


def receiveFile(controlSocket, dataSocket, dataPort):
    """
    Function: receiveFile()
    
    Input Parameters:
        controlSocket: the socket for the TCP control connection
        dataSocket: the socket for the TCP data connection
        dataPort: the port number used for the TCP data connection

    Output:
        prints messages showing what file is being downloaded, 
        how many bytes have been received, what to do if the file
        is already there, and an error message if the socket connection
        is broken

    Description:
        This function listens on the data socket for the server
        to send the file. If the server sends a 'the file was not found'
        message, the client prints this and exits. However if the file was
        found, the client recieves the files name and size from the server
        and sends back a message "transfer" indicating it is ready for the
        file transfer. Upon receipt of this message the server will send the
        file to the client, and the client reads the file in chunks in a while
        loop. Later a check is done to see if the file already exists on the
        client. If it does, the user is given the option to overwrite the file.
        If they choose to overwrite the file, the file is downloaded from the server
        otherwise the file is not downloaded. If the file is not found in the 
        client's current directory, the file is downloaded from the server.

    Internal Dependencies:
        None

    External Dependencies:
        python socket API
        python os API
        python sys API
    """
    dataSocket.bind(('',int(dataPort)))
    dataSocket.listen(1)
    controlSocket.send("valid cmd received")
            
    while 1:
         connectionSocket, addr = dataSocket.accept()
         received = controlSocket.recv(1024)
         if received == 'error: the file was not found':
                print received + '\n'
                sys.exit(1) #Kernel will close sockets for us
         else:
                #Recieve the file from the server
                fileName = received.split(":")[0]
                fileSize = received.split(":")[1]
                controlSocket.send("transfer")
                print 'Getting file \''+fileName+'\', ' + fileSize + ' bytes\n'

                fileSize = int(fileSize)
                msg = ''

                while len(msg) < fileSize:
                    chunk = connectionSocket.recv(fileSize - len(msg))
                    print 'Received ' + str(len(chunk)) + ' bytes...\n'
                    if chunk == '':
                        print 'Socket connection broken\n'
                        sys.exit(1)

                    msg = msg + chunk
                    
                print 'file has been transmitted\n' 

                if os.path.isfile(fileName):
                    response = raw_input(fileName + " exists. Do you want to overwrite it?(y/n): ")
                    if response != 'y':
                        print 'File will not be saved\n'
                        connectionSocket.close()
                        controlSocket.close()
                        return 
                        
                with open(fileName, 'w') as out:
                    out.write(msg)
                        
                print 'The file has been saved\n'    
                return


def sendHostPortCmd(controlSocket, cmd, dataPort):
    """
    Function: sendHostPortCmd()
    
    Input Parameters:
        the socket to receive and send data over the TCP control connection (controlSocket)
        the command to send to the server (cmd)
        the number for the data port for the TCP data connection to send to the server (dataPort)

    Output:
        Prints out whatever the server sends back over the TCP control connection

    Description:
        Sends the hostname of the client, port number for the data connection, and command entered
        by the user to the server. It sends this over the TCP control connection. The server will send
        back a message indicating if a valid command was sent or not. If the command sent was invalid, 
        the sockets for the data and control connections are closed and the function ends with a return 
        statement. If the command was valid, an appropriate function is executed to receive the results
        of the command, whether it be a 'list' command or a 'get' command
        
    Internal Dependencies:
        receiveListCommand()
        receiveFile()

    External Dependencies:
        python socket API
    """

    #send the command that the user passed in earlier as well as the data port number and host
    controlSocket.send(cmd)    
    recieved = controlSocket.recv(1024)
    print recieved

    if 'sending' in recieved:
        print "TEST\n"
        dataSocket = createSocket() #Create data socket
        if "list" == cmd:
            #The function to get the results of the list command from the server
            #and show it on screen
            receiveListCommand(controlSocket, dataSocket, dataPort)
            
        if 'get ' in cmd and len(cmd) > 4:
            #Function to receive the file from the server
            receiveFile(controlSocket, dataSocket, dataPort)

    else:
        dataSocket.close()
        controlSocket.close()
        return


#Main program---------------------------

#Get the hostname and port number
hostName, ctrlPort, dataPort, cmd = getHostPortCmd() 
print "GetHostPortCmd worked\n"

#Make the socket for the client
controlSocket = createSocket() 
print "createSocket worked\n"

#connect the client socket
connectControlSocket(controlSocket, hostName, ctrlPort)
print "connectControlSocket worked\n" 

#get the command from user input and send to the server, as well as the hostname and dataport number
sendHostPortCmd(controlSocket, cmd, dataPort) 



