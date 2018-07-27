import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;


public class Server {
    private static void startService(Socket clientSocket, BufferedReader incomingMessage, PrintWriter outgoingMessage) {
        while (clientSocket.isConnected()) {
            try {
                String clientInputStream = incomingMessage.readLine();

                if (clientInputStream != null) {
                        String[] clientArgs = parseInput(clientInputStream);
                        String clientCommand = clientArgs[0];
                    

					if (clientCommand.equalsIgnoreCase("get") && clientCommand.length() > 0 && clientCommand != null) {
						String pathname = clientArgs[1];
                        File folder = new File(pathname).getCanonicalFile();
						if (!folder.exists()) {
                        outgoingMessage.println("SERVER: Invalid filename.");
						}
						if (folder.isFile()) {
							outgoingMessage.println("sendingFile");
							BufferedInputStream fileData = new BufferedInputStream(new FileInputStream(folder));
							BufferedOutputStream outStream = new BufferedOutputStream(clientSocket.getOutputStream());
							byte buffer[] = new byte[1024];
							int read;
							while((read = fileData.read(buffer))!=-1)
							{
								outStream.write(buffer, 0, read);
								outStream.flush();
							}
							fileData.close();
						} else {
							outgoingMessage.println("SERVER: Invalid filename.");
						}

					}
					else if (clientCommand.equalsIgnoreCase("list") && clientCommand.length() > 0 && clientCommand != null) {
						String pathname = System.getProperty("user.dir");
						File folder = new File(pathname).getCanonicalFile();
						File[] listOfFiles = folder.listFiles();
						outgoingMessage.println("sendingList");
						for (int i = 0; i < listOfFiles.length; i++) {
							if (listOfFiles[i].isFile()) {
								outgoingMessage.println("File " + listOfFiles[i].getName());
							} else if (listOfFiles[i].isDirectory()) {
								outgoingMessage.println("Directory " + listOfFiles[i].getName());
							}
						}
						outgoingMessage.println("eof");
					}

					else {
						outgoingMessage.println("Server: Invalid command");
					}
                    
                }
                else if (clientInputStream.equalsIgnoreCase("close")) {
                    outgoingMessage.println("shuttingDown");
                    incomingMessage.close();
                    outgoingMessage.close();
                    clientSocket.close();
                    System.exit(0);
                }
                else {
                    outgoingMessage.println("Server: Invalid command");
                }
            }
            catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    public static String readBuffer(BufferedReader message) throws IOException {
        try {
            while(!message.ready());
            return message.readLine();
        }
        catch (IOException e) {
            System.out.println("error reading buffer: " + e.getMessage());
        }
        return null;
    }

    private static boolean isValidCommand (String consoleInput) {
        if (consoleInput.trim().contains(" ")) {
            return true;
        }
        else {
            return false;
        }
    }

    private static String[] parseInput (String consoleInput) {
        String[] parsedArray = consoleInput.split("\\s+");
        return parsedArray;
    }

    public static void main(String args[])throws IOException
    {
        ServerSocket serverSocket = null;
        Socket clientSocket= null;
		int portNum;
		if (args.length > 0) 
		{
			try 
			{
				portNum = Integer.parseInt(args[0]);
			} 
			catch (NumberFormatException e) 
			{
				System.out.println("Argument " + args[0] + " must be an integer.");
				System.exit(1);
			}
		}
		else
		{
			System.out.println("Please input an integer to be used as the port number.");
			System.exit(1);
		}
		portNum = Integer.parseInt(args[0]);
        try
        {
            serverSocket = new ServerSocket(portNum);
            System.out.println("Server: Socket initialized, now listening on: " + serverSocket.toString());
            clientSocket = serverSocket.accept();
			//System.out.println("GOT SOCKET");
            PrintWriter outgoingStream = new PrintWriter(clientSocket.getOutputStream(), true);
            BufferedReader incomingStream = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
			//System.out.println("Directory = " + System.getProperty("user.dir"));
            startService(clientSocket, incomingStream, outgoingStream);
        }
        catch(IOException e)
        {
            System.out.println("couldn't listen: " + e.getMessage());
            System.exit(0);
        }
    }
}
