# coding = utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import argparse
import re
import random
from peer import Peer

parser = argparse.ArgumentParser(description="start peer with arguments")
parser.add_argument("-p", help="Port to listen on")
parser.add_argument("-l", help="hachat link (ex. localhost:12345)")
parser.add_argument("-n", help="set own name")
args = parser.parse_args()

# set name
name = args.n
if name == None:
    nr = random.randint(0, 99999)
    name = "user" + str(nr)

if args.l != None:
    (hostIP, hostPort) = re.split(":", args.l, 1)
    peer = Peer(firstHost = (hostIP, hostPort), port = args.p, name = name)
else:
    peer = Peer(port = args.p, name = name)
