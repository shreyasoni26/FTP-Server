import socket
import sys
import time
import os
import struct
import threading
import ssl
print( "\nWelcome to the FTP server.\n\nTo get started, connect a client.")


 
# Initialise socket stuff
#TCP_IP = "127.0.0.1" # Only a local serverp
TCP_PORT = 1456 # Just a random choice
BUFFER_SIZE = 1048 # Standard size


def upld(conn, addr):
    # Send message once server is ready to recieve file details
    conn.send(b"1")
    # Recieve file name length, then file name
    file_name_size = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_size)
    # Send message to let client know server is ready for document content
    conn.send(b"1")
    # Recieve file size
    file_size = struct.unpack("i", conn.recv(4))[0]
    # Initialise and enter loop to recive file content
    start_time = time.time()
    output_file = open(file_name, "wb")
    # This keeps track of how many bytes we have recieved, so we know when to stop the loop
    bytes_received = 0
    print (f"\nRecieving from {addr}...")
    while bytes_received < file_size:
        l = conn.recv(BUFFER_SIZE)
        output_file.write(l)
        bytes_received += len(l)
       
    output_file.close()
    print (f"\nRecieved file: {file_name}")
    # Send upload performance details
    conn.send(struct.pack("f", time.time() - start_time))
    conn.send(struct.pack("i", file_size))
    return

def list_files(conn, addr):
    print ("Listing files...")
    # Get list of files in directory
    listing = os.listdir(os.getcwd())
    # Send over the number of files, so the client knows what to expect (and avoid some errors)
    conn.send(struct.pack("i", len(listing)))
    data = conn.recv(BUFFER_SIZE)
    print("exist {}".format(data))
    total_directory_size = 0
    # Send over the file names and sizes whilst totaling the directory size
    for i in listing:
        # File name size
        conn.send(struct.pack("i", sys.getsizeof(i)))
        # File name
        conn.send(i.encode())
        # File content size
        #print(type(struct.pack("i",os.path.getsize(i))))
        #conn.send(struct.pack("i", os.path.getsize(i)))
        #print("are we here")
        total_directory_size += os.path.getsize(i)
        # Make sure that the client and server are synchronized
        conn.recv(BUFFER_SIZE)
    
    conn.recv(BUFFER_SIZE)
    # Sum of file sizes in directory
    conn.send(struct.pack("i", total_directory_size))
    #Final check
    conn.recv(BUFFER_SIZE)
    print (f"Successfully sent file listing to {addr}")
    return

def dwld(conn, addr):
    conn.send(b"1")
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    print (file_name_length)
    file_name = conn.recv(file_name_length)
    print(file_name)
    if os.path.isfile(file_name):
        # Then the file exists, and send file size
        conn.send(struct.pack("i", os.path.getsize(file_name)))
    else:
        # Then the file doesn't exist, and send error code
        print ("File name not valid")
        conn.send(struct.pack("i", -1))
        return
    # Wait for ok to send file
    conn.recv(BUFFER_SIZE)
    # Enter loop to send file
    start_time = time.time()
    print ("Sending file...")
    content = open(file_name, "rb")
    # Again, break into chunks defined by BUFFER_SIZE
    l = content.read(BUFFER_SIZE)
    while l:
        conn.send(l)
        l = content.read(BUFFER_SIZE)
    content.close()
    # Get client go-ahead, then send download details
    conn.recv(BUFFER_SIZE)
    conn.send(struct.pack("f", time.time() - start_time))
    return


def delf(conn, addr):
    # Send go-ahead
    conn.send(b"1")
    # Get file details
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_length)
    # Check file exists
    if os.path.isfile(file_name):
        conn.send(struct.pack("i", 1))
    else:
        # Then the file doesn't exist
        conn.send(struct.pack("i", -1))
    # Wait for deletion conformation
    confirm_delete = conn.recv(BUFFER_SIZE)

    if confirm_delete == b"Y":
        try:
            # Delete file
            os.remove(file_name)
            conn.send(struct.pack("i", 1))
        except:
            # Unable to delete file
            print ("Failed to delete {}".format(file_name))
            conn.send(struct.pack("i", -1))
    else:
        # User abandoned deletion
        print("Delete abandoned by client!")
        return


def quit(conn, addr):
    # Send quit conformation
    conn.send(b"1")
    # Close and restart the server
    conn.close()
    # s.close()
    # os.execl(sys.executable, sys.executable, *sys.argv)

    
    
def handle_client(conn, addr):
    connected = True
    while connected:
        # Enter into a while loop to recieve commands from client
        print("\n\nWaiting for instruction")
        data = conn.recv(BUFFER_SIZE)
        print (f"\nRecieved instruction: {data} from {addr}")
        # Check the command and respond correctly
        if data == b"UPLD":
            upld(conn, addr)
        elif data == b"LIST":
            list_files(conn, addr)
        elif data == b"DWLD":
            dwld(conn, addr)
        elif data == b"DELF":
            delf(conn, addr)
        elif data == b"QUIT":
            print(f"Client {addr} disconnecting forever :/")
            connected = False
            quit(conn, addr)
        # Reset the data to loop 
        data = None
    
        

def main():
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', TCP_PORT))
    s.listen(1)    
    print(f"Server is listening")
    
    while True:
            conn, addr = s.accept()
            thread = threading.Thread(target = handle_client, args=(conn, addr))
            thread.start()
            print(f"\nActive connections: {threading.active_count() - 1}")
    
if __name__ == "__main__":
    main()
    
    