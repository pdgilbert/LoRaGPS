#!/usr/bin/env python3

'''
Read GPS using gpsd and send GPS location via LoRa. This needs gpsd running 
on the system and accepting connection on  "127.0.0.1", port=2947
'''

# See examples in  pySX127x.

import sys
from time import sleep
from SX127x.LoRa import *
#from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD

import socket
import gpsd

quiet=False

ReportInterval = 1.0  # seconds

# See Vcourse/gpsPos.py for a better example of gpsCon
gpsCon = gpsd.connect(host="127.0.0.1", port=2947) 

hn = socket.gethostname()

BOARD.setup()

#parser = LoRaArgumentParser("A simple LoRa beacon")
#parser.add_argument('--single', '-S', dest='single', default=False, action="store_true", help="Single transmission")
#parser.add_argument('--wait', '-w', dest='wait', default=1, action="store", type=float, help="Waiting time between transmissions (default is 0s)")


class LoRaGPStx(LoRa):
    '''
    verbose True/False  is used by pySX127x to print extra information (mode setting).
    quiet   True/False  is used in class  LoRaGPSrx to turn off/on printing.
    '''
    
    def __init__(self, verbose=False, quiet=False):
        super(LoRaGPStx, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([1,0,0,0,0,0])
        self.quiet=quiet
        self.set_freq(915)
    
    def on_rx_done(self):
        #print(self.get_irq_flags())
        print(map(hex, self.read_payload(nocheck=True)))
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
    
    def on_tx_done(self):
        global args
        self.set_mode(MODE.STDBY)
        self.clear_irq_flags(TxDone=1)
        sys.stdout.flush()
        if not self.quiet : sys.stdout.write(".")
        sleep(ReportInterval)
        
        try:
           p = gpsd.get_current()
        except:
           try:
              # logging.debug('getGPS attempting reconnect.' )
              gpsd.connect(host=self.host, port=self.port) # re-connect
              p = gpsd.get_current()
           except:
              return(None)
        
        x = hn + ' ' + str(p.lat) + ' ' + str(p.lon )+ ' ' + str(p.time)
        #print([ord(ch) for ch in x])
        self.write_payload([ord(ch) for ch in x])
        self.set_mode(MODE.TX)
    
    def on_cad_done(self):
        print("\non_CadDone")
        print(self.get_irq_flags())
    
    def on_rx_timeout(self):
        print("\non_RxTimeout")
        print(self.get_irq_flags())
    
    def on_valid_header(self):
        print("\non_ValidHeader")
        print(self.get_irq_flags())
    
    def on_payload_crc_error(self):
        print("\non_PayloadCrcError")
        print(self.get_irq_flags())
    
    def on_fhss_change_channel(self):
        print("\non_FhssChangeChannel")
        print(self.get_irq_flags())
    
    def start(self):
        #global args
        sys.stdout.write("\rstart")
        x='Started transmit from ' + hn + '.'
        #print( [ord(ch) for ch in x])
        self.write_payload([ord(ch) for ch in x])
        self.set_mode(MODE.TX)
        while True:
            sleep(1)

lora = LoRaGPStx(verbose=False)
#args = parser.parse_args(lora)


#  Medium Range  Defaults after init are 434.0MHz, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on 13 dBm
#     Slow+long range  Bw = 125 kHz, Cr = 4/8, Sf = 4096chips/symbol, CRC on. 13 dBm

#lora.set_pa_config(pa_select=1)
lora.set_pa_config(pa_select=1, max_power=21, output_power=15)
#lora.set_pa_config(max_power=0x04, output_power=0x0F)
#lora.set_pa_config(max_power=0x04, output_power=0b01000000)

lora.set_freq(915.0)  
lora.set_bw(BW.BW125)
lora.set_coding_rate(CODING_RATE.CR4_8)
#lora.set_agc_auto_on(True)
# setting spreading_factor(12)  reports 4096 chips/symb  but does not work yet
# not setting (comment out)     reports 128 chips/symb  and works
# lora.set_spreading_factor(12)
lora.set_rx_crc(False)   #True
#lora.set_pa_ramp(PA_RAMP.RAMP_50_us)
#lora.set_lna_gain(GAIN.G1)
#lora.set_lna_gain(GAIN.NOT_USED)
#lora.set_implicit_header_mode(False)
lora.set_low_data_rate_optim(False)  #True


if not quiet : print(lora)
#assert(lora.get_lna()['lna_gain'] == GAIN.NOT_USED)
assert(lora.get_agc_auto_on() == 1)
assert(lora.get_freq() == 915)

print("Report interval %f s" % ReportInterval)

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
    if not quiet :
       sys.stdout.flush()
       #print(lora)
       #sys.stdout.flush()
       sys.stderr.write("Shut down.\n")
