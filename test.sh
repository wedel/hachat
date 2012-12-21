#!/bin/sh

# this script will start 5 HaChat Clients for testing purpose

address="127.0.0.1"
port1=5001
port2=5002

(python hachat.py -i $address -p $port1 -n Anna -v >> Anna.log 2>&1 &)
(python hachat.py -l ${address}:$port1 -n Arthur -v >> Arthur.log 2>&1 &)
(python hachat.py -i $address -p $port2 -l localhost:$port1 -n Paul -v >> Paul.log 2>&1 &)
(python hachat.py -l ${address}:$port2 -n Pauline -v >> Pauline.log 2>&1 &)
(python hachat.py -l ${address}:$port2 -n Zora -v >> Zora.log 2>&1 &)

