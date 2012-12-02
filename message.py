# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import re

class Message(object): # inherit from object
        HEAD = "HACHAT VER0.1"
        recipientIP = None
        recipientPort = None
        senderIP = None
        senderPort = None
        type = None
        msgstring = None
        def __init__(self, recipientIP, recipientPort, senderIP, senderPort, type, msgstring):
                super(Message, self).__init__() # inherit from object
                self.msgstring = msgstring
                # testing for known message types
                if type == "HELO" or type == "MSG":
                        self.type = type
                else:
                        raise Exception("Unknown message type!")
                        
                # set recipient and sender
                if recipientIP == None or recipientPort == None:
                        raise Exception("Message needs recipient!")
                else:
                        self.recipientIP = recipientIP
                        self.recipientPort = recipientPort
                if senderIP == None or senderPort == None:
                        raise Exception("Message needs sender!")
                else:
                        self.senderIP = senderIP
                        self.senderPort = senderPort
                        
        def __str__(self):
                '''cast Message to string'''
                string = ",".join([self.HEAD, self.recipientIP, str(self.recipientPort), self.senderIP, str(self.senderPort), self.type, self.msgstring])
                return string
                
def toMessage(string):
        '''construct Message type from string'''
        try:
                #debug
                print string
                #enddebug
                (HEAD, recipientIP, recipientPort, senderIP, senderPort, type, msgstring) = re.split(',', string, 7)
        except Exception,e:
                #raise MessageError("malformed message recieved")
                print e
                raise Exception("malformed message recieved")
                
        # cast ports to int
        recipientPort = int(recipientPort)
        senderPort = int(senderPort)
                
        if HEAD == "HACHAT VER0.1":
                return Message(recipientIP, recipientPort, senderIP, senderPort, type, msgstring)
        else:
                #raise MessageError("wrong Header: " + HEAD)
                raise Exception("wrong Header: " + HEAD)
