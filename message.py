# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

'''module which provides all message types for hachat'''

import re
import random
import hashlib
from collections import OrderedDict, deque
import logging

class Message(object): # inherit from object
    '''abstract class all other message types will inherit from'''

    def __init__(self, uid):
        ''' build Message with supplied uid
        or otherwise get a random uid'''
        self.type = None
        self.uid = None
        
        super(Message, self).__init__() # inherit from object
        # set unifier
        if uid == None:
            self.uid = random.randint(0, 999999)
        else:
            self.uid = uid

    def __str__(self):
        '''cast Message to string'''
        raise NotImplementedError # must be implemented by SubClass
            
class HeloMessage(Message):
    '''regularly sent HELO Message which exchange information on IP and Port
    Message layout: | type | uid | recipientIP | recipientPort | senderIP | senderPort | '''
    
    
    def __init__(self, recipientIP, recipientPort, senderIP, senderPort, uid=None):
        self.recipientIP = None
        self.recipientPort = None
        self.senderPort = None
        super(HeloMessage, self).__init__(uid)
        self.type = "HELO"
        
        # set recipient and sender
        if recipientIP == None or recipientPort == None:
            raise MessageException("HeloMessage needs recipient!")
        else:
            self.recipientIP = recipientIP
            self.recipientPort = recipientPort
        if senderIP == None or senderPort == None:
            #if senderPort == None:
            print self
            raise MessageException("HeloMessage needs sender!")
        else:
            self.senderIP = senderIP
            self.senderPort = senderPort
            
    def __str__(self):
        '''implements interface'''
        string = ",".join([self.type, str(self.uid), self.recipientIP, str(self.recipientPort), self.senderIP, str(self.senderPort)])
        return string

class HostExchangeMessage(Message):
    '''for request and pushing Hosts
    Message layout: | type | uid | recipientIP | recipientPort | origin key | level | quant | listofHosts |'''
    
    
    
    
    def __init__(self, recipientIP, recipientPort, origin, level, quant=None , listofHosts=None, uid=None):
        super(HostExchangeMessage, self).__init__(uid)
        self.type = "HOSTEXCHANGE"
        self.level = None
        self.listofHosts = None
        self.quant = None
                        
        # set recipient and sender
        if recipientIP == None or recipientPort == None:
            raise Exception("HostExchangeMessage needs recipient!")
        else:
            self.recipientIP = recipientIP
            self.recipientPort = recipientPort
                
        if origin == None:
            print self
            raise Exception("HostExchangeMessage needs origin - you must be connected to the network!")
        else:
            self.origin = origin
                
        if level == None:
            raise Exception("HostExchangeMessage needs level!")
        else:
            self.level = level
            
            if self.level == "REQUEST":
                if quant == None:
                    raise Exception("A Requesting HostExchangeMessage needs a defined quant of Hosts!")
                else: 
                    self.quant = quant
                    
            if self.level == "PUSH":
                if listofHosts == None:
                    raise Exception("A Pushing HostExchangeMessage needs to have a list of Hosts defined!")
                else:
                    self.listofHosts = listofHosts
            
    def __str__(self):
        '''implements interface'''
        string = ",".join([self.type, str(self.uid), self.recipientIP, str(self.recipientPort), self.origin, self.level, str(self.quant), str(self.listofHosts)])
        return string
                
class HistoryExchangeMessage(Message):
    '''for request and pushing Hosts
    Message layout: | type | uid | recipientIP | recipientPort | origin key | level | quant | liste | '''
    
    
    
    def __init__(self, recipientIP, recipientPort, origin, level, quant=None, liste=None, uid=None):
        super(HistoryExchangeMessage, self).__init__(uid)
        self.type = "HISTORYEXCHANGE"
        self.level = None #level of exchange
        self.liste = None #list for everything
        self.quant = None #quantity of exchanged msgs
                        
        # set recipient and sender
        if recipientIP == None or recipientPort == None:
            raise Exception("HistoryExchangeMessage needs recipient!")
        else:
            self.recipientIP = recipientIP
            self.recipientPort = recipientPort
                
        if origin == None:
            print self
            raise Exception("HistoryExchangeMessage needs origin - you must be connected to the network!")
        else:
            self.origin = origin
                
        if level == None:
            raise Exception("HistoryExchangeMessage needs level!")
        else:
            self.level = level
            
            if self.level == "REQUEST" or self.level == "INIREQUEST":
                if quant == None:
                    raise Exception("A Requesting HistoryExchangeMessage needs a defined quant of Msgs!")
                else: 
                    self.quant = quant
                    
            elif self.level == "PUSH":
                if liste == None:
                    raise Exception("A Pushing HistoryExchangeMessage needs to have a list of History!")
                else:
                    self.liste = liste
            
            elif self.level == "REQUESTMSGS":
                if liste == None:
                    raise Exception("A GetMsgs HistoryExchangeMessage needs a list of Msg Hashes to Request!")
                else:
                    self.liste = liste
            else:
                logging.warning("HistoryExchangeMessage with unknown level!")
            
    def __str__(self):
        '''implements interface'''
        string = ",".join([self.type, str(self.uid), self.recipientIP, str(self.recipientPort), self.origin, self.level, str(self.quant), str(self.liste)])
        return string



