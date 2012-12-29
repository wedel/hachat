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
            
        self.history = message.History(const.HISTORY_SAVEDMSGSLIMIT,const.HISTORY_SAVEDHASHESLIMIT)
        
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
            self.key = None
            (hostIP, hostPort) = firstHost
            h = Host(self, hostIP, hostPort)
            
            # wait until you're connected to the network
            while self.key == None:
                time.sleep(0.5)
                
            #Initial Request for some more hosts from firstHost
            key = h.constructKey(hostIP, hostPort)
            logging.debug("Initial Request for some peers from " + key)
            self.requestHosts(key, const.INI_PEERLIMIT) # and get some more hosts
            
            #Initial Request for History
            logging.debug("Initial Request for History from " + key)
            self.getHistory(key)
        else:
            self.key = Host.constructKey(self.ip, self.port)
            logging.info("You created a new Hachat-network. Your key is " + self.key)
        
        #start gui
        self.gui.run()
                


    def startRecvLoop(self):
        ''' general recieve loop of a peer '''
        logging.debug("RecvLoop started")
        while not self.gui.stop:
            (data, addr) = self.inSocket.recvfrom(const.HACHAT_BUFSIZE)
            logging.debug("recieved msg with length: " + str(len(data)))

            # try to build Message object and decide what to do with it based on type
            try:
                msg = message.toMessage(data)
            except message.MessageException, e:
                logging.warn("unrecognised message " + str(e))
                
            if isinstance(msg, message.HeloMessage):
                # set your own ip if you dont know it
                if self.ip == "null":
                    self.ip = msg.recipientIP
                    self.key = Host.constructKey(self.ip, self.port)
                    logging.info("You're now connected to a Hachat-network. Your key is " + self.key)
                
                senderIP = addr[0]
                key = Host.constructKey(senderIP, msg.senderPort)
                logging.debug("received: HELO from " + str(key))
                
                if key in self.hosts:
                     # if you know Host set status that Host had contact
                    host = self.hosts[key]
                    host.lastSeen = 1 
                    logging.debug(key + " already in hostlist - refreshing lastSeen")
                else: 
                    # add new host to hostlist
                    self.addToHosts(key)
            
            # only accept Messages from Peers in self.hosts        
            else:
                try:
                    sender = msg.origin
                except Exception, e:
                    logging.debug("Msg needs origin, but doesn't have one " + str(msg))
                    
                try:
                    # overriding sender with lastHop
                    sender = msg.lastHop
                except Exception, e:
                    pass
                    
                if not sender in self.hosts:
                    logging.debug("We only accept Messages from Peers in Hostlist")
                else:
                
                    if isinstance(msg, message.TextMessage):
                        if not self.history.msgExists(msg.hash) : # if i don't already know message
                            self.history.addMsg(msg)
                            self.forwardMsg(msg)
                            self.gui.empfang(msg) #gibt nachricht an gui weiter 
                            
                            key = msg.origin
                            if key in self.hosts:
                                # if messag from host - update lastSeen
                                self.hosts[key].lastSeen = 1
                            else:
                                # add to knownPeers
                                self.knownPeers[key] = msg.name
                            #logging.debug(str(self.knownPeers.keys()))
                            
                            logging.debug("received " + msg.text + " from " + msg.name)
                            
                    elif isinstance(msg, message.ByeMessage):
                        key = msg.origin
                        if key in self.hosts:
                            del self.hosts[key]
                        if key in self.knownPeers:
                            del self.knownPeers[key]
                        logging.debug("recieved BYE, deleting " + key)
                    
                    elif isinstance(msg, message.HostExchangeMessage):
                        neighbour = msg.origin
                        logging.debug("received HostExchangeMessage: " + str(msg))
                            
                        if msg.level == "REQUEST":
                            self.pushHosts(neighbour, msg.quant)
                            logging.debug("received: HostExchangeMessage Request. Will enter pushHosts()")
                            
                        elif msg.level == "PUSH": # add hosts to HostList
                            logging.debug("received: HostExchangeMessage Push. Will add Hosts to HostList")
                            for h in msg.listofHosts:
                                self.addToHosts(h)      
                        else:
                            logging.warning("received HostExchangeMessage with unknown level!")
                            
                    elif isinstance(msg, message.HistoryExchangeMessage):
                        neighbour = msg.origin
                        logging.debug("received HistoryExchangeMessage: " + str(msg))
                            
                        if msg.level == "REQUEST":
                            self.pushHistroy(neighbour,msg.quant)
                            logging.debug("received: HistoryExchangeMessage Request. Will enter pushHistroy()")
                        elif msg.level == "PUSH": 
                            logging.debug("received: HistoryExchangeMessage Push. Will enter HistoryControl")
                            self.HistoryControl(neighbour,msg.liste)
                        elif msg.level == "REQUESTMSGS":
                            logging.debug("received: HistoryExchangeMessage REQUESTMSGS. Will enter pushMsgObjects")
                            self.pushMsgObjects(neighbour, msg.liste)
                        elif msg.level == "PUSHMSGS":
                            logging.debug("received: HistoryExchangeMessage PUSHMSGS. Will enter NewMsgsForHistory")
                            self.NewMsgsForHistory(msg.liste)
                            
                        else:
                            logging.warning("received HistoryExchangeMessage with unknown level!")
                            
                    else:
                        logging.warn("hier sollte der Code nie ankommen, sonst gibt es unbekannte Message Unterklassen")
                        logging.warn(type(msg))


    def sendText(self, text):
        if text != "":
            msg = message.TextMessage(self.name, self.key, self.key, text)
            for h in self.hosts.values():
                self.history.addMsg(msg) # add to own history
                h.addToMsgQueue(msg)

    def forwardMsg(self, msg):
        '''forwarding TextMessage, but not to initial sender'''
        msgSender = msg.origin
        # rewrite lastHop
        oldLastHop = msg.lastHop
        msg.lastHop = self.key
        
        for h in self.hosts.values():
            hostAddr = Host.constructKey(h.hostIP, h.hostPort)
            # don't forward to origin or lastHop
            if msgSender != hostAddr and oldLastHop != hostAddr:
                #logging.debug("Message " +  msg.text + " from " + msgSender + " will be forwarded to " + hostAddr )
                h.addToMsgQueue(msg)
            else:
                logging.debug("Message " + msg.text + " will not be forwarded to initial sender " + msgSender + " and lastHop " + oldLastHop)


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
            if not (key in self.hosts):
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
                        logging.error("You are not connected to the network!!! HostList as well as List of known Hosts are empty.")
                
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
                    logging.debug("sending msg: %s to %s:%i with length %d" %(msgStr, host.hostIP, host.hostPort, len(msgStr)))
                    host.outSocket.sendto(msgStr, (host.hostIP, host.hostPort))
                    
