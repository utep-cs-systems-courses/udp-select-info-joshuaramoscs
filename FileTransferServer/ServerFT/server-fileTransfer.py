#! /usr/bin/env python3
# udp demo -- simple select-driven uppercase server

# Eric Freudenthal with mods by Adrian Veliz

import sys
import os.path
import time
from socket import *
from select import select

# Addresses and Ports
fileTransferServerAddr = ("", 50000)   # any addr, port 50,000


# Run this function when sock has rec'd first message
def recvFileName(sock):
    message, clientAddrPort = sock.recvfrom(2048)
    print("from %s: rec'd file name" % (repr(clientAddrPort)))
    filename = message.decode()
    if os.path.exists(filename): # Reject if file exists
        sock.sendto("File not sent. File already exists.".encode(), clientAddrPort)
    else:                        # Create file and call recvMsg()
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
    print("from %s: rec'd message" % (repr(clientAddrPort)))
    if len(message2) == 0: # If we reached eof
        return False

    f = open(filename, "ab")
    f.write(message2)
    f.close()
    sock.sendto(("rec'd %d bytes" % len(message2)).encode(), clientAddrPort)
    return True

# Listening to fileTransferServerAddr
fileTransferServerSocket = socket(AF_INET, SOCK_DGRAM)
fileTransferServerSocket.bind(fileTransferServerAddr)
fileTransferServerSocket.setblocking(False)


# map socket to function to call when socket is....
readSockFunc = {}               # ready for reading
writeSockFunc = {}              # ready for writing
errorSockFunc = {}              # broken

# function to call when fileTransferServerSocket is ready for reading
readSockFunc[fileTransferServerSocket] = recvFileName


print("ready to receive")
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