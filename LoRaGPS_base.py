#!/usr/bin/env python3

"""
Receive GPS locations via LoRa, convert to AIS and multicast on network(UDP).
Record tracks if set. (Beware space requirement.)

"""

# See also examples in  pySX127x.

import argparse
from time import sleep
from SX127x.LoRa import *
from SX127x.board_config import BOARD

from AIS import AIS1_encode

import os
import socket

parser = argparse.ArgumentParser(description= 
           'Read GPS using serial (not gpsd) and send GPS location via LoRa.')

parser.add_argument('--quiet', type=bool, default=False,
                    help='if True suppress local printing. (default: False)')

# following are settings passed to LoRa

parser.add_argument('--freq', type=int, default=915,
          help='LoRa frequency. 169, 315, 433, 868 Mhz. (default: 915)')

parser.add_argument('--bw', type=int, default=125,
          help='LoRa frequency. 0-9 or 125kHz, 250kHz and 500kHz Mhz. (default: )')

parser.add_argument('--Cr', type=str, default='4_8',
          help='LoRa coding rate. "4_5", "4_6", "4_7", "4_8". (default: "4_8")')

parser.add_argument('--Sf', type=int, default=7,
          help='LoRa spreading factor. 7-12, 7-10 in NA. (default: 7)')


args = parser.parse_args()


MCAST_GROUP = '224.1.1.4'
PORT  = 65433

TTL = 20

quiet=args.quiet

BOARD.setup()

# look at this and examples in  pySX127x if shell arguments are considered.
#from SX127x.LoRaArgumentParser import LoRaArgumentParser
#parser = LoRaArgumentParser("Continous LoRa receiver.")

mmsis = {"mqtt1": 316456789 , "BT-1" : 338654321}   #316 is Canada; 338 is USA

# see https://en.wikipedia.org/wiki/Maritime_Mobile_Service_Identity
# eventually
#with open('MMSIs_table.json', 'r') as f:  mmsis = json.load(f)
#bt   = mmsis["BT_ID"] 
#mmsi = mmsis["cmmsi"] 
#ct = mmsis["country"] 

#track = ['BT-1', 'mqtt1']
track = ['BT-1']

if not os.path.exists('TRACKS') :  os.makedirs('TRACKS')

track_file_handles = {}
for b in track:
   track_file_handles.update({b : open('TRACKS/' + b + '.txt', 'w')})

