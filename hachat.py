# coding = utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import sys
from peer import Peer

if len(sys.argv) == 3:
    peer = Peer(firstHost = (sys.argv[1], sys.argv[2]))
else:
    peer = Peer()
