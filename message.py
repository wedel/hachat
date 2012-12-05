# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import re
import random
import hashlib

class Message(object): # inherit from object
        HEAD = "HACHAT VER0.1"
        type = None
        uid = None
        #msgstring = None
        def __init__(self, uid):
                super(Message, self).__init__() # inherit from object
                # set unifier
                if uid == None:
                        self.uid = random.randint(0, 999999)
                else:
                        self.uid = uid

        def __str__(self):
                '''cast Message to string'''
                # to implement
                raise NotImplementedError
                
class HeloMessage(Message):
        '''regularly sent HELO Message'''
        
        recipientIP = None
        recipientPort = None
        senderIP = None
        senderPort = None
        
        def __init__(self, recipientIP, recipientPort, senderIP, senderPort, uid=None):
                super(HeloMessage, self).__init__(uid)
                self.type = "HELO"
                
                # set recipient and sender
                if recipientIP == None or recipientPort == None:
                        raise Exception("HeloMessage needs recipient!")
                else:
                        self.recipientIP = recipientIP
                        self.recipientPort = recipientPort
                if senderIP == None or senderPort == None:
                        raise Exception("HeloMessage needs sender!")
                else:
                        self.senderIP = senderIP
                        self.senderPort = senderPort
                
        def __str__(self):
                '''implements interface'''
                string = ",".join([self.HEAD, self.type, str(self.uid), self.recipientIP, str(self.recipientPort), self.senderIP, str(self.senderPort)])
                return string
                
class TextMessage(Message):
        ''' normal Text Messages'''
        
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
                        (hash, name, text) = re.split(',', rest, 2) # get rest if message
                        
                except Exception, e:
                        raise MessageException("malformed TextMessage recieved")
                        print e
                
                # test hash
                msg = TextMessage(name, text, uid)
                
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
