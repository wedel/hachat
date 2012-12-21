# coding = utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import socket
import threading
import time
from collections import deque
import message
import logging


class Host:
    '''Class representing a connection to another peer'''
    # myPeer = None
    #hostIP = None # IP of recipient
    #hostPort = 0 # port of recipient
    #outSocket = None
    
    @classmethod
    def constructKey(self, hostIP, hostPort):
        '''Class method: construct key to identify hosts in hostlist'''
        if hostIP == "localhost" or hostIP == "127.0.1.1":
            ip = "127.0.0.1"
        else:
            ip = hostIP
            
        port = str(hostPort)
        key = ip + ':' + port
        
        return key

    def __init__(self, peer, hostIP, hostPort):
        
        # set myPeer:
        self.myPeer = peer

        # variable to check you get regularly helo
        self.lastSeen = 1
        
        # init own msgQueue
        self.msgQueue = deque()
        
        self.outSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.hostIP = hostIP # IP of recipient
        self.hostPort = int(hostPort) # port of recipient
        
        if self.myPeer == None:
            raise Exception("Host-Class needs peer")
        else:
            # add Host to its Peers Hostlist
            key = Host.constructKey(hostIP, hostPort)
            self.myPeer.hosts[key] = self
            self.sendHello() # send HELO to Host
            

    def sendHello(self):
        #print 'called sendhello method'
        # helo = message.HeloMessage(self.hostIP, self.hostPort, self.myPeer.ip, self.myPeer.port)
        helo = message.HeloMessage(self.hostIP, self.hostPort, self.myPeer.ip, self.myPeer.port)
        self.addToMsgQueue(helo)                
                
    def addToMsgQueue(self, msg):
        '''check if message is type Message and add to Queue'''
        if isinstance(msg, message.Message):
            logging.debug("adding " + str(msg) + " to MsgQueue to " + self.hostIP + ":" + str(self.hostPort))
            self.msgQueue.append(msg)
        else:
            raise Exception("Will only send Message objects!")

    def __del__(self):
        # wait until Queue empty
        while self.msgQueue:
            pass
        time.sleep(0.5)
        self.outSocket.close()
