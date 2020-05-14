#!/usr/bin/env python3

""" Receive GPS locations via LoRa. """

# See examples in  pySX127x.

from time import sleep
from SX127x.LoRa import *
from SX127x.board_config import BOARD

quiet=False

BOARD.setup()

# look at this and examples in  pySX127x if shell arguments are considered.
#from SX127x.LoRaArgumentParser import LoRaArgumentParser
#parser = LoRaArgumentParser("Continous LoRa receiver.")


class LoRaGPSrx(LoRa):
    '''
    verbose True/False  is used by pySX127x to print extra information (mode setting).
    quiet   True/False  is used in class  LoRaGPSrx to turn off/on printing.
    '''
    def __init__(self, verbose=False, quiet=False):
        super(LoRaGPSrx, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.set_freq(915)
        self.quiet=quiet
        self.last_tm = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    def on_rx_done(self):
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
           print(rx + ' dt=%f s.' % dt)
           print(bt + f'{lat:13.7f}' + f'{lon:13.7f}' + \
                      f'{tm[0]:5.0f}' + '-' + f'{tm[1]:2.0f}' + '-' + f'{tm[2]:2.0f}' + \
                      f'{tm[3]:2.0f}' + ':' + f'{tm[4]:2.0f}' + ':' + f'{tm[5]:2.0f}' + 'Z'\
                       + ' dt=%f s.' % dt)

      
        self.last_tm = tm                 # really need this for each bt
        #print( [ord(ch) for ch in payload])
        #print(chr(payload[0]))
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
    
    def on_tx_done(self):
        print("\nTxDone")
        print(self.get_irq_flags())
    
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
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        if not self.quiet :  print("\nstarted listening.")
        while True:
            sleep(.5)
            #rssi_value = self.get_rssi_value()
            #status = self.get_modem_status()
            #sys.stdout.flush()
            #sys.stdout.write("\r%d %d %d" % (rssi_value, status['rx_ongoing'], status['modem_clear']))


lora = LoRaGPSrx(verbose=False, quiet=quiet)
#args = parser.parse_args(lora)

lora.set_mode(MODE.STDBY)
#lora.set_pa_ramp(PA_RAMP.RAMP_50_us)
#lora.set_agc_auto_on(True)

#  Medium Range  Defaults after init are 434.0MHz, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on 13 dBm
#     Slow+long range  Bw = 125 kHz, Cr = 4/8, Sf = 4096chips/symbol, CRC on. 13 dBm

lora.set_pa_config(pa_select=1, max_power=21, output_power=15)
#lora.set_pa_config(pa_select=1)

lora.set_freq(915.0)  
lora.set_bw(BW.BW125)
lora.set_coding_rate(CODING_RATE.CR4_5)   #.CR4_8
# setting spreading_factor(12)  reports 4096 chips/symb  but does not work yet
# not setting (comment out)     reports 128 chips/symb  and works
#lora.set_spreading_factor(12)
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
        sys.stderr.write("Shut down.\n")

