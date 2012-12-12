#import message
import logging


class meta:     
    '''implements all meta-information exchange for the peers
    like hostList exchange and comparison of the History
     + move the HeloMessage here?
     
     all methods should be called periodically, one after one for every host 
     from hostlist, to stabilize the network.
     Log each request, if not answerd  (after a certain time/after a certain quantum of requests??) 
     erase the Host from HostList. -> eraseHosts()
     
     ex:  30sec after starting Peer Host1 - peerList()
          1min after starting Peer Host2 - historyCheck()
          1:30m after starting Peer Host3 - peerList()
          2min after starting Peer Host4 - historyCheck()
          and so forth in different order...'''
    
    def __init__(self):
        '''implements above described periodical calling of methods'''
        pass
    
    def historyCheck(self):
        '''implements the History Checking-function:
        
        1st: Request a List of the last 10 Msg-hashes of a the neighbour
            log this -> requestHistory()
        2nd: neighbour sends a List of the last 10 Msg-hashes if requested
            -> pushHistory()
        3rd: Check if given all(!) Hashes are in the HashHistory and
            if not, request the missing Msgs 
            -> requestMissingMsgs()'''
        pass
    
    def peerList(self):
        '''implements the peer-exchange:
        
        1st: Check the HostList of the Peer, if this contains less then 5 Hosts
            request a subset (containing (5 - len(HostList) + 2) Hosts or so) of a
            neighbours HostList, log request.
            -> requestPeers()
        2nd: If incoming Request, choose a random subset (quality as described above)
            of own HostList and send it back as a List.
            -> pushPeers()
        3rd: compare the List of incoming Hosts with own HostList and 
            add not-containing Hosts.
            -> CompAndAddHosts()'''
        pass
        
    def eraseHosts(self, host):
        '''Check if requests for a certain Host is answered and if not erase Host from HostList'''
        pass
    
    
    def requestHistroy(self, neighbour, quant=10):
        '''asks neighbour for its Hash-History and log request'''
        pass            
        
        
    def pushHistory(self,addr,quant=10):
        '''if neighbour requested History (latest quant of msgs)
        this will give it to them...'''
        (hostIP, hostPort) = addr
        addrPair = hostIP + ':' + str(hostPort)
        host = self.hosts[addrPair]
        
        hashList = self.history.giveLatestHashes(quant) #needs to be implemented!!!
        host.addToMsgQueue(hashList) # needs to be implemented!!!
        logging.debug("Will send History to " + addrPair)
        
    def requestMissingMsgs(self, msgHashList):
        pass
  
    def requestPeers(self, quant=5):
        '''request Peers from neighbours'''
        pass
    
    def pushPeers(self, quant=5):
        '''give Peers from hostList to a neighbour'''
        pass
    
    def CompAndAddHosts(self):
        pass
