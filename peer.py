# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import socket
import threading
import message
import time
from host import Host
import logging


class Peer:
    """ Peer Klasse """

    BUFSIZE = 1024 # Größe unseres Buffers

    inSocket = None # Socket für eingehende Verbindungen
    ip = None # IP des Peers
    port = None # Port auf dem der Peer hört
    hosts = {} # Dict. der bekannten Hosts
    name = None

    def __init__(self, firstHost = None, port = None, name = "temp"):
        
        self.name = name # set peer name
        
        # open socket
        self.inSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if port == None:
            # bind on random port
            self.inSocket.bind(('', 0))
        else:
            # bind on given port
            self.inSocket.bind(('', int(port)))
            
        self.port = int(self.inSocket.getsockname()[1])
        print "Listening on port", self.port
        
        # send HELO to first host if you know one
        if firstHost != None:
            (hostIP, hostPort) = firstHost
            h = Host(self, hostIP, hostPort)
            h.sendHello()
            
        self.history = message.History(2,10)
        self.recvThread = threading.Thread(target=self.startRecvLoop)
        self.recvThread.daemon = True
        self.recvThread.start()

    def startRecvLoop(self):
        ''' general recieve loop of a peer '''
        try:
            while True:
                (data, addr) = self.inSocket.recvfrom(self.BUFSIZE)
                # try to build Message object and decide what to do with it based on type
                try:
                    msg = message.toMessage(data)
                except message.MessageException, e:
                    print e
                    
                if isinstance(msg, message.HeloMessage):
                    senderIP = addr[0]
                    inputaddr = (senderIP,  msg.senderPort)
                    logging.debug("received: HELO from " + str(inputaddr))
                    self.addToHosts(inputaddr) 
                    
                elif isinstance(msg, message.TextMessage):
                    if not self.history.msgExists(msg) and msg.name != self.name:
                        self.history.addMsg(msg)
                        self.forwardMsg(msg)
                        print msg.name + ":",  msg.text                    
                else:
                    print "hier sollte der Code nie ankommen, sonst gibt es unbekannte Message Unterklassen"
                    print type(msg)
                    
        except Exception, e:
            print "Error: ", e

    def sendText(self, text):
            for h in self.hosts.values():
                #print "trying to send msg to %s:%s" %(recIP,recPort)
                msg = message.TextMessage(self.name, text)
                h.addToMsgQueue(msg)

    def forwardMsg(self,msg):
        if len(self.hosts) > 0:
            for h in self.hosts.values():
                logging.debug("Message" + msg.text + "will be forwarded")
                h.addToMsgQueue(msg)
        else:
            logging.debug("Peer %s:%d: No peer in HostList, can not forward msg" %(self.ip, self.port))


    def addToHosts(self, addr):
        '''check if already in hostlist otherwise add'''
        (hostIP, hostPort) = addr
        key = hostIP + ':' + str(hostPort) # construct key
        
        if key in self.hosts:
            logging.debug(key + " already in hostlist")
        else:
            #insert in host dict
            logging.debug("adding " + key + " to hostlist")
            h = Host(self, hostIP, hostPort)
            h.sendHello() # send helo to h
            self.hosts[key] = h
            logging.debug(str(self.hosts.keys()))
            


    def __del__(self):
        self.inSocket.close()
