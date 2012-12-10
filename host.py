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
    myPeer = None
    hostIP = None # IP of recipient
    outSocket = None
    inPort = 0
    hostPort = 0 # port of recipient
    sendThread = None
    # msgQueue = deque()

    def __init__(self, myPeer, hostIP, hostPort):
        
        # init own msgQueue
        self.msgQueue = deque()
        
        self.outSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.myPeer = myPeer
        self.hostIP = hostIP
        self.hostPort = int(hostPort)
        
        # start send thread
        try: 
            self.sendThread = threading.Thread(target=self.startSendLoop) 
            self.sendThread.daemon = True
            self.sendThread.start()
        except (KeyboardInterrupt,SystemExit):
            print "Quitting.."


    def sendHello(self):
        #print 'called sendhello method'
        # helo = message.HeloMessage(self.hostIP, self.hostPort, self.myPeer.ip, self.myPeer.port)
        helo = message.HeloMessage(self.hostIP, self.hostPort, self.myPeer.port)
        self.addToMsgQueue(helo)

    def startSendLoop(self):
        '''send Message objects from Queue as string'''
        while True:
            time.sleep(1)
            if self.msgQueue:
                msg = self.msgQueue.popleft()
                #convert to string to send over socket
                msgStr = str(msg)
                logging.debug("tring to send msg: %s to %s" %(msgStr, self.hostIP))
                self.outSocket.sendto(msgStr, (self.hostIP, self.hostPort))
                
                
    def addToMsgQueue(self, msg):
        '''check if message is type Message and add to Queue'''
        if isinstance(msg, message.Message):
            logging.debug("adding " + str(msg) + " to MsgQueue to " + self.hostIP + ":" + str(self.hostPort))
            self.msgQueue.append(msg)
        else:
            raise Exception("Will only send Message objects!")

    def __del__(self):
        self.outSocket.close()
        self.thread.stop()
