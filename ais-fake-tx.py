#!/usr/bin/env python3
'''
Wait for a connection then
Read lines from ais-fake.txt and write them to HOST/PORT.
Should be readable with OpenCPN and ais-fake-rx.py

In a shell
  python3 ./ais-fake-tx.py
'''

import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    print('Connected by', addr)
    with conn:
       with open("ais-fake.txt","r") as f:
             for ln in f:
                print(ln[0:-1])  # drop '\n'
                conn.sendall(ln[0:-1].encode())

s.close()
