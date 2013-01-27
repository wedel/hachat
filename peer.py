# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

'''central module which defines the behaviour of a Hachat Peer'''

import const
import socket
import threading
import string
import message
import time
import random
import re
from host import Host
import logging
import gui

class Peer:
    """ Peer Klasse """

    def __init__(self, firstHost = None, port = None, name = "temp", ip = None, testmode = False):
        
        self.name = name # set peer name
        self.inSocket = None # Socket für eingehende Verbindungen
        self.hosts = {} # Dict. der bekannten Hosts
        self.knownPeers = {} # Dict (ip:port) : name
        self.msgParts = {}
        
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
            
        self.history = message.History(const.HISTORY_SAVEDMSGSLIMIT, const.HISTORY_SAVEDHASHESLIMIT)
        
        self.gui = gui.gui(self)
        
        # lock for hostlist (not needed atm)
        # self.hostlock = threading.RLock()
        
        # start receiveLoop
        self.rThread = threading.Thread(target=self.startRecvLoop)
        self.rThread.daemon = True
        self.rThread.start()
        
        # start sendLoop
        if testmode == True:
            #if testmode is true, sendLoop will drop random parts of msgs
            self.sThread = threading.Thread(target=self.sendLoop, args=(True,))
            self.sThread.daemon = True
            self.sThread.start()
        else:
            self.sThread = threading.Thread(target=self.sendLoop, args=(False,))
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
            h.bootstrap = True
            
            # wait until you're connected to the network
            while self.key == None:
                time.sleep(0.5)
                
            #Initial Request for some more hosts from firstHost
            key = h.constructKey(hostIP, hostPort)
            logging.debug("Initial Request for some peers from " + key)
            self.requestHosts(key, const.INI_PEERLIMIT) # and get some more hosts
            
            #Initial Request for History
            logging.debug("Initial Request for History from " + key)
            self.getHistory(key, initial=True)
        else:
            self.key = Host.constructKey(self.ip, self.port)
            logging.info("You created a new Hachat-network. Your key is " + self.key)
        
        if testmode == True:
            self.generateMsgParts(10, 3000) #generates Randome Text-Msgs
        
        #start gui
        self.gui.run()                

    def startRecvLoop(self):
        ''' general receive loop of a peer '''
        logging.debug("RecvLoop started")
        while not self.gui.stop:
            (data, addr) = self.inSocket.recvfrom(const.HACHAT_BUFSIZE)

            # join the parts:

            (HEAD, splitUID, part, numOfParts, rest) = re.split(',', data, 4)
            splitUID = int(splitUID)
            part = int(part)
            numOfParts = int(numOfParts)
            logging.debug("received msg with splitUID %i, part %i of %i with length %i" %(splitUID, part, numOfParts, len(data)))

            # check if Hachat Message
            if HEAD != const.HACHAT_HEADER:
                raise message.MessageException("wrong Header: " + HEAD)
                continue


            if splitUID not in self.msgParts.keys():
                self.msgParts[splitUID] = {}
                self.msgParts[splitUID]["numOfParts"] = numOfParts
                self.msgParts[splitUID]["lastSeen"] = time.time()
                self.msgParts[splitUID]["parts"] = {}

            # add part to msgParts:
            if part not in self.msgParts[splitUID]["parts"].keys():
                self.msgParts[splitUID]["parts"][part] = rest
                self.msgParts[splitUID]["lastSeen"] = time.time()

            marked = []
            histExNeeded = False

            for tmpUID in self.msgParts.keys():
                now = time.time()
                # check whether the message is complete
                if self.msgParts[tmpUID]["numOfParts"] == len(self.msgParts[tmpUID]["parts"]):
                    i = 1
                    msgData = ""
                    while i <= self.msgParts[tmpUID]["numOfParts"]:
                        msgData += self.msgParts[tmpUID]["parts"][i]
                        i += 1
                    marked.append(tmpUID)
                    # try to build Message object and decide what to do with it based on type
                    try:
                        msg = message.toMessage(msgData)
                    except message.MessageException, e:
                        logging.warn("unrecognised message " + str(e))

                    # process the created message:
                    self.processMessage(msg, addr)

                # if not complete
                else: 
                    # when came the last part?
                    if now - self.msgParts[tmpUID]["lastSeen"] > 300.0: # after 5 min, delete all parts of the splitUID tmp
                        logging.debug("5 Minutes have passed since we saw %i, deleting it", tmpUID)
                        marked.append(tmpUID)
                        histExNeeded = True

            for markedUID in marked:
                if histExNeeded:
                    if self.hosts:
                        neighbour = random.choice(self.hosts.keys()) #pick a rand host from hostlist
                        logging.debug("Request history from " + neighbour)
                        self.getHistory(neighbour) # and get some more hosts
                    else:
                        logging.error("You are not connected to the network!!! HostList is empty!")
                del self.msgParts[markedUID]

                
    #END OF startRecvLoop

    def processMessage(self, msg, fromAddr):
        '''processes the received messages'''
        if isinstance(msg, message.HeloMessage):
            # set your own ip if you dont know it
            if self.ip == "null":
                self.ip = msg.recipientIP
                self.key = Host.constructKey(self.ip, self.port)
                logging.info("You're now connected to a Hachat-network. Your key is " + self.key)
            
            senderIP = fromAddr[0]
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
                        self.gui.queue.put(msg) #gibt nachricht an gui weiter 
                        
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
                    logging.debug("received BYE, deleting " + key)
                    
                elif isinstance(msg, message.DeadMessage):
                    deadpeer = msg.peer
                    if deadpeer in self.knownPeers:
                        del self.knownPeers[deadpeer]
                    logging.debug("deleted " + deadpeer + " from knownPeers")
                
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
                        self.pushHistory(neighbour, msg.quant)
                        logging.debug("received: HistoryExchangeMessage Request. Will enter pushHistory()")
                    elif msg.level == "INIREQUEST":
                        self.pushMsgObjects(neighbour)
                        logging.debug("received: HistoryExchangeMessage Ininitial Request. Will push Msg Objects")
                    elif msg.level == "PUSH": 
                        logging.debug("received: HistoryExchangeMessage Push. Will enter HistoryControl")
                        self.HistoryControl(neighbour, msg.liste)
                    elif msg.level == "REQUESTMSGS":
                        logging.debug("received: HistoryExchangeMessage REQUESTMSGS. Will enter pushMsgObjects")
                        self.pushMsgObjects(neighbour, msg.liste)
                    else:
                        logging.warning("received HistoryExchangeMessage with unknown level!")
                        
                else:
                    logging.warn("hier sollte der Code nie ankommen, sonst gibt es unbekannte Message Unterklassen")
                    logging.warn(type(msg))
    #END OF processMessage

    def sendAll(self, msg):
        '''send Message Object to all your Peers'''
        for h in self.hosts.values():
                h.addToMsgQueue(msg)

    def sendText(self, text):
        '''make TXTMessage out of text and send to all hosts'''
        if text != "":
            msg = message.TextMessage(self.name, self.key, self.key, text)
            self.history.addMsg(msg) # add to own history
            self.sendAll(msg)

    def forwardMsg(self, msg, Oneneigbour=None):
        '''forwarding TextMessage, but not to initial sender
        if host is set, it will only forward to this single host'''
        msgSender = msg.origin
        # rewrite lastHop
        oldLastHop = msg.lastHop
        msg.lastHop = self.key
        if Oneneigbour == None:
            for h in self.hosts.values():
                hostAddr = Host.constructKey(h.hostIP, h.hostPort)
                # don't forward to origin or lastHop
                if msgSender != hostAddr and oldLastHop != hostAddr:
                    #logging.debug("Message " +  msg.text + " from " + msgSender + " will be forwarded to " + hostAddr )
                    h.addToMsgQueue(msg)
                else:
                    logging.debug("Message " + msg.text + " will not be forwarded to initial sender " + msgSender + " and lastHop " + oldLastHop)
        else:
            host = self.hosts[Oneneigbour]
            host.addToMsgQueue(msg)
            logging.debug("Will forward msg to " + Oneneigbour)

    def addToHosts(self, addr):
        '''check if already in hostlist otherwise add'''
        
        # construct key and tuple
        if isinstance(addr, str):
            key = addr
            (hostIP, hostPort) = re.split(':', addr, 1)
        elif isinstance(addr, tuple):
            (hostIP, hostPort) = addr
            key = Host.constructKey(hostIP, hostPort)
            
        # if host is not the peer itself
        if hostIP != self.ip or int(hostPort) != int(self.port):
            if not (key in self.hosts):
                # insert in host dict
                logging.debug("adding " + key + " to hostlist")
                Host(self, hostIP, hostPort)
            logging.debug("Now %d Hosts in HostList and %d Hosts in knownHosts"%(len(self.hosts), len(self.knownPeers)))
    
    def maintenanceLoop(self):
        '''thread which runs regularly maintenance tasks'''
        history_counter = self.counter
        while True:
            time.sleep(const.MAINTENANCE_SLEEP)
            logging.debug("maintenance start")
            logging.debug("counter: " + str(self.counter) + " ,history_counter: " + str(history_counter))
            
            # every 3 maintenance loops check if you have to delete host and fill Hostlist if needed
            if self.counter == 2:
                temp = self.hosts.keys()
                for key in temp:
                    host = self.hosts[key]
                    if host.lastSeen == 0:
                        logging.debug("deleting host " + key)
                        host.__del__()
                        del self.hosts[key]
                        # send DeadMessage to all your Peers
                        deadmsg = message.DeadMessage(self.key, key)
                        self.sendAll(deadmsg)
                    else:
                        host.lastSeen = 0 # reset lastSeen
                        
                    if len(temp) > const.INI_PEERLIMIT and host.bootstrap == True:
                        # delete Host if it was just for bootstrapping and you know enough others
                        msg = message.ByeMessage(self.key)
                        host.addToMsgQueue(msg)
                        logging.debug("deleting host " + key)
                        host.__del__()
                        del self.hosts[key]

                # do we have to few neighbors and we know other peers?
                if len(self.hosts) < const.MIN_PEERLIMIT:
                    if self.knownPeers:
                        #choose one
                        filler = random.choice(self.knownPeers.keys())
                        if filler != None:
                            logging.debug("got to few Peers, filling with " + filler)
                            (fillerIP, fillerPort) = filler.split(":", 2)
                            # and add it as a new host.
                            Host(self, fillerIP, fillerPort)
                            del self.knownPeers[filler]
                            logging.debug("Now %d Hosts in HostList and %d Hosts in knownHosts"%(len(self.hosts), len(self.knownPeers)))
                    elif self.hosts: #if nothing in knownPeers but in hostlist
                        neighbour = random.choice(self.hosts.keys()) #pick a rand host from hostlist
                        logging.debug("Request some peers from " + neighbour)
                        self.requestHosts(neighbour) # and get some more hosts
                    else:
                        logging.error("You are not connected to the network!!! HostList as well as List of known Hosts are empty.")
            
            # every 6 maintenance loops make HistoryExchange 
            if history_counter == 6:
                if self.hosts:
                    neighbour = random.choice(self.hosts.keys()) #pick a rand host from hostlist
                    logging.debug("Request history from " + neighbour)
                    self.getHistory(neighbour) # and get some more hosts
                else:
                    logging.error("You are not connected to the network!!! HostList is empty!")
                
            # send HELO from all hosts in hostlist
            for h in self.hosts.values():
                if h.lastSeen == 0: # but only if you haven't seen him for a while
                    h.sendHello()

            self.counter = (self.counter + 1) % 3 
            history_counter = (history_counter + 1) % 7 #odd number for not doing history and host exchange at the same time
            logging.debug("maintenance end")
            
    def sendLoop(self, test=False):
        '''send Message objects of all hosts from Queue as string'''
        if test == False:
            logging.debug("starting sendLoop")
        if test == True:
            logging.debug("starting sendLoop in test-Mode, will erase random parts of msgs")
            
        while True:
            time.sleep(0.1)
            for host in self.hosts.values():
                while host.msgQueue:
                    msg = host.msgQueue.popleft()
                    #convert to string to send over socket
                    msgStr = str(msg)

                    # create splitUID
                    splitUID = random.randint(0, 999999)

                    # check in how many parts the message has to be splitted
                    msgLen = len(msgStr)
                    maxMsgLen = const.HACHAT_BUFSIZE - len(str(splitUID)) - len(const.HACHAT_HEADER) - 10 # 10 for some space for the part and numOfParts variables
                    #logging.debug("%i - %i - %i - 10 = %i" % (const.HACHAT_BUFSIZE, len(str(splitUID)), len(const.HACHAT_HEADER), maxMsgLen))
                    numOfParts = (msgLen / maxMsgLen) + 1
                    logging.debug("splitting message %s of length %i into %i parts (maxMsgLen is %i)" % (msgStr, msgLen, numOfParts, maxMsgLen))
                    part = 1

                    # while there are parts left, construct and send them
                    while len(msgStr) > 0:
                        partStr = ",".join([const.HACHAT_HEADER, str(splitUID), str(part), str(numOfParts), msgStr[:maxMsgLen]])
                        msgStr = msgStr[maxMsgLen:]
                        
                        if test == True and part > 1:
                            #will drop random parts of the msg for testing
                            if random.randrange(0, 5) == 2:
                                logging.debug("will drop msg-part %d" %(part))
                                part += 1
                                continue
                                
                        logging.debug("sending msg part %i of %i: \"%s\" to %s:%i with length %d" %(part, numOfParts, partStr, host.hostIP, host.hostPort, len(partStr)))

                        # send the part
                        host.outSocket.sendto(partStr, (host.hostIP, host.hostPort))
                        part += 1
                    
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
        takefromhosts = 0
        
        # adjust quantitiy
        if len(self.knownPeers) < quant:
            takefromhosts = 1
            if len(self.knownPeers) + len(self.hosts) - 1 < quant: # -1 because neighbour is part of hostlist
                quant = len(self.knownPeers) + len(self.hosts) - 1 # give everything you have
        
        # get neighbour from hostlist
        try:
            neighbourHost = self.hosts[neighbour]
            neighbourIP = neighbourHost.hostIP
            neighbourPort = neighbourHost.hostPort
        except Exception, e:
            logging.error(str(e))
            
        while i < quant:
            if takefromhosts == 0:
                key = random.choice(self.knownPeers.keys())
            else:
                key = random.choice(self.knownPeers.keys() + self.hosts.keys())
            if key == None:
                break #nothing in knownPeers and hosts
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
            
    def getHistory(self, neighbour, initial=False):
        '''request History from neigbour; initial is true for a initial history exchange:
        this will skip pushing Hashes and immediately request msg.objects'''
        try:
            neighbourHost = self.hosts[neighbour]
            neighbourIP = neighbourHost.hostIP
            neighbourPort = neighbourHost.hostPort
        except Exception:
            raise message.MessageException("getHistory(): given neighbour needs to be a (IP,Port)Pair and needs to be in HostList")
        
        if initial == False:
            requestMsg = message.HistoryExchangeMessage(neighbourIP, neighbourPort, self.key, "REQUEST", quant=const.HISTORY_GETLIMIT)
        elif initial == True:
            requestMsg = message.HistoryExchangeMessage(neighbourIP, neighbourPort, self.key, "INIREQUEST", quant=const.HISTORY_INIGETLIMIT)
            
        neighbourHost.addToMsgQueue(requestMsg)# push it in hosts msgqueue
        logging.debug("Requested History from %s" %(neighbour))
        
    
    def pushHistory(self, neighbour, quant):
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
        in own History. If so, these lostMsg Hahses will be pushed back and by this
        the associated msgObjects are requested. '''
        
        logging.debug("entered HistoryControle, will check our History...")
        lostMsgHashes = []

        for o in historyList:
            if self.history.msgExists(o) == False:
                lostMsgHashes.append(o)
        
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
        
    def pushMsgObjects(self, neighbour, lostMsgHashes=None):
        '''pushes requested msgObjects back to neighbour'''
        logging.debug("entered pushMsgObjects, will push History Msg Objects")
        
        if lostMsgHashes == None:
            logging.debug("pushMsgObjects: will push last Msgs")
            historyList = self.history.getListMsgObjects(const.HISTORY_INIGETLIMIT)
            historyList.reverse() # to push it in right order
        else:
            historyList = []       
            for o in lostMsgHashes:
                historyList.append(self.history.getMsgObjects(o))
                historyList.reverse() # to push it in right order
        
        if len(historyList) > 0:
            for msg in historyList:
                self.forwardMsg(msg, neighbour)
                logging.debug("pushMsgObjects: pushed Msg %s to forwardMsg"%(msg.text))
        else: 
            logging.debug("Can't push History, no Msgs in History")


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
        
############################################################################
##################### test & debug  ########################################
############################################################################
        
    def generateMsgParts(self, quant=5, length=2000):
        '''generates random TextMsgs, if length > 1000
        there will be more then one msg-part'''
        texts = ["Test" + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(length-len("Test")+1)) for i in range(quant)]
        logging.debug("will send generated text-msgs")
        for t in texts:
            self.sendText(t)
