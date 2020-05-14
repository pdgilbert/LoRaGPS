# LoRaGPS
Transmit GPS and other information with LoRa

The code is in an initial development stage, pre-alpha. More information will
eventually appear here. For the time being the following content is a rough
status and "to do" list intended mainly to help me keep track of the 
different pieces.

The LoRa tx and rx use SX127x from pySX127x.

tx-LoRaGPS.py   transmit message over LoRa (not LoRaWAN).
                Status: working (on Raspberry Pi Zero W) but in active
                        development and re-org.

rx-LoRaGPS.py   receive message over LoRa.
                Status: working (on Raspberry Pi 3Bv1.2) but in active
                        development and re-org.

lib/AIS.py      Not real AIS! Utilities for converting LoRa broadcast of GPS   
                information into AIS messages to feed into OpenCPN. 
                Status: working but possible precision problem with lon and lat.

ais-fake-tx.py  Wait for a TCP connection then read lines from ais-fake.txt and
                write them to HOST/PORT. For testing sending of data to OpenCPN.
                Status: working but could be threaded.

ais-fake-rx.py  For testing ais-fake-tx.py.
                Status: working.

ais-fake.txt    Text file with sample NMEA data for ais-fake-tx.py testing.
