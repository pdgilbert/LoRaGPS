#!/usr/bin/env python3
'''
This is a tool for debugging the system setups.
Send (UDP) to multicast group(s) using port as specified below in the code.
(Note that the multicast group(s) take the place of a host IP address.)
Two AIS messages are sent with 10s between.

  python3  ./ais-fake-rx-udp.py
in a different shell, possibly a different computer
  python3  ./ais-fake-tx-udp.py

To view in OpenCPN  tools>connections add UDP network connection using
the multicast group (eg '224.1.1.4') as the network address and the port
as specified in the code below. Then 'enable' and 'apply'.
Start OpenCPN before running this script as UDP broadcasts are lost if
they occur before OpenCPN is listening.
(If this host's IP address is used for the network address in the OpenCPN 
connection OpenCPN seems to get the messages as long as ./ais-fake-rx-udp.py
is also running, but not otherwise. This may be because ./ais-fake-rx-udp.py
sets the socket to allow reuse.)

The receiver and the sender should be on the same subnet for this setup.

See 
 https://stackoverflow.com/questions/603852/how-do-you-udp-multicast-in-python
for fancy example.
'''

import socket
from time import sleep
from AIS import AIS1_encode

MCAST_GROUP = '224.1.1.4'
PORT  = 65433

TTL = 20
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)

#with open("ais-fake.txt","r") as f:
#   for ln in f:
#      print(ln[0:-1])  # drop '\n'
#      sleep(5)
#      sock.sendto(ln[0:-1].encode(), (MCAST_GROUP, PORT))

#ais = '!AIVDM,1,1,,A,133sVg0rh0rAjP02Qn4@?wvN2000,0*7D' #west of Panama

# Portsmouth Olympic Harbour, Kingston, Canada
ais = AIS1_encode(
   mmsi=123456789, navStat=0, ROT=128, SOG=1023, PosAcc=0, 
   lon= -76.514790, lat= 44.215940, COG=360, HDG=511, tm=15, mvInd=0,  
   spare=0, RAIM=False, RadStat=0, returnk=False)

#ais = '!AIVDM,1,1,,A,11mg=5@P?wJQgSdIC?7>4?vN0000,0*38'

sock.sendto(ais.encode(), (MCAST_GROUP, PORT))

sleep(10)

ais = AIS1_encode(
   mmsi=987654321, navStat=0, ROT=128, SOG=1023, PosAcc=0, 
   lon= -76.514775, lat= 44.215972, COG=360, HDG=511, tm=15, mvInd=0,  
   spare=0, RAIM=False, RadStat=0, returnk=False)

#ais = '!AIVDM,1,1,,A,1>eq`d@P?wJQgSvIC?;v4?vN0000,0*73'

sock.sendto(ais.encode(), (MCAST_GROUP, PORT))

sock.close()
