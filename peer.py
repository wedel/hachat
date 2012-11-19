#!/usr/bin/python


import socket
import threading

class Peer:
    
    def __init__(self, port, ip_addr=None, peer_id = None):
        """init des clients """
        print "Start"
        self.port = int(port)
        self.ip_addr = self.__init_ip_lookup()
        if peer_id: self.peer_id = peer_id
        else: self.peer_id = '%s:%d' % (self.ip_addr, self.port)

        print "Connect via hachat://" + self.peer_id
        
        self.peers = {} # list of known peers (ip_addr, port, hops)
        self.down = False
        
    def turndown(self):
        self.down = True
        
    def __init_ip_lookup(self):
        """ lookup der eigenen IP-Adresse"""
        # kennt wer einen schoeneren Weg?
        s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        s.connect( ( "www.google.com", 80 ) )
        self.ip_addr = s.getsockname()[0]
        s.close()
        return self.ip_addr
        
    def add_to_peerList(self, ip_addr, port, peer_id=None, hops=0):
        """Hinzufuegen eines Peers zu der Liste der bekannten"""
       
        if not peer_id: peer_id =  '%s:%d' % (ip_addr, port)
       
        if peer_id not in self.peers:
            self.peers[peer_id] = (ip_addr, int(port), int(hops))
            return True
        else: return False
   
    def remove_peer(self, peer_id):
        """loeschen eines Peers von der Liste"""
        if peer_id not in self.peers:
            return False
        else: 
            del self.peers[peer_id]
            return True
    
    def peer_connection(self, peer_socket):
        """hier soll die neue verbindung zu einem neuen Peer verwaltet werden. """
        
        #bisher nur beispielhafte funktionalitaet
        peer_addr, peer_port = peer_socket.getpeername()

        peer_socket.send("Thanks for connecting, " + peer_addr + ":" + str(peer_port))

        if not self.add_to_peerList(peer_addr, peer_port):
            peer_socket.close()
        else: self.add_to_peerList(peer_addr, peer_port)
        
        
    
    def create_incoming_socket(self, port):
        """erstellt einen Socket welcher auf einem bestimmten Port lauscht"""
        s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        s.bind( ( '', port ) )
        s.listen(10)
        return s
    
    def listen_to_socket(self):
        """lauscht nach eingehenden connections und spereriert diese in eigene Threads"""
       
        in_socket = self.create_incoming_socket(self.port)
        print 'Socket lauscht auf Port %d' % self.port
        
        while not self.down:
            #Accept a connection. Return value (new socket object, address):
            try:
                new_peer_socket, new_peer_ip_addr = in_socket.accept()
                
                #constructor fuer einen neuen thread
                thread = threading.Thread(target=self.peer_connection, args = [new_peer_socket] ) 
                thread.start()
            except:
                print "Stop"
                self.down = True
        
        in_socket.close()  

p = Peer(5000)
p.listen_to_socket()
p.turndown()
    
# Modeline for vim:
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
