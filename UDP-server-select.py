#! /usr/bin/env python3
# udp demo -- simple select-driven uppercase server

# Eric Freudenthal with mods by Adrian Veliz

import sys
from socket import *
from select import select

# Addresses and Ports
upperServerAddr = ("", 50000)   # any addr, port 50,000
lowerServerAddr = ("", 50001)   # any addr, port 50,001


# Function to uppercase message
def uppercase(sock):
  "run this function when sock has rec'd a message"
  message, clientAddrPort = sock.recvfrom(2048)
  print("from %s: rec'd '%s'" % (repr(clientAddrPort), message))
  modifiedMessage = message.decode().upper().encode()
  sock.sendto(modifiedMessage, clientAddrPort)

# Function to lowercase message
def lowercase(sock):
  "run this function when sock has rec'd a message"
  message, clientAddrPort = sock.recvfrom(2048)
  print("from %s: rec'd '%s'" % (repr(clientAddrPort), message))
  modifiedMessage = message.decode().lower().encode()
  sock.sendto(modifiedMessage, clientAddrPort)


# Listening to upperServerAddr
upperServerSocket = socket(AF_INET, SOCK_DGRAM)
upperServerSocket.bind(upperServerAddr)
upperServerSocket.setblocking(False)

# Listening to lowerServerAddr
lowerServerSocket = socket(AF_INET, SOCK_DGRAM)
lowerServerSocket.bind(lowerServerAddr)
lowerServerSocket.setblocking(False)

# map socket to function to call when socket is....
readSockFunc = {}               # ready for reading
writeSockFunc = {}              # ready for writing
errorSockFunc = {}              # broken

# function to call when upperServerSocket is ready for reading
readSockFunc[upperServerSocket] = uppercase
readSockFunc[lowerServerSocket] = lowercase


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

    readRdySet, writeRdySet, errorRdySet = select(list(readSockFunc.keys()),
                                                  list(writeSockFunc.keys()),
                                                  list(errorSockFunc.keys()),
                                                  timeout)

    if not readRdySet and not writeRdySet and not errorRdySet:
        print("timeout: no events")
    for sock in readRdySet:
        readSockFunc[sock](sock)
