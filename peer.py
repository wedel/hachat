# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import const
import socket
import threading
import message
import time
from host import Host
import logging
import gui

class Peer:
    """ Peer Klasse """
    
    BUFSIZE = 1024 # Größe unseres Buffers

    def __init__(self, firstHost = None, port = None, name = "temp", ip = None):
        
        self.name = name # set peer name
        self.inSocket = None # Socket für eingehende Verbindungen
        self.hosts = {} # Dict. der bekannten Hosts
        self.remindList = {} # Dict (ip:port) : name
        
        # set own ip if you already know it
        if ip != None:
            self.ip = ip
        else:
            self.ip = "null"
        
        # open socket
        self.inSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if port == None:
            # bind on random port
            self.inSocket.bind(('', 0))
        else:
            # bind on given port
            self.inSocket.bind(('', int(port)))
            
        self.port = int(self.inSocket.getsockname()[1]) # port where peer listens on
        logging.info("Listening on port " + str(self.port))
            
        self.history = message.History(10,100)
        
        self.gui = gui.gui(self)
        
        # lock for hostlist (not needed atm)
        # self.hostlock = threading.RLock()
        
        # start recieveLoop
        self.recvThread = threading.Thread(target=self.startRecvLoop)
        self.recvThread.daemon = True
        self.recvThread.start()
        
        # start sendLoop
        self.sThread = threading.Thread(target=self.sendLoop)
        self.sThread.daemon = True
        self.sThread.start()
        
        # start maintenance Loop
        self.counter = 0
        self.mThread = threading.Thread(target=self.maintenanceLoop)
        self.mThread.daemon = True
        self.mThread.start()
        
        # initialise Host Class
        Host.myPeer = self
        
        # send HELO to first host if you know one
        if firstHost != None:
            (hostIP, hostPort) = firstHost
            h = Host(hostIP, hostPort)
        
        #start gui
        self.gui.run()
                


    def startRecvLoop(self):
        ''' general recieve loop of a peer '''
        logging.debug("RecvLoop started")
        try:
            while not self.gui.stop:
                (data, addr) = self.inSocket.recvfrom(const.HACHAT_BUFSIZE)
                # try to build Message object and decide what to do with it based on type
                try:
                    msg = message.toMessage(data)
                except message.MessageException, e:
                    print e
                    
                if isinstance(msg, message.HeloMessage):
                    # set your own ip if you dont know it
                    if self.ip == "null":
                        self.ip = msg.recipientIP
                    
                    # add new host to hostlist
                    senderIP = addr[0]
                    inputaddr = (senderIP,  msg.senderPort)
                    logging.debug("received: HELO from " + str(inputaddr))
                    self.addToHosts(inputaddr) 
                    
                elif isinstance(msg, message.TextMessage):
                    if not self.history.msgExists(msg) : # if i don't already know message
                        self.history.addMsg(msg)
                        self.forwardMsg(msg)
                        self.gui.empfang(msg) #gibt nachricht an gui weiter 
                        
                        # add host to remindlist
                        key = Host.constructKey(msg.ip, msg.port)
                        self.remindList[key] = msg.name
                        #logging.debug(str(self.remindList.keys()))
                        
                        logging.debug("received " + msg.text + " from " + msg.name)   
                else:
                    print "hier sollte der Code nie ankommen, sonst gibt es unbekannte Message Unterklassen"
                    print type(msg)
                    
        except Exception, e:
            print "Error: ", e

    def sendText(self, text):
        if text != "":
            for h in self.hosts.values():
                #print "trying to send msg to %s:%s" %(recIP,recPort)
                msg = message.TextMessage(self.name, self.ip, self.port, text)
                self.history.addMsg(msg) # add to own history
                h.addToMsgQueue(msg)

    def forwardMsg(self,msg):
        if len(self.hosts) > 0:
            for h in self.hosts.values():
                #logging.debug("Message " + msg.text + " will be forwarded")
                h.addToMsgQueue(msg)
        else:
            logging.debug("Peer %s:%d: No peer in HostList, can not forward msg" %(self.ip, self.port))


    def addToHosts(self, addr):
        '''check if already in hostlist otherwise add'''
        (hostIP, hostPort) = addr
        key = Host.constructKey(hostIP, hostPort)
        
        if key in self.hosts:
            host = self.hosts[key]
            host.lastSeen = 1 # set status that Host had contact
            logging.debug(key + " already in hostlist - refreshing lastSeen")
        else:
            #insert in host dict
            logging.debug("adding " + key + " to hostlist")
            h = Host(hostIP, hostPort)
            #logging.debug(str(self.hosts.keys()))

    def __del__(self):
        self.inSocket.close()
    
    def maintenanceLoop(self):
        while True:
            time.sleep(const.MAINTENANCE_SLEEP)
            logging.debug("maintenance start")
            logging.debug("counter: " + str(self.counter))
            
            # every 3 maintenance loops check if you have to delete host
            if self.counter == 2:
                temp = self.hosts.keys()
                for key in temp:
                    host = self.hosts[key]
                    if host.lastSeen == 0:
                        logging.debug("deleting host " + key)
                        host.__del__()
                        del self.hosts[key]
                    else:
                        host.lastSeen = 0 # reset lastSeen
                
            # send HELO from all hosts in hostlist
            for h in self.hosts.values():
                if h.lastSeen == 0: # but only if you haven't seen him for a while
                    h.sendHello()

            self.counter = (self.counter + 1) % 3
            logging.debug("maintenance end")
            
    def sendLoop(self):
        '''send Message objects of all hosts from Queue as string'''
        logging.debug("starting sendLoop")
        while True:
            time.sleep(0.1)
            for host in self.hosts.values():
                while host.msgQueue:
                    msg = host.msgQueue.popleft()
                    #convert to string to send over socket
                    msgStr = str(msg)
                    logging.debug("sending msg: %s to %s" %(msgStr, host.hostIP))
                    host.outSocket.sendto(msgStr, (host.hostIP, host.hostPort))
