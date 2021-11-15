#! /usr//bin/env python3
# A file transfer client

import sys, re
from socket import *
from select import select
import os.path

# Addresses and Ports: default params
serverAddr = ('localhost', 50000)

# server select code (needs to be implemented)
try:
    args = sys.argv[1:]
    while args:
        sw = args[0]; del args[0]
        if sw in ("--serverAddr", "-s"):
            addr, port = re.split(":", args[0]); del args[0]
            serverAddr = (addr, int(port)) # addr can be a string (yippie)
        else:
            print("unexpected parameter %s" % args[0])
            print("usage: %s [--serverAddr host:port]" % sys.argv[0])
            sys.exit(1)
except:
    print("usage: %s [--serverAddr host:port]" % sys.argv[0])
    sys.exit(1)


# FILE TRANSFER PROTOCOL
NEW_FILE_BYTES = 4  # Number of consecutive 0 bytes to indicate a new file

print("CLIENT RUNNING\nConnecting to serverAddr: %s" % repr(serverAddr))
clientSocket = socket(AF_INET, SOCK_DGRAM)
print("*******************************\nInput file name with extension:")
filename = sys.stdin.readline()[:-1] # delete final \n

try:
    with open(filename, "rb") as f:  # "rb" ==  read in byte mode
        # Send 4 bytes of zeroes, file size, and filename
        # \x00\x00\x00\x00[file size][filename]
        filesize = os.path.getsize(filename)
        message = bytearray(NEW_FILE_BYTES)
        message.extend(filename.encode())
        message.append(filesize)
        clientSocket.sendto(message, serverAddr)
        confirmation, serverAddrPort = clientSocket.recvfrom(2048)
        print('Message from %s is "%s"' % (repr(serverAddrPort), confirmation.decode()))

        # Send file content
        # FILE CONTENT: [sequenceNum][filename][file content]
        sequenceNum = 0
        byte = f.read(100)          # read 100 bytes at a time
        while byte:                  # while byte is not empty, send to server
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
    print('Could not read/send file: %s' % filename)
