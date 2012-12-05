# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import re
import random

class Message(object): # inherit from object
        HEAD = "HACHAT VER0.1"
        type = None
        uid = None
        #msgstring = None
        def __init__(self):
                super(Message, self).__init__() # inherit from object
                # set unifier
                self.uid = random.randint(0, 999999)

        def __str__(self):
                '''cast Message to string'''
                # to implement
                pass
                
class HeloMessage(Message):
        '''regularly sent HELO Message'''
        
        recipientIP = None
        recipientPort = None
        senderIP = None
        senderPort = None
        
        def __init__(self, recipientIP, recipientPort, senderIP, senderPort):
                super(HeloMessage, self).__init__()
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

def toMessage(string):
        '''construct Message type from string'''
        try:
                (HEAD, type, uid, rest) = re.split(',', string, 3) #get first part of message
                
        except Exception, e:
                print e
                raise MessageException("malformed message recieved")
                
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
                        msg = HeloMessage(recipientIP, recipientPort, senderIP, senderPort)
                        return msg
                        
                except Exception, e:
                        raise MessageException("malformed message recieved")
                        print e
                        
                
        elif type == "MSG":
                # to implement
                pass
        else:
                raise MessageException("unknown type of message")
                
                
class MessageException(Exception):
        '''Custom Exception Type for Messages'''
        def __init__(self, value):
                 self.parameter = value
        def __str__(self):
                return repr(self.parameter)
