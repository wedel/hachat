# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import const
import socket
import threading
import message
import time
import random
import re
from host import Host
import logging
import gui

class Peer:
    """ Peer Klasse """

    def __init__(self, firstHost = None, port = None, name = "temp", ip = None):
        
        self.name = name # set peer name
        self.inSocket = None # Socket für eingehende Verbindungen
        self.hosts = {} # Dict. der bekannten Hosts
        self.knownPeers = {} # Dict (ip:port) : name
        
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
        
        # send HELO to first host if you know one
        if firstHost != None:
            (hostIP, hostPort) = firstHost
            h = Host(self, hostIP, hostPort)
            
            #Initial Request for some more hosts from firstHost
            key = h.constructKey(hostIP, hostPort)
            logging.debug("Initial Request for some peers from " + key)
            self.requestHosts(key, const.INI_PEERLIMIT) # and get some more hosts
        
        #start gui
        self.gui.run()
                


    def startRecvLoop(self):
        ''' general recieve loop of a peer '''
        logging.debug("RecvLoop started")
        while not self.gui.stop:
            (data, addr) = self.inSocket.recvfrom(const.HACHAT_BUFSIZE)
            # try to build Message object and decide what to do with it based on type
            try:
                msg = message.toMessage(data)
            except message.MessageException, e:
                logging.warn("unrecognised message " + str(e))
                
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
                    
                    key = Host.constructKey(msg.ip, msg.port)
                    if key in self.hosts:
                        # if messag from host - update lastSeen
                        self.hosts[key].lastSeen = 1
                    else:
                        # add to knownPeers
                        self.knownPeers[key] = msg.name
                    #logging.debug(str(self.knownPeers.keys()))
                    
                    logging.debug("received " + msg.text + " from " + msg.name)
                    
            elif isinstance(msg, message.ByeMessage):
                key = Host.constructKey(msg.ip, msg.port)
                if key in self.hosts:
                    del self.hosts[key]
                if key in self.knownPeers:
                    del self.knownPeers[key]
                logging.debug("recieved BYE, deleting " + key)
            
            elif isinstance(msg, message.HostExchangeMessage):
                senderIP = addr[0]
                neighbour = senderIP + ':' + str(msg.senderPort)
                logging.debug("received HostExchangeMessage: " + str(msg))
                    
                if msg.level == "REQUEST":
                    self.pushHosts(neighbour, msg.quant)
                    logging.debug("received: HostExchangeMessage Request. Will enter pushHosts()")
                    
                elif msg.level == "PUSH": # add hosts to HostList
                    logging.debug("received: HostExchangeMessage Push. Will add Hosts to HostList")
                    for h in msg.listofHosts:
                        self.addToHosts(h)
                        logging.debug("adding " + h + " to HostList")         
                else:
                    logging.warning("received HostExchangeMessage with unknown level!")
                    
            else:
                logging.warn("hier sollte der Code nie ankommen, sonst gibt es unbekannte Message Unterklassen")
                logging.warn(type(msg))


    def sendText(self, text):
        if text != "":
            msg = message.TextMessage(self.name, self.ip, self.port, text)
            for h in self.hosts.values():
                #print "trying to send msg to %s:%s" %(recIP,recPort)
                self.history.addMsg(msg) # add to own history
                h.addToMsgQueue(msg)

    def forwardMsg(self,msg):
        if len(self.hosts) > 0:
            msgSender = msg.ip + ":" + str(msg.port)
            for h in self.hosts.values():
                hostAddr = h.hostIP + ":" + str(h.hostPort)
                if msgSender != hostAddr:
                    #logging.debug("Message " +  msg.text + " from " + msgSender + " will be forwarded to " + hostAddr )
                    h.addToMsgQueue(msg)
                else:
                    logging.debug("Message " + msg.text + " will not be forwarded to initial sender " + msgSender)
        else:
            logging.debug("Peer %s:%d: No peer in HostList, can not forward msg" %(self.ip, self.port))


    def addToHosts(self, addr):
        '''check if already in hostlist otherwise add'''
        
        # construct key and tuple
        if isinstance(addr, str):
            key = addr
            (hostIP, hostPort) = re.split(':',addr,1)
        elif isinstance(addr, tuple):
            (hostIP, hostPort) = addr
            key = Host.constructKey(hostIP, hostPort)
            
        # if host is not the peer itself
        if hostIP != self.ip or int(hostPort) != int(self.port):
            if key in self.hosts:
                # set status that Host had contact
                host = self.hosts[key]
                host.lastSeen = 1 
                logging.debug(key + " already in hostlist - refreshing lastSeen")
            else:
                # insert in host dict
                logging.debug("adding " + key + " to hostlist")
                h = Host(self, hostIP, hostPort)
        logging.debug("Now %d Hosts in HostList and %d Hosts in knownHosts"%(len(self.hosts), len(self.knownPeers)))
    
    def maintenanceLoop(self):
        while True:
            time.sleep(const.MAINTENANCE_SLEEP)
            logging.debug("maintenance start")
            logging.debug("counter: " + str(self.counter))
            
            # every 3 maintenance loops check if you have to delete host and fill Hostlist if needed
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

                # do we have to few neighbors and we know other peers?
                if len(self.hosts) < const.MIN_PEERLIMIT:
                    if self.knownPeers:
                        #choose one
                        filler = random.choice(self.knownPeers.keys())
                        if filler != None:
                            logging.debug("got to few Peers, filling with " + filler)
                            (fillerIP, fillerPort) = filler.split(":", 2)
                            # and add it as a new host.
                            newHost = Host(self, fillerIP, fillerPort)
                            del self.knownPeers[filler]
                            logging.debug("Now %d Hosts in HostList and %d Hosts in knownHosts"%(len(self.hosts), len(self.knownPeers)))
                    elif self.hosts: #if nothing in knownPeers but in hostlist
                        neighbour = random.choice(self.hosts.keys()) #pick a rand host from hostlist
                        logging.debug("Request some peers from " + neighbour)
                        self.requestHosts(neighbour) # and get some more hosts
                    else:
                        logging.error("You are not connected to the network!!! HostList as well as List of known Hosts is empty.")
                
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
                    logging.debug("sending msg: %s to %s:%i" %(msgStr, host.hostIP, host.hostPort))
                    host.outSocket.sendto(msgStr, (host.hostIP, host.hostPort))
                    
    def requestHosts(self, neighbour, quant=None):
        '''request Hosts from neighbour'''
        if quant == None:
            quantToRequest = ((const.MIN_PEERLIMIT - len(self.hosts)))
        else: 
            quantToRequest = quant
        try:
            neighbourHost = self.hosts[neighbour] #check neighbour in hostlist
            neighbourIP = neighbourHost.hostIP
            neighbourPort = neighbourHost.hostPort
            
            # constuct requestMsg: recipientIP, recipientPort, senderPort, level, quant , listofHosts=None, uid=None: 
            requestMsg = message.HostExchangeMessage(neighbourIP, neighbourPort, self.port, "REQUEST", quant=quantToRequest)
            neighbourHost.addToMsgQueue(requestMsg)# push it in hosts msgqueue
            logging.debug("Requested more Hosts from %s" %(neighbour))
        except Exception:
            raise message.MessageException("requestHost(): given neighbour needs to be a (IP,Port)Pair and needs to be in HostList")

    
    def pushHosts(self, neighbour, quant):
        '''give Hosts from hostExchange to a neighbour'''
        logging.debug("entered pushHosts, request for %d hosts"%(quant))
        listofHosts = []
        i = 0
        if len(self.hosts) < quant:
            quant = len(self.hosts)
            
        while i < quant:
            host = random.choice(self.hosts.keys())
            if host == None:
                break #nothing in hostlist
            if host not in listofHosts:
                listofHosts.append(host) 
                i = i+1       
        
        if len(listofHosts) > 0:
            #logging.debug("construct pushHostExchange Msg")
            try:
                neighbourHost = self.hosts[neighbour] #check neighbour in hostlist
                neighbourIP = neighbourHost.hostIP
                neighbourPort = neighbourHost.hostPort
                
                pushMsg = message.HostExchangeMessage(neighbourIP, neighbourPort, self.port, "PUSH", listofHosts=listofHosts)
                neighbourHost.addToMsgQueue(pushMsg)# push it in hosts msgqueue
                #logging.debug("Pushed Hosts to %s" %(neighbour))
            except Exception:
                raise message.MessageException("requestHost(): given neighbour needs to be a (IP,Port)Pair and needs to be in HostList") 
        else: 
            logging.debug("Can't push Hosts, no Hosts in HostList")
    
    
    def __del__(self):
        # tell other peers to delete your host
        logging.debug("sending BYE")
        msg = message.ByeMessage(self.ip, self.port)
        for h in self.hosts.values():
            h.addToMsgQueue(msg)
            h.__del__()
            
        self.inSocket.close()
