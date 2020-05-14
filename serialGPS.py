#!/usr/bin/env python3

'''
Parse GPS NMEA 0183 direct from serial (not gpsd). 

To make serial available this needs    systemctl stop  gpsd
and 
pip3 install Pyserial
'''
# see
#  https://www.gpsinformation.org/dale/nmea.htm for NMEA sentence info.
#  https://www.u-blox.com/sites/default/files/products/documents/u-blox6_ReceiverDescrProtSpec_%28GPS.G6-SW-10018%29_Public.pdf
#    for ublox 6 details including controls

import sys
from time import sleep, strftime
import serial  # from Pyserial
import threading, signal

import logging

#in decreasing order CRITICAL, ERROR, WARNING. INFO, DEBUG
# level logs everything higher. NOTSET looks to parent levels

# basicConfig can only be set once in a python session. Additional calls ignored.
#logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s')
#logging.basicConfig(level=logging.INFO, format='(%(threadName)-9s) %(message)s')
logging.info('message level info.')
#logging.debug('message level debug.')

global lat, lon, tm, date

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
      # speed[7] in knots, true course [8]
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


###################################################################

class serialGPS(threading.Thread):
   """
   Threading object used to read serial GPS and maintain current information.
   The information is (not yet) broadcast. (possibly should reponds to queries like gpsd.)
   In testing the information is periodically printed.
   
   This process keeps most recent lat, lon, dateTtime, ...
   (A timeout should set values to null if they get too old, to avoid illusion
   that GPS is working.)
   """
   
   def __init__(self, shutdown, port = "/dev/serial0"):
      threading.Thread.__init__(self)
      
      self.name='serialGPS'
      self.shutdown = shutdown
      self.ser = serial.Serial(port, baudrate = 9600, timeout = 0.5)
      
      #Store date for use with NMEA sentences that do not return it.
      global lat, lon, tm, date
      date = None 
      lat  = None 
      lon  = None 
      tm   = None 
            
      #self.sleepInterval = 0.1 # between reading GPS, may not be needed
      #logging.debug('serialGPS initialized.')
   
   def run(self):
      global lat, lon, tm, date
      logging.info('serialGPS started')
 
      while not self.shutdown.is_set():   
          # Wrapped in try for case when read fails.
          try :
              rx = self.ser.readline().decode()
              p = parseNMEA0183(rx)
              
              #for now using globals lat, lon, tm, date
              if p is not None :
                 lat = p[0]
                 lon = p[1]
                 tm  = p[2]
                 if p[3] is not None : 
                    dt = p[3].split('/')
                    dt.reverse()
                    date = '20' + '-'.join(dt)
          except :
             #logging.debug('ser.readline exception.')
             pass
          
          #sleep(self.sleepInterval)
      
      logging.info('exiting serialGPS thread.')


###################################################################

if __name__ == '__main__':

   global lat, lon, tm, date
   
   logging.info('main thread starting. ' + strftime('%Y-%m-%d %H:%M:%S %Z'))
   shutdown = threading.Event()

   serialGPS(shutdown).start()

   logging.debug(threading.enumerate())
 
   def shutdownHandler(signum, frame):
       logging.info('main thread setting shutdown signal.')
       shutdown.set()  # to exit threads
       sleep(5)
       logging.info('main thread exit.' + strftime('%Y-%m-%d %H:%M:%S %Z')+ '\n')
       logging.debug('threads still running:')
       logging.debug(threading.enumerate())
       sys.exit()

   # ^C works if process is not deamonized with &
   signal.signal(signal.SIGINT,  shutdownHandler) # ^C, kill -2
   signal.signal(signal.SIGTERM, shutdownHandler) # kill -15 (default)

   while True:               # Ctrl+c or kill to exit
      #x = hn + ' ' + str(p.lat) + ' ' + str(p.lon) + ' ' + str(p.tm)
      #x = str(p[0]) + ' ' + str(p[1])  + ' ' + str(date) + 'T' + str(p[2])
      x = str(lat) + ' ' + str(lon)  + ' ' + str(date) + 'T' + str(tm)
      print( x )
      sleep(1)
