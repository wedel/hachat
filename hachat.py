# coding = utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import argparse
import re
from peer import Peer

parser = argparse.ArgumentParser(description="start peer with arguments")
parser.add_argument("-p")
parser.add_argument("-l")
args = parser.parse_args()

print args
print args.l

if args.l != None:
    (hostIP, hostPort) = re.split(":", args.l, 1)
    peer = Peer(firstHost = (hostIP, hostPort))
else:
    peer = Peer()
