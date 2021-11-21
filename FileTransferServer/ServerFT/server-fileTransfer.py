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
    # message = [File name length][Filename][Sequence # length][Sequence #0][File Length/File content]
    #print("Message from %s: rec'd: " % (repr(clientAddrPort)), message)
    if len(message) > 0:
        filename = message[1: message[0]+1]
        message = message[message[0]+1:]
        sequenceNum = message[1: message[0]+1]
        message = message[message[0]+1:]
        if int.from_bytes(sequenceNum, "big") == 0:
            recvFileName(sock, clientAddrPort, filename, sequenceNum, message)
        else:
            recvFileContent(sock, clientAddrPort, filename, sequenceNum, message)
    else:
        print("EOF")

# Run this function when sock has rec'd a new file message
def recvFileName(sock, clientAddrPort, filename, sequenceNum, fileSize):
    if os.path.exists(filename):  # Reject if file exists
        sock.sendto("File not sent. File already exists.".encode(), clientAddrPort)
    else:  # Create file
        print("From %s: Message #%d, File Name: %s, File size: %d bytes" % (repr(clientAddrPort), int.from_bytes(sequenceNum, "big"), filename.decode(), int.from_bytes(fileSize, "big")))
        f = open(filename, "w")
        f.write("")
        f.close()
        filesInTransit[filename] = fileSize  # add to dictionary of files in transit
        sock.sendto("rec'd file name".encode(), clientAddrPort)


# Run this function after creating a new file.
def recvFileContent(sock, clientAddrPort, filename, sequenceNum, message):
    if len(message) == 0:  # If we reached eof                MOVE OR FIX THIS
        del filesInTransit[filename]
        sock.sendto(("rec'd %d bytes" % len(message)).encode(), clientAddrPort)
    else:
        print("From %s: Message #%d, %d bytes" % (repr(clientAddrPort), int.from_bytes(sequenceNum, "big"), len(message)))
        f = open(filename, "ab")
        f.write(message)
        f.close()
        sock.sendto(("rec'd %d bytes" % (len(message))).encode(), clientAddrPort)


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
