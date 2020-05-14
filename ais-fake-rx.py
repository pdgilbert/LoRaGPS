#!/usr/bin/env python3
'''
For simple test of ais-fake-tx.py. Connect and receive data.

In one shell
  python3 ./ais-fake-tx.py
in another
  python3 ./ais-fake-rx.py
'''

import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        #  (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
   s.connect((HOST, PORT))
   while True:
       data = s.recv(1024)  # not sure about 1024, grabbing too much?
       if not data:
           break
       #print(repr(data))   # repr puts quotes around value 
       #print(data)   
       print(data.decode())   
       print('\n')   

s.close()
