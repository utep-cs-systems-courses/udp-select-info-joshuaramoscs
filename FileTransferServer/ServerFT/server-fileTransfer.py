#! /usr/bin/env python3
# A file transfer server

from socket import *
from select import select
import os.path

# Addresses and Ports
fileTransferPort = ("", 50000)  # any addr, port 50,000
# Dictionary of all files in transit
filesInTransit = {}


# Run this function when receiving a message
# Determines if msg is a new file name or file content
def recvMsg(sock):
    message, clientAddrPort = sock.recvfrom(2048)
    #print("Message from %s: rec'd: " % (repr(clientAddrPort)), message)
    if message[0:4] == b'\x00\x00\x00\x00':  # Check if its a new file
        recvFileName(sock, message[4:], clientAddrPort)
    else:                                    # Else, check if msg belongs to file in transit, let client time out if not
        filenameSet = list(filesInTransit)
        for fn in filenameSet:
            if message[0:len(fn)] == fn:
                recvFileContent(sock, fn, message[len(fn):], clientAddrPort)  # receive file content
            break


# Run this function when sock has rec'd a new file message
def recvFileName(sock, message, clientAddrPort):
    filename = message[0:len(message) - 1]
    filesize = message[len(message) - 1]
    if os.path.exists(filename):  # Reject if file exists
        sock.sendto("File not sent. File already exists.".encode(), clientAddrPort)
    else:                         # Create file
        print("File Name: %s, File size is: %s bytes long" % (filename.decode(), filesize))
        f = open(filename, "w")
        f.write("")
        f.close()
        filesInTransit[filename] = filesize  # add to dictionary of files in transit
        sock.sendto("rec'd file name".encode(), clientAddrPort)


# Run this function after creating a new file.
def recvFileContent(sock, filename, message, clientAddrPort):
    if len(message) == 0:  # If we reached eof
        del filesInTransit[filename]
        sock.sendto(("rec'd %d bytes" % len(message)).encode(), clientAddrPort)
    else:
        print("Message #%d from %s: %d bytes" % (message[0], (repr(clientAddrPort)), len(message)-1))
        f = open(filename, "ab")
        f.write(message[1:])
        f.close()
        sock.sendto(("rec'd %d bytes" % (len(message)-1)).encode(), clientAddrPort)


# Listening to fileTransferPort
fileTransferServerSocket = socket(AF_INET, SOCK_DGRAM)
fileTransferServerSocket.bind(fileTransferPort)
fileTransferServerSocket.setblocking(False)

# map socket to function to call when socket is....
readSockFunc = {}  # ready for reading
writeSockFunc = {}  # ready for writing
errorSockFunc = {}  # broken

# function to call when fileTransferServerSocket is ready for reading
readSockFunc[fileTransferServerSocket] = recvMsg

print("SERVER RUNNING\nListening to port: %s" % repr(fileTransferPort))
print("*******************************\nReady to receive")
timeout = 5  # select delay before giving up, in seconds
while 1:
    readRdySet, writeRdySet, errorRdySet = select(list(readSockFunc.keys()),
                                                  list(writeSockFunc.keys()),
                                                  list(errorSockFunc.keys()),
                                                  timeout)

    if not readRdySet and not writeRdySet and not errorRdySet:
        print("timeout: no events")
    for sock in readRdySet:
        readSockFunc[sock](sock)
