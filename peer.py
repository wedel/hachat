# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import socket
import threading
from message import Message
from host import Host

class Peer:
    """ Peer Klasse """

    BUFSIZE = 1024 # Größe unseres Buffers

    inSocket = None # Socket für eingehende Verbindungen
    ip = None # IP des Peers
    port = None # Port auf dem der Peer hört
    hosts = {} # Dict. der bekannten Hosts

    def __init__(self, firstHost = None):
        self.inSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.inSocket.bind(('', 0))
        self.port = int(self.inSocket.getsockname()[1])
        print "Listening on port", self.port
        if firstHost != None:
            self.addToHosts(firstHost)

        self.startRecvLoop()
        

    def startRecvLoop(self):
        try:
            while True:
                data, addr = self.inSocket.recvfrom(self.BUFSIZE)
                # TODO!!!! zum test:
                i = data.find("CALLME:")
                i = i+7
                (ip, port) = addr
                addr = (ip, int(data[i:]))
                self.addToHosts(addr) 
                print "received:", data, "from", addr

        except Exception, e:
            print "Error: ", e
        except KeyboardInterrupt:
            print "Quitting.."

    def addToHosts(self, addr):
        print "adding", addr
        (hostIP, hostPort) = addr
        h = Host(self, hostIP, hostPort)
        h.sendHello()
        self.hosts[hostIP] = h


    def __del__(self):
        self.inSocket.close()