class TextMessage(Message):
    ''' normal Text Messages
    Message layout: | type | uid | hash | sender name | origin key | lastHop key | text | '''
    
    def __init__(self, name, origin, lastHop, text, uid=None):
        super(TextMessage, self).__init__(uid)
        self.type = "TXT"
        self.name = name
        if origin != None:
            self.origin = origin
        else:
            raise MessageException("TextMessage: Sender-IP mustn't be None")
        self.lastHop = lastHop
        self.text = text
        
        # make md5-hash over uid, name, text
        hasher = hashlib.md5()
        hasher.update(str(self.uid))
        hasher.update(self.name)
        hasher.update(self.origin)
        hasher.update(self.text)
        self.hash = hasher.hexdigest()
    
    def __str__(self):
        '''implements interface'''
        string = ",".join([self.type, str(self.uid), self.hash, self.name, self.origin, self.lastHop, self.text])
        return string
            
class ByeMessage(Message):
    '''Message Type to be send when leaving'''
    
    def __init__(self, origin, uid=None):
        super(ByeMessage, self).__init__(uid)
        self.type = "BYE"
        self.origin = origin
    
    def __str__(self):
        '''implements interface'''
        string = ",".join([self.type, str(self.uid), self.origin])
        return string

        
class DeadMessage(Message):
    '''Message that tells a Peer that another Peer is dead'''
    def __init__(self, origin, peer, uid=None):
        super(DeadMessage, self).__init__(uid)
        self.type = "DEAD"
        self.origin = origin
        self.peer = peer
    
    def __str__(self):
        '''implements interface'''
        string = ",".join([self.type, str(self.uid), self.origin, self.peer])
        return string
            

def toMessage(string):
    '''construct Message type from string'''
    try:
        (type, uid, rest) = re.split(',', string, 2) # get first part of message
        uid = int(uid)
            
    except Exception, e:
        print e
        raise MessageException("malformed Message recieved")
            
            
    # decide on type of message        
    if type == "HELO":
        try:
            (recipientIP, recipientPort, senderIP, senderPort) = re.split(',', rest, 3) # get rest of message
            # cast ports to int
            recipientPort = int(recipientPort)
            senderPort = int(senderPort)
            msg = HeloMessage(recipientIP, recipientPort, senderIP, senderPort, uid)
            return msg
                
        except Exception, e:
            raise MessageException("malformed HeloMessage recieved")
            print e
                    
    elif type == "TXT":
        try:
            (hash, name, origin, lastHop, text) = re.split(',', rest, 4) # get rest if message
                
        except Exception, e:
            raise MessageException("malformed TextMessage recieved")
            print e
        
        msg = TextMessage(name, origin, lastHop, text, uid)
        
         # test hash
        if msg.hash != hash:
            raise MessageException("TextMessage has wrong hash " + str(msg))
        else:
            return msg # return good TextMessage
                    
    elif type == "BYE":
        try:
            origin = str(rest) # get rest of message
            msg = ByeMessage(origin, uid)
        except Exception, e:
            raise MessageException("malformed ByeMessage recieved")
            print e
        
        return msg
    
    elif type == "DEAD":
        try:
            (origin, peer) = re.split(',', rest, 1) #get rest of message
            msg = DeadMessage(origin, peer, uid)
        except Exception, e:
            raise MessageException("malformed DeadMessage recieved")
            print e
        
        return msg
    
    elif type == "HOSTEXCHANGE":
        try:
            (recipientIP, recipientPort, origin, level, quant, listofHosts) = re.split(',', rest, 5) # get rest if message
        except Exception, e:
            raise MessageException("malformed HostExchangeMessage recieved")
            print e
                
        if level == "REQUEST":               
            msg = HostExchangeMessage(recipientIP, recipientPort, origin, level, quant=int(quant), uid=uid)
            logging.debug("HostExchangeMessage: got REQUEST")
            return msg # return good HostExchangeMessage
        elif level == "PUSH":
            list = eval(listofHosts)
            msg = HostExchangeMessage(recipientIP, recipientPort, origin, level, listofHosts=list, uid=uid)
            logging.debug("HostExchangeMessage: got PUSH")
            return msg # return good HostExchangeMessage
            
    elif type == "HISTORYEXCHANGE":
        try:
            (recipientIP, recipientPort, origin, level, quant, liste) = re.split(',', rest, 5) # get rest if message
        except Exception, e:
            raise MessageException("malformed HistoryExchangeMessage recieved")
            print e
                
        if level == "REQUEST":               
            msg = HistoryExchangeMessage(recipientIP, recipientPort, origin, level, quant=int(quant), uid=uid)
            logging.debug("HostExchangeMessage: got REQUEST")
            return msg # return good HistoryExchangeMessage
        elif level == "INIREQUEST":
            msg = HistoryExchangeMessage(recipientIP, recipientPort, origin, level, quant=int(quant), uid=uid)
            logging.debug("HostExchangeMessage: got INIREQUEST")
            return msg # return good HistoryExchangeMessage
        elif level == "PUSH":
            evallist = eval(liste)
            msg = HistoryExchangeMessage(recipientIP, recipientPort, origin, level, liste=evallist, uid=uid)
            logging.debug("HistorExchangeMessage: got PUSH")
            return msg # return good HistoryExchangeMessage
        elif level == "REQUESTMSGS":
            evallist = eval(liste)
            msg = HistoryExchangeMessage(recipientIP, recipientPort, origin, level, liste=evallist, uid=uid)
            logging.debug("HistorExchangeMessage: got GETMSGS")
            return msg # return good HistoryExchangeMessage
    else:
        raise MessageException("unknown type of message")
            
            
