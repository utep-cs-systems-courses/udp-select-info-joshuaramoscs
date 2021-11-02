#! /usr/bin/env python3
# udp demo -- simple select-driven uppercase server

# Eric Freudenthal with mods by Adrian Veliz

import sys
from socket import *
from select import select

# Addresses and Ports
fileTransferServerAddr = ("", 50000)   # any addr, port 50,000


# Run this function when sock has rec'd a message
def recvMsg(sock):
  message, clientAddrPort = sock.recvfrom(2048)
  print("from %s: rec'd file" % (repr(clientAddrPort)))
  fileMessage = message.decode()

  f = open("serverFile.txt", "w")
  f.write(fileMessage)
  f.close()

  sock.sendto("rec'd file".encode(), clientAddrPort)


# Listening to fileTransferServerAddr
fileTransferServerSocket = socket(AF_INET, SOCK_DGRAM)
fileTransferServerSocket.bind(fileTransferServerAddr)
fileTransferServerSocket.setblocking(False)


# map socket to function to call when socket is....
readSockFunc = {}               # ready for reading
writeSockFunc = {}              # ready for writing
errorSockFunc = {}              # broken

# function to call when upperServerSocket is ready for reading
readSockFunc[fileTransferServerSocket] = recvMsg


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
        print("in Loop")
        readSockFunc[sock](sock)