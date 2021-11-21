#! /usr//bin/env python3
# A file transfer client

import sys, re
from socket import *
from select import select
import os.path
import time

# Addresses and Ports: default params
serverAddr = ('localhost', 50000)

# File info
filename = ""
fileSize = 0
seqByteLen = 1
sequenceNum = 0


# Client service info
sentTime = 0
recvTime = 0

# Function to call to request filename from user
def reqFileName():
    global filename
    while len(filename) == 0 or len(filename) > 255:
        print("*******************************\nInput file name with extension:")
        filename = sys.stdin.readline()[:-1]  # delete final \n
        # Windows, Linux, and MacOS have a default maximum file name length of 255, but check just in case
        if len(filename) == 0 or len(filename) > 255:
            print("File name must be less than 256 characters long. Please try again.")

# Function to call when initiating file transfer
def initFileTransfer():
    global filename
    global fileSize
    global seqByteLen
    print("CLIENT RUNNING\nConnecting to serverAddr: %s" % repr(serverAddr))
    reqFileName()
    try:
        fileSize = os.path.getsize(filename)
        # Check how many bytes it takes to send file size
        while 256 ** seqByteLen < fileSize:
            seqByteLen += 1
        # message = [File name length][Filename][Sequence # length][Sequence #0][File size]
        message = len(filename).to_bytes(1, "big") + bytearray(filename, 'utf-8') + \
                  seqByteLen.to_bytes(1, "big") + sequenceNum.to_bytes(seqByteLen, "big") + \
                  fileSize.to_bytes(seqByteLen, "big")
        clientSocket.sendto(message, serverAddr)
    except IOError:
        print('File %s is not in directory' % filename)


def sendFile():
    confirmation, serverAddrPort = clientSocket.recvfrom(2048)
    print('From %s: Message: "%s"' % (repr(serverAddrPort), confirmation.decode()))
    global sequenceNum  # Send file content
    try:
        with open(filename, "rb") as f:  # "rb" ==  read in byte mode
            byte = f.read(100)  # read 100 bytes at a time
            while byte:  # while byte is not empty, send to server
                # message = [File name length][Filename][Sequence # length][Sequence #0][File content]
                sequenceNum += 1
                message = len(filename).to_bytes(1, "big") + bytearray(filename, 'utf-8') + \
                          seqByteLen.to_bytes(1,"big") + sequenceNum.to_bytes(seqByteLen, "big") + byte
                sentTime = time.time()
                clientSocket.sendto(message, serverAddr)
                confirmation, serverAddrPort = clientSocket.recvfrom(2048)
                recvTime = time.time()
                print('From %s: Message: "%s", RTT: %.4f ms.' % (repr(serverAddrPort), confirmation.decode(), (1000 * (recvTime - sentTime))))
                byte = f.read(100)
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
readSockFunc[clientSocket] = sendFile

initFileTransfer()  # Initiate a new file transfer
timoutCount = 0
timeout = 1  # select delay before giving up, in seconds

while 1:
    readRdySet, writeRdySet, errorRdySet = select(list(readSockFunc.keys()),
                                                  list(writeSockFunc.keys()),
                                                  list(errorSockFunc.keys()),
                                                  timeout)

    if not readRdySet and not writeRdySet and not errorRdySet:
        print("timeout: no events")
        timoutCount += 1
        if timoutCount == 2:  # If no event after 3 timeouts, quit
            sys.exit()
    for sock in readRdySet:
        readSockFunc[sock]()
