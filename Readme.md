# select lab

This directory contains a udp capitalization server that responds to
requests on a single port.  This server uses select to determine when
that socket is ready to read.


Your task is to modify it to respond to requests on two ports.  Select should be used to determine which port is "ready for reading."

Responses to messages sent to one port should be capitalized, requests
to messages sent to the other port should be in lower case.




