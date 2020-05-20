#!/usr/bin/env python3
'''
This is a tool for debugging the system setups.
See instructions in ais-fake-tx-udp.py.

The receiver and the sender should be on the same subnet for this setup.
IFACE is the local system's IP address (the system running this program)
MCAST_GROUPS and BIND_GROUP take the place of of a host address for the
system broadcasting information.
See
https://stackoverflow.com/questions/10692956/what-does-it-mean-to-bind-a-multicast-udp-socket
regarding bind for multicast (vs for TCP).
'''

import socket
import struct

#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#s.connect(("8.8.8.8", 80))
#IFACE = s.getsockname()[0]
#s.close()
#or
IFACE = socket.gethostbyname(socket.gethostname())
#IFACE = '127.0.0.1'  

PORT = 65433        # The port used by ...
MCAST_GROUPS = ['224.1.1.4']

BIND_GROUP = MCAST_GROUPS[0]  # '224.1.1.4'

#BIND_GROUP = '0.0.0.0'
# bind to '' or 0.0.0.0  is all multicast addresses of the interface
# Should bind to one of the groups joined in mcast_groups.
# Also possible to bind to groups added by some other programs.

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Allow reuse of socket (to allow other programs to bind to the same ip/port).
# It is suggested to set this before bind().
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sock.bind((BIND_GROUP, PORT))

for group in MCAST_GROUPS:
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, 
     struct.pack( '4s4s', socket.inet_aton(group), socket.inet_aton(IFACE)))

try:
   while True:
      print(sock.recv(1024)) #10240
except KeyboardInterrupt:
    print("Interrupt. ")
finally:
    sock.close()
    print("Shut down.\n")

