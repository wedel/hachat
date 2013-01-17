hachat
======
A peer-to-peer-network, designed for "Peer-to-Peer Systeme", Humboldt-Universität Berlin. 

test
----
You can use hachat.py or test.sh to test the network.

Usage: ./hachat.py [-l Link] [-i IP-Adress] [-p Port] [-n name] [-v verbose] [-T Test-Mode]

A link or your own ip adress is nessesery to start HaChat. The Link must be a hostname:port pair.

You can use test.sh to start 5 clients on localhost. Pass over a time (in sec.) and starting the first three and the last two peers will halt. This way you can test the history-functionality.
Usage: ./test.sh [time in seconds]

Have fun chatting...
