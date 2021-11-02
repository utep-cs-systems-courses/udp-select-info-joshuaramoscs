#! /usr//bin/env python3
# File transfer client.  Modified from Kurose/Ross by Eric Freudenthal 2016

from socket import *
import sys, re

# default params
serverAddr = ('localhost', 50000)

# server select code, could probably delete
try:
    args = sys.argv[1:]
    while args:
        sw = args[0]; del args[0]
        if sw in ("--serverAddr", "-s"):
            addr, port = re.split(":", args[0]); del args[0]
            serverAddr = (addr, int(port)) # addr can be a string (yippie)
        else:
            print("unexpected parameter %s" % args[0])
            usage();
except:
    print("usage: %s [--serverAddr host:port]" % sys.argv[0])
    sys.exit(1)


# File transfer protocol
print("serverAddr = %s" % repr(serverAddr))
clientSocket = socket(AF_INET, SOCK_DGRAM)

print("Input file name with extension:")
filename = sys.stdin.readline()[:-1] # delete final \n

try:
    with open(filename, "rb") as f:  # "rb" ==  read in byte mode
        # Send filename
        clientSocket.sendto(filename.encode(), serverAddr)
        print('Message from %s is "%s"' % (repr(serverAddrPort), confirmation.decode())
        # Send file content
        byte = f.read(2048)          # read 2048 bytes at a time
        while byte:                  # while byte is not empty, send to server
            clientSocket.sendto(byte, serverAddr)
            confirmation, serverAddrPort = clientSocket.recvfrom(2048)
            print('Message from %s is "%s"' % (repr(serverAddrPort), confirmation.decode())
            byte = f.read(2048)
            
except IOError:
    print('Could not read file %s' % filename)