class LoRaGPSrx(LoRa):
    '''
      quiet   True/False  is used to turn off/on local printing.
    Arguments passed on to class LoRa from SX127x.LoRa
      freq=915, bw=125, Cr='4_8', Sf=7
      verbose True/False  is used by pySX127x to print extra information (mode setting).
      do_calibration=True, calibration_freq=915
    '''
    def __init__(self, quiet=False,
           freq=915, bw=125, Cr='4_8', Sf=7,
           verbose=False, do_calibration=True, calibration_freq=915):
        
        super(LoRaGPSrx, self).__init__(verbose, do_calibration, calibration_freq)
        
        self.quiet=quiet
        
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        
        self.set_freq(freq)
        
        self.set_bw((BW.BW125, BW.BW250, BW.BW500)[(125, 250, 500).index(bw)])
        
        CR= {"4_5": CODING_RATE.CR4_5, 
             "4_6": CODING_RATE.CR4_6,
             "4_7": CODING_RATE.CR4_7, 
             "4_8": CODING_RATE.CR4_8 }[args.Cr]
        self.set_coding_rate(CR)
        
        self.set_spreading_factor(Sf)
        
        self.last_tm = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    def on_rx_done(self):
        # on interupt read LoRa payload
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)        
        rx = bytes(payload).decode("utf-8",'ignore')
        
        try:
           p   = rx.split(' ')
           bt  = p[0]
           lat = float(p[1])
           lon = float(p[2])
           # tm is year, month, day, hr, min, sec  UTC
           tm = p[3].replace('Z', '').replace('T', ':').replace('-', ':').split(':')
           tm = [float(x) for x in tm]  # could use int here
        except:
           bt  = None
           lat = None
           lon = None
           tm = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        # dt is just to identify time gaps when testing
        if bt is not None:
           dt = 3600 * (tm[3] - self.last_tm[3]) + 60 * (tm[4] - self.last_tm[4]) + (tm[5] - self.last_tm[5])
           #print(rx + ' dt=%f s.' % dt)
           # f-strings starting in Python 3.6
	   #print(bt + f'{lat:13.7f}' + f'{lon:13.7f}' + \
           #           f'{tm[0]:5.0f}' + '-' + f'{tm[1]:2.0f}' + '-' + f'{tm[2]:2.0f}' + \
           #           f'{tm[3]:2.0f}' + ':' + f'{tm[4]:2.0f}' + ':' + f'{tm[5]:2.0f}' + 'Z'\
           #            + ' dt=%f s.' % dt)
           
           record = '%s %f %f %i-%i-%i %i:%i:%rZ  dt=%r s' % \
              (bt, lat, lon, tm[0], tm[1], tm[2], tm[3], tm[4], tm[5],  dt)
           
           if not self.quiet : print(record)
           
           if bt in track : ok = track_file_handles[bt].write(record + "\n")
           
           ais = AIS1_encode(
              mmsi=mmsis[bt], navStat=0, ROT=128, SOG=1023, PosAcc=0, 
              lon= lon, lat= lat, COG=360, HDG=511, tm=int(tm[5]), mvInd=0,  
              spare=0, RAIM=False, RadStat=0, returnk=False)
           
           
           sock.sendto(ais.encode(), (MCAST_GROUP, PORT))
   
        self.last_tm = tm                 # really need this for each bt
        #print( [ord(ch) for ch in payload])
        #print(chr(payload[0]))
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
    
    # These are marked as overridable functions in LoRa class definition and the
    #  following are give as example overrides:
    #def on_tx_done(self):
    #    print("\nTxDone")
    #    print(self.get_irq_flags())
    #
    #def on_cad_done(self):
    #    print("\non_CadDone")
    #    print(self.get_irq_flags())
    #
    #def on_rx_timeout(self):
    #    print("\non_RxTimeout")
    #    print(self.get_irq_flags())
    #
    #def on_valid_header(self):
    #    print("\non_ValidHeader")
    #    print(self.get_irq_flags())
    #
    #def on_payload_crc_error(self):
    #    print("\non_PayloadCrcError")
    #    print(self.get_irq_flags())
    #
    #def on_fhss_change_channel(self):
    #    print("\non_FhssChangeChannel")
    #    print(self.get_irq_flags())
    
    def start(self):
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        if not self.quiet :  print("\nstarted listening.")
        while True:
            sleep(.5)
            #rssi_value = self.get_rssi_value()
            #status = self.get_modem_status()
            #sys.stdout.flush()
            #sys.stdout.write("\r%d %d %d" % (rssi_value, status['rx_ongoing'], status['modem_clear']))


lora = LoRaGPSrx(quiet=args.quiet, 
             freq=args.freq, bw=args.bw, Cr=args.Cr, Sf=args.Sf, 
             verbose=False)

lora.set_mode(MODE.STDBY)
#lora.set_pa_ramp(PA_RAMP.RAMP_50_us)
#lora.set_agc_auto_on(True)

# SX127x class LoRa has (Medium Range  Defaults after init):
#  Medium Range     434.0MHz, Bw = 125 kHz, Cr = 4/5, Sf =  128chips/symbol, CRC on 13 dBm
#  Slow+long range            Bw = 125 kHz, Cr = 4/8, Sf = 4096chips/symbol, CRC on 13 dBm

# North America requires 915MHz, Sf 7-10 == 128 - 1024 chips/symbol == 2**7 - 2**10
# This code (class LoRaGPSrx) SHOULD sets defaults 
# 915.0MHz, Bw = 125 kHz, Cr = 4/5, Sf = 10 == 1024 chips/symbol, CRC on 13 dBm

lora.set_pa_config(pa_select=1, max_power=21, output_power=15)
#lora.set_pa_config(pa_select=1)

lora.set_freq(915.0)  
lora.set_bw(BW.BW125)
lora.set_coding_rate(CODING_RATE.CR4_5)   #.CR4_8
#lora.set_spreading_factor(10)  #1024 chips/symbol
lora.set_rx_crc(False)   #True
#lora.set_lna_gain(GAIN.G1)
#lora.set_implicit_header_mode(False)
lora.set_low_data_rate_optim(False)  #True
#lora.set_pa_ramp(PA_RAMP.RAMP_50_us)
#lora.set_agc_auto_on(True)

#lora.set_pa_config(pa_select=1)

if not quiet :  print(lora)
assert(lora.get_agc_auto_on() == 1)
assert(lora.get_freq() == 915)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)
print('network (UDP) multicast group to %s:%i' % (MCAST_GROUP, PORT))

try:
    lora.start()
except KeyboardInterrupt:
    if not quiet :
       sys.stdout.flush()
       print("")
       sys.stderr.write("Interrupt. ")
finally:
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()
    sock.close()
    for f in track_file_handles.values():
        f.close()
    if not quiet :
        sys.stdout.flush()
        sys.stderr.write("Shut down.\n")

