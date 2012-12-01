# coding=utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import re

# TODO: absender und empfänger

class Message:
        HEAD = "HACHAT VER0.1"
        type = None
        msgstring = None
        def __init__(self, type, msgstring):
                self.msgstring = msgstring
                # testing for known message types
                if type == "HELO" or type == "MSG":
                        self.type = type
                else:
                        raise Exception("Unknown message type!")
                        
        def __str__(self):
                string = ",".join([self.HEAD, self.type, self.msgstring])
                return string
                
def toMessage(string):
        '''construct Message type from string'''
        (HEAD, type, msgstring) = re.split(',', string, 3)
        if HEAD == "HACHAT VER0.1":
                return Message(type, msgstring)
