#! /usr/bin/env python3
# A file transfer server

from socket import *
from select import select
import os.path

# Addresses and Ports
fileTransferPort = ("", 50001)  # any addr, port 50,000
lastSequenceNum = -1


# Run this function when receiving a message
def recvMsg(sock):
    global lastSequenceNum
    # message: [File name length][Filename][Sequence # length][Sequence #0][File Length/File content]
    message, clientAddrPort = sock.recvfrom(2048)
    # print("Message from %s: rec'd: " % (repr(clientAddrPort)), message)
    filename = message[1: message[0] + 1]
    message = message[message[0] + 1:]
    seqByteLen = message[0]
    sequenceNum = message[1: seqByteLen+1]
    message = message[seqByteLen + 1:]
    if len(message) > 0:                                # Check if not EOF
        wFileContent(sock, clientAddrPort, filename, seqByteLen, sequenceNum, message)
    else:                                               # EOF
        print("Reached EOF of %s." % filename.decode())
        ackMsg = "Rec'd EOF of %s." % filename.decode()
        sock.sendto(sequenceNum + bytearray(ackMsg, 'utf-8'), clientAddrPort)  # message: [Sequence Number][Message]
        print("\t\t\t\t\t\t\tAck'ed msg #%d" % int.from_bytes(sequenceNum, "big"))
        lastSequenceNum = -1


# Run this function when sock has rec'd file content
def wFileContent(sock, clientAddrPort, filename, seqByteLen, sequenceNum, message):
    global lastSequenceNum
    if int.from_bytes(sequenceNum, "big") == 0:                                # If new file
        if os.path.exists(filename):                                           # Reject if file exists
            ackMsg = "Error: File %s already exists." % filename.decode()
        else:                                                                  # Create file
            print("From %s: New File Transfer" % repr(clientAddrPort))
            # lastSequenceNum = 0
            ackMsg = "Rec'd file name %s & file size %d bytes." % (filename.decode(), int.from_bytes(message, "big"))
        lastSequenceNum = 0
        sock.sendto(lastSequenceNum.to_bytes(seqByteLen, "big") + bytearray(ackMsg, 'utf-8'), clientAddrPort)
        print("\t\t\t\t\t\t\tAck'ed msg #%d" % int.from_bytes(sequenceNum, "big"))
    else:                                                                      # If file content
        print("From %s: Message #%d, %d bytes" % (repr(clientAddrPort), int.from_bytes(sequenceNum, "big"), len(message)))
        ackMsg = "Rec'd %s, %d bytes" % (filename.decode(), len(message))
        if int.from_bytes(sequenceNum, "big") == lastSequenceNum + 1:          # If sequence num is the correct one
            try:
                f = open(filename, "ab+")
                f.write(message)
                f.close()
                sock.sendto(sequenceNum + bytearray(ackMsg, 'utf-8'), clientAddrPort)
                print("\t\t\t\t\t\t\tAck'ed msg #%d" % int.from_bytes(sequenceNum, "big"))
                lastSequenceNum += 1
            except IOError:
                print("Error writing to file %s from wFileContent()." % filename.decode())
        else:                                                                   # Resend ack for last correct sequence
            sock.sendto(lastSequenceNum.to_bytes(seqByteLen, "big") + bytearray(ackMsg, 'utf-8'), clientAddrPort)
            print("\t\t\t\t\t\t\tAck'ed msg #%d" % int.from_bytes(sequenceNum, "big"))


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
        lastSequenceNum = -1
    for sock in readRdySet:
        readSockFunc[sock](sock)
