#! /usr//bin/env python3
# A file transfer client

import sys, re
from socket import *
from select import select
import os.path

# Addresses and Ports: default params
serverAddr = ('localhost', 50000)

def newFileTransfer():
    print("CLIENT RUNNING\nConnected to serverAddr: %s" % repr(serverAddr))
    print("*******************************\nInput file name with extension:")
    filename = sys.stdin.readline()[:-1]  # delete final \n
    try:
        # Send 4 bytes of zeroes, file size, and filename
        # \x00\x00\x00\x00[filename][file size]
        filesize = os.path.getsize(filename)
        message = bytearray(4)
        message.extend(filename.encode())
        message.append(filesize)
        clientSocket.sendto(message, serverAddr)
        return filename
    except IOError:
        print('File %s is not in directory' % filename)

def recvAck(sock):
    confirmation, serverAddrPort = clientSocket.recvfrom(2048)
    print('Message from %s is "%s"' % (repr(serverAddrPort), confirmation.decode()))
    sendFile(sock)


def sendFile(sock):
    # Send file content
    # FILE CONTENT: [sequenceNum][filename][file content]
    sequenceNum = 0
    try:
        with open(filename, "rb") as f:  # "rb" ==  read in byte mode
            byte = f.read(100)  # read 100 bytes at a time
            while byte:  # while byte is not empty, send to server
                message = bytearray()
                message.extend(filename.encode())
                message.append(sequenceNum)
                message.extend(byte)
                clientSocket.sendto(message, serverAddr)
                confirmation, serverAddrPort = clientSocket.recvfrom(2048)
                print('Message from %s is "%s"' % (repr(serverAddrPort), confirmation.decode()))
                byte = f.read(100)
                sequenceNum += 1
            clientSocket.sendto(byte, serverAddr)
    except IOError:
        print('Error reading %s' % filename)


# Listening to clientSocket
clientSocket = socket(AF_INET, SOCK_DGRAM)

# map socket to function to call when socket is....
readSockFunc = {}  # ready for reading
writeSockFunc = {}  # ready for writing
errorSockFunc = {}  # broken

# function to call when fileTransferSocket is ready for reading acknowledgement
readSockFunc[clientSocket] = recvAck

filename = newFileTransfer() # Initiate a new file transfer
timoutCount = 0
timeout = 5  # select delay before giving up, in seconds
while 1:
    readRdySet, writeRdySet, errorRdySet = select(list(readSockFunc.keys()),
                                                  list(writeSockFunc.keys()),
                                                  list(errorSockFunc.keys()),
                                                  timeout)

    if not readRdySet and not writeRdySet and not errorRdySet:
        print("timeout: no events")
        timoutCount += 1
        if timoutCount == 2: # If no event after 3 timeouts, quit
            sys.exit()
    for sock in readRdySet:
        readSockFunc[sock](sock)