############################################################################
##################### HostExchange  ########################################
############################################################################

                    
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
            
            # constuct requestMsg: recipientIP, recipientPort, origin, level, quant , listofHosts=None, uid=None: 
            requestMsg = message.HostExchangeMessage(neighbourIP, neighbourPort, self.key, "REQUEST", quant=quantToRequest)
            neighbourHost.addToMsgQueue(requestMsg)# push it in hosts msgqueue
            logging.debug("Requested more Hosts from %s" %(neighbour))
        except Exception:
            raise message.MessageException("requestHost(): given neighbour needs to be a (IP,Port)Pair and needs to be in HostList")

    
    def pushHosts(self, neighbour, quant):
        '''give Hosts from hostExchange to a neighbour'''
        logging.debug("entered pushHosts, request for %d hosts"%(quant))
        listofHosts = []
        i = 0
        # -1 because neighbour is part of hostlist
        if len(self.hosts) - 1 < quant:
            quant = len(self.hosts) - 1
        
        # get neighbour from hostlist
        try:
            neighbourHost = self.hosts[neighbour]
            neighbourIP = neighbourHost.hostIP
            neighbourPort = neighbourHost.hostPort
        except Exception, e:
            logging.error(str(e))
            
        while i < quant:
            key = random.choice(self.hosts.keys())
            if key == None:
                break #nothing in hostlist
            # check if key doesnt belong to neighbour
            if neighbourHost != self.hosts[key]:
                if key not in listofHosts:
                    listofHosts.append(key) 
                    i = i+1       
            
        if len(listofHosts) > 0:
            #logging.debug("construct pushHostExchange Msg")
            pushMsg = message.HostExchangeMessage(neighbourIP, neighbourPort, self.key, "PUSH", listofHosts=listofHosts)
            neighbourHost.addToMsgQueue(pushMsg)# push it in hosts msgqueue
            #logging.debug("Pushed Hosts to %s" %(neighbour))
        else: 
            logging.debug("Can't push Hosts, no Hosts in HostList")
            

