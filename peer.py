# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import socket
#import threading
import message
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
        self.ip = socket.gethostbyname(socket.gethostname())
        self.port = int(self.inSocket.getsockname()[1])
        print "Listening on port", self.port
        if firstHost != None:
            self.addToHosts(firstHost)
        self.startRecvLoop()
        

    def startRecvLoop(self):
        try:
            while True:
                (data, addr) = self.inSocket.recvfrom(self.BUFSIZE)
                try:
                    msg = message.toMessage(data)
                except message.MessageException, e:
                    print e
                if isinstance(msg, message.HeloMessage):
                    print "received: HELO from", addr
                    inputaddr = (msg.senderIP, msg.senderPort)
                    self.addToHosts(inputaddr) 
                elif isinstance(msg, message.TextMessage):
                    print "received:",  msg.text, "from", msg.name
                else:
                    print "hier sollte der Code nie ankommen, sonst gibt es unbekannte Message Unterklassen"
                    print type(msg)

        except Exception, e:
            print "Error: ", e
        except KeyboardInterrupt:
            print "Quitting.."

    def addToHosts(self, addr):
        '''check if already in hostlist otherwise add'''
        (hostIP, hostPort) = addr
        
        key = hostIP + ':' + str(hostPort) # construct key
        
        #insert in host dict
        if key in self.hosts:
            #test sende message
            msg = message.TextMessage(self.ip,  key + ' already in hostlist')
            for host in self.hosts:
                self.hosts[host].addToMsgQueue(msg)
            #testende
        else:
            print "adding", key, "to hostlist"
            h = Host(self, hostIP, hostPort)
            h.sendHello() # send helo to h
            self.hosts[key] = h


    def __del__(self):
        self.inSocket.close()
