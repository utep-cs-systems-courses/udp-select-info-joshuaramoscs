#! /usr//bin/env python3
# A file transfer client

import sys, re
from socket import *
from select import select
import os.path
import time

# Addresses and Ports: default params
serverAddr = ('localhost', 50000)
timeoutCount = 0
timeout = 1  # select delay before giving up, in seconds
sentTime = 0
recvTime = 0
takeNewStart = True  # True: If the rec ack is the correct sequence, False otherwise
RRT = 0


# File info
f = ""
byte = b''
filename = ""
fileSize = 0
seqByteLen = 1
sequenceNum = 0


def recvAck():
    global byte, sequenceNum, recvTime, takeNewStart, timeout
    # message: [Sequence Number][Message]
    ackMessage, serverAddrPort = clientSocket.recvfrom(2048)
    recvTime = time.time()
    ackSeqNum = ackMessage[0:seqByteLen]
    ackMessage = ackMessage[seqByteLen:]
    print('From %s: Sequence: %d, Message: "%s"' % ((serverAddrPort), int.from_bytes(ackSeqNum, "big"), ackMessage.decode()))
    if int.from_bytes(ackSeqNum, "big") == sequenceNum:               # Send next message
        RTT = recvTime - sentTime
        timeout = RTT * 2
        print("\t\t\t\t\t\t\tRTT: %.4f sec.,\tNew Time Out: %.4f sec." % (RTT, timeout))
        if len(byte) == 0 and int.from_bytes(ackSeqNum, "big") != 0:  # If length of byte == 0 here, that means that the END message was acknowledged
            print("TRANSMISSION SUCCESS!")
            sys.exit()
        else:
            byte = f.read(100)
            sequenceNum += 1
            takeNewStart = True
            sendFile()
    elif int.from_bytes(ackSeqNum, "big") < sequenceNum:              # Error, resend previous message
        sequenceNum = int.from_bytes(ackSeqNum, "big") + 1
        takeNewStart = False
        timeout *= 2
        sendFile()
    else:
        print("There was an unknown error.")


def sendFile():
    global sentTime
    try:
        if sequenceNum == 0:
            # message = [File name length][Filename][Sequence # length][Sequence #0][File size]
            message = len(filename).to_bytes(1, "big") + bytearray(filename, 'utf-8') + \
                      seqByteLen.to_bytes(1, "big") + sequenceNum.to_bytes(seqByteLen, "big") + \
                      fileSize.to_bytes(seqByteLen, "big")
        else:
            # message = [File name length][Filename][Sequence # length][Sequence #][File content]
            message = len(filename).to_bytes(1, "big") + bytearray(filename, 'utf-8') + \
                      seqByteLen.to_bytes(1, "big") + sequenceNum.to_bytes(seqByteLen, "big") + byte
        if takeNewStart: # Check if we need to reset sent time
            sentTime = time.time()
        clientSocket.sendto(message, serverAddr)
        print("Sent Msg: #%d, w/ Time Out: %.4f sec." % (sequenceNum, timeout))
    except IOError:
        print('Error sending %s' % filename)


# Function to call to initiate file transfer
def initiateTransfer():
    global f, filename, fileSize, seqByteLen
    while len(filename) == 0 or len(filename) > 255:
        print("*******************************\nInput file name with extension:")
        filename = sys.stdin.readline()[:-1]  # delete final \n
        # Windows, Linux, and MacOS have a default maximum file name length of 255, but check just in case
        if len(filename) == 0 or len(filename) > 255:
            print("File name must be less than 256 characters long. Please try again.")
        else:
            try:
                f = open(filename, "rb")
                fileSize = os.path.getsize(filename)
                # Check how many bytes it takes to send file size
                while 256 ** seqByteLen < fileSize:
                    seqByteLen += 1
                sendFile()
            except IOError:
                print('File %s is not in directory' % filename)


clientSocket = socket(AF_INET, SOCK_DGRAM)
# Map socket to function to call when socket is:
readSockFunc = {}  # ready for reading
writeSockFunc = {}  # ready for writing
errorSockFunc = {}  # broken

# function to call when fileTransferSocket is ready for reading acknowledgement
readSockFunc[clientSocket] = recvAck

print("CLIENT RUNNING\nConnecting to serverAddr: %s" % repr(serverAddr))
initiateTransfer()
while 1:
    readRdySet, writeRdySet, errorRdySet = select(list(readSockFunc.keys()),
                                                  list(writeSockFunc.keys()),
                                                  list(errorSockFunc.keys()),
                                                  timeout)

    if not readRdySet and not writeRdySet and not errorRdySet:
        timeoutCount += 1
        if timeoutCount == 6:  # If no event after 6 timeouts, quit
            print("timeout: no events, connection lost")
            sys.exit()
        else:  # try resending last message
            print("timeout: no events, resending")
            takeNewStart = False
            timeout *= 2
            sendFile()
    for sock in readRdySet:
        timeoutCount = 0
        readSockFunc[sock]()