############################################################################
##################### HistoryExchange  #####################################
############################################################################
            
    def getHistory(self, neighbour):
        '''request History from neigbour'''
        try:
            neighbourHost = self.hosts[neighbour]
            neighbourIP = neighbourHost.hostIP
            neighbourPort = neighbourHost.hostPort
        except Exception:
            raise message.MessageException("getHistory(): given neighbour needs to be a (IP,Port)Pair and needs to be in HostList")
               
        requestMsg = message.HistoryExchangeMessage(neighbourIP, neighbourPort, self.key, "REQUEST", quant=const.HISTORY_GETLIMIT)
        neighbourHost.addToMsgQueue(requestMsg)# push it in hosts msgqueue
        logging.debug("Requested History from %s" %(neighbour))
        
    
    def pushHistroy(self, neighbour, quant):
        '''push own List of History-Hashes to neighbour'''
        
        logging.debug("entered pushHistory, request for List of latest History")
        List = self.history.getMsgHashes(quant)
        
        if len(List) > 0:
            # get neighbour from hostlist
            try:
                neighbourHost = self.hosts[neighbour]
                neighbourIP = neighbourHost.hostIP
                neighbourPort = neighbourHost.hostPort
            except Exception, e:
                logging.error(str(e))
                
            logging.debug("construct pushHistoryExchange Msg")
            pushMsg = message.HistoryExchangeMessage(neighbourIP, neighbourPort, self.key, "PUSH", liste=List)
            neighbourHost.addToMsgQueue(pushMsg)# push it in hosts msgqueue
            logging.debug("Pushed History to %s" %(neighbour))
        else: 
            logging.debug("Can't push History, no Msgs in History")

    def HistoryControl(self, neighbour, historyList):
        '''checks if the historyList from neighbour contains msgs wich are not
        in own History. If so, it sends these lostMsg Hahses back and by this
        requests the associated msgObjects'''
        
        logging.debug("entered HistoryControle, will check our History...")
        lostMsgHashes = []

        for i in range(0, len(historyList)):
            if self.history.msgExists(historyList[i]) == False:
                lostMsgHashes.append(historyList[i])
        
        if len(lostMsgHashes) > 0:
            logging.debug("have to request some History Msg Objects...")
            try:
                neighbourHost = self.hosts[neighbour]
                neighbourIP = neighbourHost.hostIP
                neighbourPort = neighbourHost.hostPort
            except Exception, e:
                logging.error(str(e))
            # create GETMSGS msg:
            getmsg = message.HistoryExchangeMessage(neighbourIP, neighbourPort, self.key, "REQUESTMSGS", liste=lostMsgHashes)
            neighbourHost.addToMsgQueue(getmsg)# push it in hosts msgqueue
            logging.debug("Requested Msgs from %s" %(neighbour))
        else: 
            logging.debug("History Check found no Lost Msgs")
        
    def pushMsgObjects(self, neighbour, lostMsgHashes):
        '''pushes requested msgObjects back to neighbour'''
        
        logging.debug("entered pushMsgObjects, will push History Msg Objects")
        historyList = []
        for i in range(0,len(lostMsgHashes)):
            historyList.append(self.history.getMsgObjects(lostMsgHashes[i]))
            historyList.reverse() # to push it in right order
        
        if len(historyList) > 0:
            # get neighbour from hostlist
            try:
                neighbourHost = self.hosts[neighbour]
                neighbourIP = neighbourHost.hostIP
                neighbourPort = neighbourHost.hostPort
            except Exception, e:
                logging.error(str(e))
                
            logging.debug("construct pushMsgObjects Msg")
            pushMsg = message.HistoryExchangeMessage(neighbourIP, neighbourPort, self.key, "PUSHMSGS", liste=historyList)
            neighbourHost.addToMsgQueue(pushMsg)# push it in hosts msgqueue
            logging.debug("Pushed History to %s" %(neighbour))
        else: 
            logging.debug("Can't push History, no Msgs in History")
            
    
    def NewMsgsForHistory(self, msgList):
        ''' enters not containing msgs to history and sends them to the gui'''
        
        logging.debug("entered NewMsgsForHistory, will push Msgs to History...")
        for i in range(0,len(msgList)):
            tomsg = message.toMessage(msgList[i])
            self.history.addMsg(tomsg)
            logging.debug("entered msg %s to History."%(msgList[i]))
            self.gui.empfang(tomsg) #gibt nachricht an gui weiter
            
        logging.debug("NewMsgsForHistory finished")
        

############################################################################
##################### __del__  #############################################
############################################################################
        

    def __del__(self):
        # tell other peers to delete your host
        logging.debug("sending BYE")
        msg = message.ByeMessage(self.key)
        for h in self.hosts.values():
            h.addToMsgQueue(msg)
            h.__del__()
            
        self.inSocket.close()