class MessageException(Exception):
    '''Custom Exception Type for Messages'''
    def __init__(self, value):
        super(MessageException, self).__init__()
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class History:
    '''Klasse History speichert und ueberprueft Text-Msgs'''

    def __init__(self, msgLimit, hashLimit):
        self.msgDic = OrderedDict()  
        self.hashDic = deque()
        self.msgLimit = msgLimit
        self.hashLimit = hashLimit
        logging.debug("History applied")

    def addMsg(self, msg):
        '''add TXTMessage to History'''
        self.msgDic[msg.hash] = msg
        self.hashDic.append(msg.hash)
        logging.debug("Laenge der msgDic %d, laenge der HashDic %d" %(len(self.msgDic), len(self.hashDic)))

        if len(self.msgDic) > self.msgLimit: 
            if len(self.hashDic) > self.hashLimit:
                hashQuant = ((len(self.hashDic))-self.hashLimit)
                msgQuant = ((len(self.msgDic))-self.msgLimit)
                self.removeMsg(msgQuant, hashQuant)

            elif len(self.hashDic) <= self.hashLimit:
                msgQuant = ((len(self.msgDic))-self.msgLimit)
                self.removeMsg(msgQuant, 0)
        logging.debug("added msg to history")

    def msgExists(self, msghash):
        '''Message is already in History (test on hash)'''
        if msghash in self.hashDic:
            return True
        else:
            return False

    def msgSafed(self, msg):
        '''Message is already in History (test on TMssage object)'''
        if msg.hash in self.msgDic:
            return True
        else:
            return False

    def removeMsg(self, msgQuant=0, hashQuant=0):
        '''remove x Messages from History'''
        if msgQuant > 0:
            if len(self.msgDic) >= msgQuant:
                for i in range(0, msgQuant):
                    self.msgDic.popitem(last=False)
                logging.debug("Erased %d msgs out of History" % msgQuant)
            else:
                raise MessageException('Can not remove msg out of MsgDict. Its to small')

        if hashQuant > 0:
            if len(self.hashDic) >= hashQuant:
                for i in range(0, msgQuant):
                    self.hashDic.popleft()
                logging.debug("Erased %d hashes out of Hash-History" % hashQuant)
            else:
                raise MessageException('Can not remove hashes out of HashDict. Its to small')
        
    def getMsgHashes(self, msgQuant):
        '''get a list of hashes from x Messages'''
        hashList = []
        if len(self.msgDic) < msgQuant:
            msgQuant = len(self.msgDic)
            logging.debug("reduced msgQuant to Length of msgDic") 
                    
        for i in range(0, msgQuant):
            index = (len(self.msgDic)-i-1)
            hashList.append(list(self.msgDic.keys())[index])
        #return keys (hashes of msgs) of saved msgs
        return hashList
        
    def getListMsgObjects(self, msgQuant):
        '''get a list of x Messages'''
        msgList = []
        if len(self.msgDic) < msgQuant:
            msgQuant = len(self.msgDic)
            logging.debug("reduced msgQuant to Length of msgDic") 
                    
        for i in range(0, msgQuant):
            index = (len(self.msgDic)-i-1)
            msg = list(self.msgDic.values())[index]
            msgList.append(msg)
        #return list of values (msg objects) of saved msgs
        return msgList
        
        
    def getMsgObjects(self, msgHash):
        '''get Message object from hash'''
        msg = self.msgDic[msgHash]
        #return value (msg objects) of saved msgs
        return msg
