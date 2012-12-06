# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import socket
import threading
import message
import sys
import select
import time
from host import Host

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
            
        try: #lesen von stdIn als Thread...
            self.keyboardThread = threading.Thread(target=self.checkStdIn) 
            self.keyboardThread.daemon = True
            self.keyboardThread.start()
        except (KeyboardInterrupt,SystemExit):
            print "Quitting Peer.."
            
        self.startRecvLoop()
        

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
                    print "received: HELO from", addr
                    senderIP = addr[0]
                    inputaddr = (senderIP,  msg.senderPort)
                    self.addToHosts(inputaddr) 
                    
                elif isinstance(msg, message.TextMessage):
                    print msg.name + ":",  msg.text
                    
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
        
        if key in self.hosts:
            print key, "already in hostlist"
        else:
            #insert in host dict
            print "adding", key, "to hostlist" 
            h = Host(self, hostIP, hostPort)
            h.sendHello() # send helo to h
            self.hosts[key] = h
            
    def checkStdIn(self):
        '''checkt ob in sdtIn geschrieben wird und
        sendet dann alle peers aus host-liste die nachricht
        wird als thread gerufen, scheint so ueblich zu sein, sihe
        http://stackoverflow.com/questions/292095/polling-the-keyboard-in-python'''
        #print "checkStdIn called"
        while True:
            try:
                i,o,e = select.select([sys.stdin],[],[],0.0001) #checkt ob irgendwas auf sdtIN
            except:
                raise 'could not read from stdIn'                
            for s in i:
                if s == sys.stdin and len(self.hosts) > 0: #falls, und hosts in der liste, so
                    msgstring = sys.stdin.readline() # wird dies an alle in der liste verteilt
                    for h in self.hosts.values():
                        #print "trying to send msg to %s:%s" %(recIP,recPort)
                        msg = message.TextMessage(self.name, msgstring)
                        h.addToMsgQueue(msg)


    def __del__(self):
        self.inSocket.close()
