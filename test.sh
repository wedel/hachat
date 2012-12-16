#!/bin/sh

# this script will start 4 HaChat Clients for testing purpose

port1=5001
port2=5002

(python hachat.py -p $port1 -n Anna -v >> Anna.log 2>&1 &)
(python hachat.py -l localhost:$Port1 -n Arthur -v >> Arthur.log 2>&1 &)
(python hachat.py -p $port2 -l localhost:$port1 -n Paul -v >> Paul.log 2>&1 &)
(python hachat.py -l localhost:$port2 -n Pauline -v >> Pauline.log 2>&1 &)
(python hachat.py -l localhost:$port2 -n Zora -v >> Zora.log 2>&1 &)

