#! /usr/bin/env python3
# A file transfer server

import sys
from socket import *
from select import select
import os.path
import time

# Addresses and Ports
fileTransferPort = ("", 50000)   # any addr, port 50,000

# Run this function when sock has rec'd first message
def recvFileName(sock):
    message, clientAddrPort = sock.recvfrom(2048)
    print("Message from %s: rec'd: " % (repr(clientAddrPort)), message)
    filesize = message[4]
    filename = message[5:len(message)]
    if os.path.exists(filename): # Reject if file exists
        sock.sendto("File not sent. File already exists.".encode(), clientAddrPort)
    else:                        # Create file and call recvMsg()
        print("File size is: %s bytes long" % filesize)
        f = open(filename, "w")
        f.write("")
        f.close()
        sock.sendto("rec'd file name".encode(), clientAddrPort)
        time.sleep(1)

        repeat = True
        while repeat:
            time.sleep(1)
            repeat = recvMsg(sock, filename)

# Run this function after creating a new file.
def recvMsg(sock, filename):
    message2, clientAddrPort = sock.recvfrom(2048)
    if len(message2) == 0: # If we reached eof
        return False
    print("Message #%d from %s: %d bytes" % (message2[0], (repr(clientAddrPort)), len(message2)))
    f = open(filename, "ab")
    f.write(message2[len(filename)+1:])
    f.close()
    sock.sendto(("rec'd %d bytes" % len(message2)).encode(), clientAddrPort)
    return True

# Listening to fileTransferPort
fileTransferServerSocket = socket(AF_INET, SOCK_DGRAM)
fileTransferServerSocket.bind(fileTransferPort)
fileTransferServerSocket.setblocking(False)


# map socket to function to call when socket is....
readSockFunc = {}               # ready for reading
writeSockFunc = {}              # ready for writing
errorSockFunc = {}              # broken

# function to call when fileTransferServerSocket is ready for reading
readSockFunc[fileTransferServerSocket] = recvFileName

print("SERVER RUNNING\nListening to port: %s" % repr(fileTransferPort))
print("*******************************\nReady to receive")
timeout = 5                     # select delay before giving up, in seconds
while 1:
    readRdySet, writeRdySet, errorRdySet = select(list(readSockFunc.keys()),
                                                  list(writeSockFunc.keys()),
                                                  list(errorSockFunc.keys()),
                                                  timeout)

    if not readRdySet and not writeRdySet and not errorRdySet:
        print("timeout: no events")
    for sock in readRdySet:
        readSockFunc[sock](sock)