#!/usr/bin/env python
# coding = utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import argparse
import logging
import re
import random
import const
from peer import Peer


parser = argparse.ArgumentParser(description="start peer with arguments")
parser.add_argument("-p", "--port", help="Port to listen on")
parser.add_argument("-l", "--link", help="hachat link (ex. localhost:12345)")
parser.add_argument("-n", "--name", help="set own name")
parser.add_argument("-v", "--verbose", action="store_true", default=False, help="show p2p-information")
args = parser.parse_args()

# initialise logger
if args.verbose == True:
    logging.basicConfig(level=logging.DEBUG)

# set name
name = args.name
if name == None:
    nr = random.randint(0, 99999)
    name = "user" + str(nr)

if args.link != None:
    (hostIP, hostPort) = re.split(":", args.link, 1)
    peer = Peer(firstHost = (hostIP, hostPort), port = args.port, name = name)
else:
    peer = Peer(port = args.port, name = name)




   

