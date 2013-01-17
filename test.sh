#!/bin/sh

# this script will start 5 HaChat Clients for testing purpose

address="127.0.0.1"
port1=5001
port2=5002
if echo $1 | egrep -q '^[0-9]+$'; then
    # $1 is a number
    sec=$1
    echo "HaChat0.1: Will start 5 Peers for localhost..."
    echo "We will wait for $1 second(s) between starting first 3 and last 2 peers"
    echo "have fun chatting..."
else
   sec=0
fi


(python hachat.py -i $address -p $port1 -n Anna -v >> Anna.log 2>&1 &)
(python hachat.py -l ${address}:$port1 -n Arthur -v >> Arthur.log 2>&1 &)
(python hachat.py -i $address -p $port2 -l localhost:$port1 -n Paul -v >> Paul.log 2>&1 &)
sleep $sec
(python hachat.py -l ${address}:$port2 -n Pauline -v >> Pauline.log 2>&1 &)
(python hachat.py -l ${address}:$port2 -n Zora -v >> Zora.log 2>&1 &)

