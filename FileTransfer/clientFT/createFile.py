#! /usr/bin/env python3
filename = "y.txt"
msgMultiplier = 100

counter = 0
f = open(filename, "a")
while counter < msgMultiplier:
    f.write("%d\nHello this file is from the client.\n\nEnjoy!\n\n" % counter)
    counter += 1
f.close()