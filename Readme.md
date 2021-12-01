# UDP select lab

The "FileTransferServer" directory contains a udp-like server/client protocol.

The "demo UDP" directory contains a udp capitalization server that responds to
requests on a single port.  This server uses select to determine when
that socket is ready to read.