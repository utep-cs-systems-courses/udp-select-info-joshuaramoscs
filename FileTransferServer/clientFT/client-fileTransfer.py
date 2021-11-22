#! /usr//bin/env python3
# A file transfer client

import sys, re
from socket import *
from select import select
import os.path
import time

# Addresses and Ports: default params
serverAddr = ('localhost', 50000)
windowSize = 4

# File info
f = ""
byte = b''
filename = ""
fileSize = 0
seqByteLen = 1
sequenceNum = 0
sendHist = {}

# Client service info
sentTime = 0
recvTime = 0


def recvAck():
    global byte, sequenceNum, recvTime
    # message: [Sequence Number][Success/Error Code][Message]
    ackMessage, serverAddrPort = clientSocket.recvfrom(2048)
    recvTime = time.time()
    ackSeqNum = ackMessage[0:seqByteLen]
    ackCode = ackMessage[seqByteLen]
    ackMessage = ackMessage[seqByteLen+1:]
    print('From %s: Sequence: %d, Message: "%s", RTT: %.4f ms.' % ((serverAddrPort), int.from_bytes(ackSeqNum, "big"), ackMessage.decode(), (1000 * (recvTime - sentTime))))
    if ackCode == 0: # Send next message
        if len(byte) != 0:
            byte = f.read(100)
            sequenceNum += 1
            sendFile()
    elif ackCode == 1:  # Error, resend previous message
        if int.from_bytes(ackSeqNum, "big") == 0:
            print("Already sent this file")
        else:
            sendFile()
    elif ackCode == 2:  # EOF
        print("FILE TRANSFER SUCCESS!")
    else:
        print("There was an unknown error.")


def sendFile():
    global sentTime
    try:
        # message = [File name length][Filename][Sequence # length][Sequence #0][File content]
        message = len(filename).to_bytes(1, "big") + bytearray(filename, 'utf-8') + \
                  seqByteLen.to_bytes(1, "big") + sequenceNum.to_bytes(seqByteLen, "big") + byte
        sentTime = time.time()
        clientSocket.sendto(message, serverAddr)
        print("Sent Msg: #%d" % sequenceNum)
    except IOError:
        print('Error reading %s' % filename)


# Function to call when initiating file transfer
def initFileTransfer():
    global f, byte, fileSize, seqByteLen, sequenceNum
    print("CLIENT RUNNING\nConnecting to serverAddr: %s" % repr(serverAddr))
    reqFileName()
    # Send first four messages
    try:
        f = open(filename, "rb")
        fileSize = os.path.getsize(filename)
        # Check how many bytes it takes to send file size
        while 256 ** seqByteLen < fileSize:
            seqByteLen += 1
        # message = [File name length][Filename][Sequence # length][Sequence #0][File size]
        message = len(filename).to_bytes(1, "big") + bytearray(filename, 'utf-8') + \
                  seqByteLen.to_bytes(1, "big") + sequenceNum.to_bytes(seqByteLen, "big") + \
                  fileSize.to_bytes(seqByteLen, "big")
        sendHist[sequenceNum] = message
        clientSocket.sendto(message, serverAddr)
        print("Sent Msg: #%d" % sequenceNum)
        for i in range(0, windowSize-1):
            byte = f.read(100)
            sequenceNum += 1
            sendFile()
    except IOError:
        print('File %s is not in directory' % filename)


# Function to call to request filename from user
def reqFileName():
    global filename
    while len(filename) == 0 or len(filename) > 255:
        print("*******************************\nInput file name with extension:")
        filename = sys.stdin.readline()[:-1]  # delete final \n
        # Windows, Linux, and MacOS have a default maximum file name length of 255, but check just in case
        if len(filename) == 0 or len(filename) > 255:
            print("File name must be less than 256 characters long. Please try again.")


clientSocket = socket(AF_INET, SOCK_DGRAM)
# Map socket to function to call when socket is:
readSockFunc = {}  # ready for reading
writeSockFunc = {}  # ready for writing
errorSockFunc = {}  # broken

# function to call when fileTransferSocket is ready for reading acknowledgement
readSockFunc[clientSocket] = recvAck

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
