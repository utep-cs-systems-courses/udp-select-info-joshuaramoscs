#! /usr//bin/env python3
# udp demo client.  Modified from Kurose/Ross by Eric Freudenthal 2016

from socket import *


# default params
serverAddr = ('localhost', 50000)

import sys, re

def usage():
    print("usage: %s [--serverAddr host:port]"  % sys.argv[0])
    sys.exit(1)

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
    usage()


print("serverAddr = %s" % repr(serverAddr))

clientSocket = socket(AF_INET, SOCK_DGRAM)
print("Input file name")
filename = sys.stdin.readline()[:-1]     # delete final \n
f = open(filename, "r")
fileContent = f.read()
f.close()

clientSocket.sendto(fileContent.encode(), serverAddr)
confirmation, serverAddrPort = clientSocket.recvfrom(2048)
print('Message from %s is "%s"' % (repr(serverAddrPort), confirmation.decode()))
