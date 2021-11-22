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
def recvMsg(sock):
    # message: [File name length][Filename][Sequence # length][Sequence #0][File Length/File content]
    message, clientAddrPort = sock.recvfrom(2048)
    print("Message from %s: rec'd: " % (repr(clientAddrPort)), message)
    filename = message[1: message[0] + 1]
    message = message[message[0] + 1:]
    sequenceNum = message[1: message[0] + 1]
    message = message[message[0] + 1:]
    # Check for EOF
    if len(message) > 0:
        # Determines if msg is a new file name or is file content
        if int.from_bytes(sequenceNum, "big") == 0:
            wFileName(sock, clientAddrPort, filename, sequenceNum, message)
        else:
            wFileContent(sock, clientAddrPort, filename, sequenceNum, message)
    else: # EOF
        print("Reached EOF of %s." % filename.decode())
        del filesInTransit[filename, clientAddrPort]
        ackCode = 2  # 2 == EOF
        ackMsg = "Rec'd EOF of %s." % filename.decode()
        sendAck(sequenceNum, ackCode, ackMsg, clientAddrPort)


# Run this function when sock has rec'd a new file message
def wFileName(sock, clientAddrPort, filename, sequenceNum, fileSize):
    if os.path.exists(filename):  # Reject if file exists
        ackCode = 1  # 1 == error
        ackMsg = "Error: File %s already exists." % filename.decode()
    else:  # Create file
        try:
            print("From %s: Message #%d, File Name: %s, File size: %d bytes" % (repr(clientAddrPort), int.from_bytes(sequenceNum, "big"), filename.decode(), int.from_bytes(fileSize, "big")))
            f = open(filename, "w")
            f.write("")
            f.close()
            filesInTransit[filename, clientAddrPort] = fileSize  # add to dictionary of files in transit
            ackCode = 0  # 0 == success
            ackMsg = "Rec'd file name %s." % filename.decode()
        except IOError:
            print("Error writing to file %s from wFileName()." % filename.decode())
            ackCode = 1  # 1 == error
            ackMsg = "Error: Could not create file %s." % filename.decode()
    sendAck(sequenceNum, ackCode, ackMsg, clientAddrPort)


# Run this function when sock has rec'd file content
def wFileContent(sock, clientAddrPort, filename, sequenceNum, message):
    # Check if file is in dictionary
    if (filename, clientAddrPort) in filesInTransit.keys():
        try:
            print("From %s: Message #%d, %d bytes" % (repr(clientAddrPort), int.from_bytes(sequenceNum, "big"), len(message)))
            f = open(filename, "ab")
            f.write(message)
            f.close()
            ackCode = 0  # 0 == success
            ackMsg = "Rec'd %s, %d bytes" % (filename.decode(), len(message))
        except IOError:
            print("Error writing to file %s from wFileContent()." % filename.decode())
            ackCode = 1  # 1 == error
            ackMsg = "Error: Could not write file %s." % filename.decode()
    else:
        ackCode = 1  # 1 == error
        ackMsg = "Error: Unknown file name %s." % filename.decode()
    sendAck(sequenceNum, ackCode, ackMsg, clientAddrPort)


def sendAck(sequenceNum, ackCode, ackMsg, clientAddrPort):
    # message: [Sequence Number][Success/Error Code][Message]
    sock.sendto(sequenceNum + ackCode.to_bytes(1, "big") + bytearray(ackMsg, 'utf-8'), clientAddrPort)


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
