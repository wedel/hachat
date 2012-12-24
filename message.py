# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import const
import re
import random
import hashlib
from collections import OrderedDict, deque
import logging

class Message(object): # inherit from object
    def __init__(self, uid):
        ''' build Message with supplied uid
        or otherwise get a random uid'''
        self.HEAD = const.HACHAT_HEADER
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
    Message layout: | HEAD | type | uid | recipientIP | recipientPort | senderIP | senderPort | '''
    
    
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
        string = ",".join([self.HEAD, self.type, str(self.uid), self.recipientIP, str(self.recipientPort), self.senderIP, str(self.senderPort)])
        # string = ",".join([self.HEAD, self.type, str(self.uid), self.recipientIP, str(self.recipientPort), str(self.senderPort)])
        return string

class HostExchangeMessage(Message):
        '''for request and pushing Hosts
        Message layout: | HEAD | type | uid | recipientIP | recipientPort | senderPort | level | quant | listofHosts |'''
        recipientIP = None
        recipientPort = None
        # senderIP = None
        senderPort = None
        level = None
        listofHosts = None
        quant = None
        
        
        def __init__(self, recipientIP, recipientPort, senderPort, level, quant=None , listofHosts=None, uid=None):
                super(HostExchangeMessage, self).__init__(uid)
                self.type = "HOSTEXCHANGE"
                                
                # set recipient and sender
                if recipientIP == None or recipientPort == None:
                        raise Exception("HostExchangeMessage needs recipient!")
                else:
                        self.recipientIP = recipientIP
                        self.recipientPort = recipientPort
                # if senderIP == None or senderPort == None:
                if senderPort == None:
                        print self
                        raise Exception("HostExchangeMessage needs sender!")
                else:
                        # self.senderIP = senderIP
                        self.senderPort = senderPort
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
                string = ",".join([self.HEAD, self.type, str(self.uid), self.recipientIP, str(self.recipientPort), str(self.senderPort), self.level, str(self.quant), str(self.listofHosts)])
                return string


class HistReqMessage(Message):
    '''HistReqMessages are sent when a peer wants to request the history of another peer. quantity is the number of history entries the other peer should send uns back.
    Message layout: | HEAD | type | uid | quantity | '''

    def __init__(self, quantity, uid=None):
        super(HistReqMessage, self).__init__(uid)
        self.type = "HISTREQ"
        
        # set recipient and sender
        if quantity == None:
                raise MessageException("HistReqMessage needs quantity!")
        else:
                self.reqQuant = quantity
    def __str__(self):
        '''implements interface'''
        string = ",".join([self.HEAD, self.type, str(self.uid), str(self.reqQuant)])
        return string
        
class TextMessage(Message):
    ''' normal Text Messages
    Message layout: | HEAD | type | uid | hash | sender name | origin key | lastHop key | text | '''
    
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
        string = ",".join([self.HEAD, self.type, str(self.uid), self.hash, self.name, self.origin, self.lastHop, self.text])
        return string
            
class ByeMessage(Message):
    '''Message Type to be send when leaving'''
    
    def __init__(self, origin, uid=None):
        super(ByeMessage, self).__init__(uid)
        self.type = "BYE"
        self.origin = origin
    
    def __str__(self):
        '''implements interface'''
        string = ",".join([self.HEAD, self.type, str(self.uid), self.origin])
        return string
            

def toMessage(string):
    '''construct Message type from string'''
    try:
        (HEAD, type, uid, rest) = re.split(',', string, 3) # get first part of message
        uid = int(uid)
            
    except Exception, e:
        print e
        raise MessageException("malformed Message recieved")
            
     # check if Hachat Message
    if HEAD != const.HACHAT_HEADER:
        raise MessageException("wrong Header: " + HEAD)
            
    # decide on type of message        
    if type == "HELO":
        try:
            (recipientIP, recipientPort, senderIP, senderPort) = re.split(',', rest, 3) # get rest of message
            # (recipientIP, recipientPort, senderPort) = re.split(',', rest, 2) # get rest of message
            # cast ports to int
            recipientPort = int(recipientPort)
            senderPort = int(senderPort)
            msg = HeloMessage(recipientIP, recipientPort, senderIP, senderPort, uid)
            # msg = HeloMessage(recipientIP, recipientPort, senderPort, uid)
            return msg
                
        except Exception, e:
            raise MessageException("malformed HeloMessage recieved")
            print e
                    
    elif type == "HISTREQ":
        try:
            quantity = int(rest)
            msg = HistReqMessage(uid, quantity)
            return msg

        except Exception, e:
            raise MessageException("malformed HistReqMessage recieved")
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
        except Exception, e:
            raise MessageException("malformed ByeMessage recieved")
        
        msg = ByeMessage(origin, uid)
        return msg
    
    elif type == "HOSTEXCHANGE":
        try:
            (recipientIP, recipientPort, senderPort, level, quant, listofHosts) = re.split(',', rest, 5) # get rest if message
        except Exception, e:
            raise MessageException("malformed HostExchangeMessage recieved")
            print e
                
        if level == "REQUEST":               
            msg = HostExchangeMessage(recipientIP, recipientPort, senderPort, level, quant=int(quant), uid=uid)
            logging.debug("HostExchangeMessage: got REQUEST")
            return msg # return good HostExchangeMessage
        elif level == "PUSH":
            list = eval(listofHosts)
            msg = HostExchangeMessage(recipientIP, recipientPort, senderPort, level, listofHosts=list, uid=uid)
            logging.debug("HostExchangeMessage: got PUSH")
            return msg # return good HostExchangeMessage
            
    else:
        raise MessageException("unknown type of message")
            
            
class MessageException(Exception):
    '''Custom Exception Type for Messages'''
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class History:
    '''Klasse History speichert und ueberprueft Text-Msgs'''


    def __init__(self, msgLimit=100, hashLimit=1000):
        self.msgDic = OrderedDict()  
        self.hashDic = deque()
        self.msgLimit = msgLimit
        self.hashLimit = hashLimit
        logging.debug("History applied")

    def addMsg(self, msg):
        self.msgDic[msg.hash] = msg
        self.hashDic.append(msg.hash)
        logging.debug("Laenge der msgDic %d, laenge der HashDic %d" %(len(self.msgDic), len(self.hashDic)))

        if len(self.msgDic) > self.msgLimit: 
            if len(self.hashDic) > self.hashLimit:
                hashQuant = ((len(self.hashDic))-self.hashLimit)
                msgQuant = ((len(self.msgDic))-self.msgLimit)
                self.removeMsg(msgQuant,hashQuant)

            elif len(self.hashDic) <= self.hashLimit:
                msgQuant = ((len(self.msgDic))-self.msgLimit)
                self.removeMsg(msgQuant,0)
        logging.debug("added msg to history")

    def msgExists(self,msg):
        if msg.hash in self.hashDic:
            return True
        else:
            return False

    def msgSafed(self,msg):
        if msg.hash in self.msgDic:
            return True
        else:
            return False

    def removeMsg(self, msgQuant=0, hashQuant=0):
        if msgQuant > 0:
            if len(self.msgDic) >= msgQuant:
                for i in range(0,msgQuant):
                    self.msgDic.popitem(last=False)
                logging.debug("Erased %d msgs out of History" % msgQuant)
            else:
                raise MessageException('Can not remove msg out of MsgDict. Its to small')

        if hashQuant > 0:
            if len(self.hashDic) >= hashQuant:
                for i in range(0,msgQuant):
                    self.hashDic.popleft()
                logging.debug("Erased %d hashes out of Hash-History" % hashQuant)
            else:
                raise MessageException('Can not remove hashes out of HashDict. Its to small')

                

