#!/usr/bin/env python3

'''
Read GPS using serial (not gpsd) and send GPS location via LoRa. 
This needs gpsd NOT running (it blocks serial). 
   sudo systemctl stop  gpsd
   sudo systemctl disable  gpsd

Will need to detach from shell if the sensor system is going out of wifi range:
   nohup  [python3]  LoRaGPS_sensor.py --quiet=True  report=15.0 &
'''
# see
#  https://www.gpsinformation.org/dale/nmea.htm for NMEA sentence info.
#  https://www.u-blox.com/sites/default/files/products/documents/u-blox6_ReceiverDescrProtSpec_%28GPS.G6-SW-10018%29_Public.pdf
#    for ublox 6 details including controls

# See examples in  pySX127x  for more LoRa info.

import argparse
import sys
from socket import gethostname
from time import sleep, strftime

from SX127x.LoRa import *
from SX127x.board_config import BOARD

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

parser = argparse.ArgumentParser(description= 
           'Read GPS using serial (not gpsd) and send GPS location via LoRa.')

parser.add_argument('--report', type=float, default=15.0,
                    help='Reporting interval in seconds. (default: 15.0)')

parser.add_argument('--quiet', type=bool, default=False,
                    help='if True suppress local printing. (default: False)')

# following are settings passed to LoRa

parser.add_argument('--freq', type=int, default=915,
          help='LoRa frequency. 169, 315, 433, 868, 915 Mhz. (default: 915)')

parser.add_argument('--bw', type=int, default=125,
          help='LoRa frequency. 0-9 or 125kHz, 250kHz and 500kHz Mhz. (default: )')

parser.add_argument('--Cr', type=str, default='4_8',
          help='LoRa coding rate. "4_5", "4_6", "4_7", "4_8". (default: "4_8")')

parser.add_argument('--Sf', type=int, default=7,
          help='LoRa spreading factor. 7-12, 7-10 in NA. (default: 7)')


args = parser.parse_args()

hn = gethostname()

BOARD.setup()

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

class LoRaGPStx(LoRa):
    '''
      ReportInterval      in seconds controls how often the location report is sent.
      quiet   True/False  is used to turn off/on local printing.
    Arguments passed on to class LoRa from SX127x.LoRa
      freq=915, bw=125, Cr='4_8', Sf=7,
      verbose True/False  is used by pySX127x to print extra information (mode setting).
      do_calibration=True, calibration_freq=915
    '''
    
    def __init__(self, ReportInterval=1.0, quiet=False,
           freq=915, bw=125, Cr='4_8', Sf=7,
           verbose=False, do_calibration=True, calibration_freq=915):
        
        super(LoRaGPStx, self).__init__(verbose, do_calibration, calibration_freq)
        
        self.ReportInterval=ReportInterval
        self.quiet=quiet        
        
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([1,0,0,0,0,0])
                
        #self.set_pa_config(pa_select=1)
        self.set_pa_config(pa_select=1, max_power=21, output_power=15)
        #self.set_pa_config(max_power=0x04, output_power=0x0F)
        #self.set_pa_config(max_power=0x04, output_power=0b01000000)
        
        self.set_freq(freq)  

        self.set_bw((BW.BW125, BW.BW250, BW.BW500)[(125, 250, 500).index(bw)])

        CR= {"4_5": CODING_RATE.CR4_5, 
             "4_6": CODING_RATE.CR4_6,
             "4_7": CODING_RATE.CR4_7, 
             "4_8": CODING_RATE.CR4_8 }[args.Cr]
        self.set_coding_rate(CR)

        self.set_spreading_factor(Sf)

        #self.set_agc_auto_on(True)
        self.set_rx_crc(False)   #True
        #self.set_pa_ramp(PA_RAMP.RAMP_50_us)
        #self.set_lna_gain(GAIN.G1)
        #self.set_lna_gain(GAIN.NOT_USED)
        #self.set_implicit_header_mode(False)
        self.set_low_data_rate_optim(False)  #True
        
    def on_rx_done(self):
        #print(self.get_irq_flags())
        print(map(hex, self.read_payload(nocheck=True)))
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
    
    def on_tx_done(self):
        global lat, lon, tm, date
        self.set_mode(MODE.STDBY)
        self.clear_irq_flags(TxDone=1)
        sleep(self.ReportInterval)
        
        x = hn + ' ' + str(lat) + ' ' + str(lon)  + ' ' + str(date) + 'T' + str(tm)
        if not self.quiet :
           #sys.stdout.flush()
           #if not self.quiet : sys.stdout.write(".")
           print(x)
           #print([ord(ch) for ch in x])
        self.write_payload([ord(ch) for ch in x])
        self.set_mode(MODE.TX)
        
    def start(self):
        #global args
        if not self.quiet : sys.stdout.write("\rstart")
        x='Started transmit from ' + hn + '.'
        #print( [ord(ch) for ch in x])
        self.write_payload([ord(ch) for ch in x])
        self.set_mode(MODE.TX)
        while True:
            sleep(1)

###################################################################
        
###################################################################

if __name__ == '__main__':

   global lat, lon, tm, date
   logging.info('main thread starting. ' + strftime('%Y-%m-%d %H:%M:%S %Z'))

   logging.info('setting LoRa.' )
      
     
   lora = LoRaGPStx(ReportInterval=args.report, quiet=args.quiet, 
             freq=args.freq, bw=args.bw, Cr=args.Cr, Sf=args.Sf, 
             verbose=False)
   
   assert(lora.get_freq() in (169, 315, 433, 868, 915))
   assert(lora.get_freq() == 915)  # in North America
   
   #assert(lora.get_lna()['lna_gain'] == GAIN.NOT_USED)
   #assert(lora.get_agc_auto_on() == 1)

   if not args.quiet :
      print(lora)
      print("Report interval %f s" % args.report)
  
   shutdown = threading.Event()

   logging.info('starting serialGPS.' )
   serialGPS(shutdown).start()

   logging.debug(threading.enumerate())
 
   def shutdownHandler(signum, frame):
       if not args.quiet : sys.stderr.write("Interrupt. Shutting down.\n")
       logging.info('main thread setting shutdown signal.')
       shutdown.set()  # to exit threads
       sleep(2)
       logging.info('main thread exit.' + strftime('%Y-%m-%d %H:%M:%S %Z')+ '\n')
       logging.debug('threads still running:')
       logging.debug(threading.enumerate())
       lora.set_mode(MODE.SLEEP)
       BOARD.teardown()
       if not args.quiet :
          sys.stdout.flush()
          #print(lora)
          #sys.stdout.flush()
          sys.stderr.write("Shut down.\n")
       sys.exit()

   # ^C works if process is not deamonized with &
   signal.signal(signal.SIGINT,  shutdownHandler) # ^C, kill -2
   signal.signal(signal.SIGTERM, shutdownHandler) # kill -15 (default)

   #while True:
   lora.start()    # lora does loop  Ctrl+c or kill to exit
