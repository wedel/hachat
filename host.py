# coding = utf-8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import socket
import threading
import time
from collections import deque
import message


class Host:
    myPeer = None
    hostIP = None
    outSocket = None
    inPort = 0
    hostPort = 0
    sendThread = None
    msgQueue = deque()

    def __init__(self, myPeer, hostIP, hostPort):
        self.outSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.myPeer = myPeer
        self.hostIP = hostIP
        self.hostPort = int(hostPort)
        try: 
            self.sendThread = threading.Thread(target=self.startSendLoop) 
            self.sendThread.daemon = True
            self.sendThread.start()
        except (KeyboardInterrupt,SystemExit):
            print "Quitting.."


    def sendHello(self):
        print 'called sendhello method'
        hoststr = self.hostIP + ":" + str(self.hostPort)
        hellostr = "HELLO YOU:" + hoststr + " CALLME:" + str(self.myPeer.port)
        helo = message.Message("HELO", hellostr)
        self.addToMsgQueue(helo)

    def startSendLoop(self):
        while True:
            time.sleep(3)
            if self.msgQueue:
                msg = self.msgQueue.popleft()
                #convert to string to send over socket
                msgStr = str(msg)                
                self.outSocket.sendto(msgStr, (self.hostIP, self.hostPort))
            
    def addToMsgQueue(self, message):
        print "adding", message
        self.msgQueue.append(message)



    def __del__(self):
        self.outSocket.close()
        self.thread.stop()
