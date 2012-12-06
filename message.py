# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import re
import random
import hashlib
from collections import OrderedDict, deque

class Message(object): # inherit from object
        HEAD = "HACHAT VER0.1"
        type = None
        uid = None
        #msgstring = None
        def __init__(self, uid):
                ''' build Message with supplied uid
                or otherwise get a random uid'''
                
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
        Message layout: | HEAD | type | uid | recipientIP | recipientPort | senderPort | '''
        
        recipientIP = None
        recipientPort = None
        # senderIP = None
        senderPort = None
        
        def __init__(self, recipientIP, recipientPort, senderPort, uid=None):
                super(HeloMessage, self).__init__(uid)
                self.type = "HELO"
                
                # set recipient and sender
                if recipientIP == None or recipientPort == None:
                        raise Exception("HeloMessage needs recipient!")
                else:
                        self.recipientIP = recipientIP
                        self.recipientPort = recipientPort
                # if senderIP == None or senderPort == None:
                if senderPort == None:
                        print self
                        raise Exception("HeloMessage needs sender!")
                else:
                        # self.senderIP = senderIP
                        self.senderPort = senderPort
                
        def __str__(self):
                '''implements interface'''
                # string = ",".join([self.HEAD, self.type, str(self.uid), self.recipientIP, str(self.recipientPort), self.senderIP, str(self.senderPort)])
                string = ",".join([self.HEAD, self.type, str(self.uid), self.recipientIP, str(self.recipientPort), str(self.senderPort)])
                return string
                
class TextMessage(Message):
        ''' normal Text Messages
        Message layout: | HEAD | type | uid | hash | sender name | text | '''
        
        hash = None
        name = None
        text = None
        
        def __init__(self, name, text, uid=None):
                super(TextMessage, self).__init__(uid)
                self.type = "TXT"
                self.name = name
                self.text = text
                
                # make md5-hash over uid, name, text
                hasher = hashlib.md5()
                hasher.update(str(self.uid))
                hasher.update(self.name)
                hasher.update(self.text)
                self.hash = hasher.hexdigest()
        
        def __str__(self):
                '''implements interface'''
                string = ",".join([self.HEAD, self.type, str(self.uid), self.hash, self.name, self.text])
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
        if HEAD != "HACHAT VER0.1":
                raise MessageException("wrong Header: " + HEAD)
                
        # decide on type of message        
        if type == "HELO":
                try:
                        # (recipientIP, recipientPort, senderIP, senderPort) = re.split(',', rest, 3) # get rest of message
                        (recipientIP, recipientPort, senderPort) = re.split(',', rest, 2) # get rest of message
                        # cast ports to int
                        recipientPort = int(recipientPort)
                        senderPort = int(senderPort)
                        #msg = HeloMessage(recipientIP, recipientPort, senderIP, senderPort, uid)
                        msg = HeloMessage(recipientIP, recipientPort, senderPort, uid)
                        return msg
                        
                except Exception, e:
                        raise MessageException("malformed HeloMessage recieved")
                        print e
                        
                
        elif type == "TXT":
                try:
                        (hash, name, text) = re.split(',', rest, 2) # get rest if message
                        
                except Exception, e:
                        raise MessageException("malformed TextMessage recieved")
                        print e
                
                msg = TextMessage(name, text, uid)
                
                 # test hash
                if msg.hash != hash:
                        raise MessageException("TextMessage has wrong hash")
                else:
                        return msg # return good TextMessage
                
        else:
                raise MessageException("unknown type of message")
                
                
class MessageException(Exception):
        '''Custom Exception Type for Messages'''
        def __init__(self, value):
                 self.parameter = value
        def __str__(self):
                return repr(self.parameter)

class History:
    '''Klasse History speichert und ueberprueft
       Text-Msgs'''
    
    msgDic = OrderedDict()  
    hashDic = deque()

    def __init__(self, msgLimit=100, hashLimit=1000):
        self.msgLimit = msgLimit
        self.hashLimit = hashLimit
        print "History entered..."

    def addMsg(self, msg):
        self.msgDic[msg.hash] = msg
        self.hashDic.append(msg.hash)
        print "Laenge der msgDic %d, laenge der HashDic %d" %(len(self.msgDic), len(self.hashDic))

        if len(self.msgDic) > self.msgLimit: 
            if len(self.hashDic) > self.hashLimit:
                hashQuant = ((len(self.hashDic))-self.hashLimit)
                msgQuant = ((len(self.msgDic))-self.msgLimit)
                self.removeMsg(msgQuant,hashQuant)

            elif len(self.hashDic) <= self.hashLimit:
                msgQuant = ((len(self.msgDic))-self.msgLimit)
                self.removeMsg(msgQuant,0)
        print "added msg to history"
    
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
            if len(msgDic) >= msgQuant:
                for i in range(0,msgQuant):
                    self.msgDic.popitem(last=False)
                print "Erased %d msgs out of History" % msgQuant
            else:
                raise MessageException('Can not remove msg out of MsgDict. Its to small')

        if hashQuant > 0:
            if len(hashDic) >= hashQuant:
                for i in range(0,msgQuant):
                    self.hashDic.popleft()
                print "Erased %d hashes out of Hash-History" % hashQuant
            else:
                raise MessageException('Can not remove hashes out of HashDict. Its to small')

                    
     




