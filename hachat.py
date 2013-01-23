#!/usr/bin/env python
# coding = utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

'''This is the basic hachat module which starts a Peer with
    the given options from command line'''

import argparse
import logging
import re
import random
from peer import Peer
import time


parser = argparse.ArgumentParser(description="start peer with arguments")
parser.add_argument("-v", "--verbose", action="store_true", default=False, help="show p2p-information")
parser.add_argument("-l", "--link", help="hachat link (ex. localhost:12345)")
parser.add_argument("-p", "--port", help="Port to listen on")
parser.add_argument("-n", "--name", help="set own name")
parser.add_argument("-i", "--ip", help="ip-adresse where you can be reached")
parser.add_argument("-T", "--Test", action="store_true", default=False, help="for testing the network")

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
    if args.Test == True:
        peer = Peer(firstHost = (hostIP, hostPort), port = args.port, name = name, testmode=True)
    else:
        peer = Peer(firstHost = (hostIP, hostPort), port = args.port, name = name)
else:
    if args.ip:
        if args.Test == True:
            peer = Peer(ip = args.ip, port = args.port, name = name, testmode=True)
        else:
            peer = Peer(ip = args.ip, port = args.port, name = name)
            
        # terminate peer
        peer.__del__()
        time.sleep(1)
    else:
        print "You need a link or your own ip adress to start hachat!"

   

