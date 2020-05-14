#!/usr/bin/env python3

'''
Parse GPS NMEA 0183 direct from serial (not gpsd). 

To make serial available this needs    systemctl stop  gpsd
and 
pip3 install Pyserial
'''
# see https://www.gpsinformation.org/dale/nmea.htm for NMEA sentence info.

#import sys
#from time import sleep
import serial

port = "/dev/serial0"
ser = serial.Serial(port, baudrate = 9600, timeout = 0.5)


def parseNMEA0183(rxx):
   
   #rxx = '$GPGGA,181119.00,4523.74678,N,07540.61545,W,1,08,1.13,62.8,M,-34.2,M,,*5F'
   #rxx = '$GPRMC,181124.00,A,4523.74681,N,07540.61529,W,0.035,,030520,,,A*6C'
   #rxx = '$GPGLL,4523.74678,N,07540.61550,W,181118.00,A,A*70'
   
   rxx = rxx.split(',')
   # degree, minutes DDDMM.MMMMM to decimal degrees
   
   if rxx[0] == '$GPGGA' :
      tm = rxx[1][0:2] + ":" + rxx[1][2:4] + ":" + rxx[1][4:] + "Z"
      lat = (-1, 1)[ rxx[3] is 'N'] * (float(rxx[2][0:2]) + float(rxx[2][2:])/60 )
      lon = (-1, 1)[ rxx[5] is 'E'] * (float(rxx[4][0:3]) + float(rxx[4][3:])/60 )
      date = None
   elif rxx[0] == '$GPRMC' :
      tm = rxx[1][0:2] + ":" + rxx[1][2:4] + ":" + rxx[1][4:] + "Z"
      lat = (-1, 1)[ rxx[4] is 'N'] * (float(rxx[3][0:2]) + float(rxx[3][2:])/60 )
      lon = (-1, 1)[ rxx[6] is 'E'] * (float(rxx[5][0:3]) + float(rxx[5][3:])/60 )   
      # speed[7], true course [8]
      date = rxx[9][0:2] + "/" + rxx[9][2:4] + "/" +rxx[9][4:6]
   elif rxx[0] == '$GPGLL' :
      tm = rxx[5][0:2] + ":" + rxx[5][2:4] + ":" + rxx[5][4:] + "Z"
      lat = (-1, 1)[ rxx[2] is 'N'] * (float(rxx[1][0:2]) + float(rxx[1][2:])/60 )
      lon = (-1, 1)[ rxx[4] is 'E'] * (float(rxx[3][0:3]) + float(rxx[3][3:])/60 )
      date = None
   else:
      tm = None
      lat = float('NaN')
      lon = float('NaN')
      date = None
  
   if tm is not None :
      p = (lat, lon, tm, date)
   else :
      p = None
   
   return(p)


# This should be a process that keeps most recent lat, lon, dateTtime, with timeout
# to null values, and reponds to queries like gpsd.

#Store date for use with NMEA sentences that do not return it.
date = None 
while True:
   rx = ser.readline().decode()
   p = parseNMEA0183(rx)
   if p is not None :
      if p[3] is not None : 
         date = p[3].split('/')
         date.reverse()
         date = '20' + '-'.join(date)
      #x = hn + ' ' + str(p.lat) + ' ' + str(p.lon) + ' ' + str(p.tm)
      x = str(p[0]) + ' ' + str(p[1])  + ' ' + str(date) + 'T' + str(p[2])
      print( x )
   #sleep(1)
