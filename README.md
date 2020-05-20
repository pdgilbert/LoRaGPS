# LoRaGPS
Transmit GPS and other information with LoRa

##  Contents
- [Summary and Status](#summary-and-status)
- [Hardware Setup Notes](#hardware-setup-notes)
- [sensor system](#sensor-system)
- [base station](#base-station)

##  Summary and Status

The code is in an initial development stage, pre-alpha. More information will
eventually appear here. For the time being the following content is a rough
status and "to do" list intended mainly to help me keep track of the 
different pieces.

The LoRa `tx` and `rx` use `SX127x` from `pySX127x`.

`LoRaGPS_sensor.py` -  transmit message over LoRa (not LoRaWAN).
                       Status: working (on Raspberry Pi Zero W) but in active
                        development and re-org.

`LoRaGPS_base.py` -  receive message over LoRa.
                     Status: working (on Raspberry Pi 3Bv1.2) but in active
                        development and re-org.

`lib/AIS.py`    -  Not real AIS! Utilities for converting LoRa broadcast of GPS   
                information into AIS messages to feed into OpenCPN. 
                Status: working but possible precision problem with lon and lat.

`ais-fake-tx-udp.py` - For testing sending of data to OpenCPN. 
                       Establish UDP multicast group and send some (AIS) messages
                       on thet IFACE/PORT. Status: working.

`ais-fake-rx-udp.py` - For testing UDP multicast from ais-fake-tx-udp.py and
                       LoRaGPS_base.py. Wait for UDP  multicasts and print them .
                       Status: working.

`ais-fake-tx.py`     - Wait for a TCP connection then read lines from ais-fake.txt and 
                       write them to HOST/PORT. For testing sending of data to OpenCPN.
                       Status: working but superceded by UDP version.

`ais-fake-rx.py`     - For testing TCP connection in ais-fake-tx.py.
                       Status: workingbut superceded by UDP version.

`ais-fake.txt`   - Text file with sample AIS data for ais-fake-tx.py testing.


The unit testing for `AIS.py` is run by   `python3 lib/AIS.py`
 
The receiver is run on a Raspberry Pi with LoRa hardware by
```
   python3 LoRaGPS_base.py 
```

The transmitter is run on a Raspberry Pi with LoRa and GPS hardware by
```
 python3 LoRaGPS_sensor.py
```

##  Hardware Setup Notes

Below is a description of the setup as initially being tested. 
Many other options are possible but some aspects of the code will need
adjustment if the hardware is configured differently.

There are two main parts, a "sensor system" and a "base station".
In addition to the processors in each, the sensor system has a GPS and  
a LoRa module which transmits information to the base station. 
The base station has a LoRa module to receive information,
and also needs whatever is necessary to do something with that information. 
Typically that would be a network connection to broadcast it, or a monitor
and software to display the information. In some contexts the sensor 
system might be referred to as the "transmitter" and the base station as 
the "receiver" however, some communication in the opposite direction may
eventually be done.

The eventual configuration envisages a large number of sensor systems
(e.g. a large fleet of small boats) while there would be only one of a 
few base stations. In that configuration the sensor systems would be 
headless and the base station(s) could have monitors or be headless with
a network connection.

In development and for installation both systems will need a monitor or
network access with ssh.

###  sensor system

As of May 2020 the sensor system is a Raspberry Pi Zero W running
Raspian 10 (Buster Lite). 

It has a Ublox Neo-6M GPS on a no name board "GY-GPS6MV2" with VCC, RX, TX, 
and GND solder points. These are connected to Pi pins ... respectively.

|  GPS   |Pi pin| Pi BCM |
|:-------|:-----|:---------|
|  VCC |   1  |  3v3      |
|  GND |   6  | GND   |
|  TX  |   8  | BCM 14   |
|  RX  |  10  | BCM 15   |

It also has a no name LoRa 915 MHz module with solder points connected to
Raspberry Pi header pins as follows.

|  LoRa  |Pi pin| Pi BCM |
|:-------|:-----|:-------|
|  DIO0  |   7  | BCM  4 |
|  DIO1  |  11  | BCM 17 |
|  DIO2  |  12  | BCM 18 |
|  DIO3  |  13  | BCM 27 |
|  REST  |  15  | BCM 22 |
|  VCC   |  17  |  3v3   |
|  MOSI  |  19  | BCM 10 |
|  MISO  |  21  | BCM  9 |
|  SCK   |  23  | BCM 11 |
|  NSS   |  24  | BCM  8 |
|  GND   |  25  |  GND   |

The  LoRa module DIO4, DIO5, and two additions GND solder points are not used.

In places where something other than 915 MHz should be used then a different
module will be needed and be sure to check the settings in the code before
running. 

Follow the normal instructions to download and burn an SD with Raspian.
Set up sshd if you want to run headless. 

The essential additional points are that it needs Python 3, python3-dev, and python modules RPi.GPIO, spidev, Pyserial and pySX127x:

```
  sudo apt install python3-dev python3-pip
  pip3 install RPi.GPIO
  pip3 install spidev 
  pip3 install Pyserial
  sudo apt install git 
  git clone https://github.com/rpsreal/pySX127x # or another source
```

Depending on the install location put something like
```
   export PYTHONPATH=/home/pi/pySX127x/
```
in .bashrc

possibly it will be necessary to
```
  sudo apt autoremove
  sudo apt update
  sudo apt upgrade
```
  
and probably it will be necessary to reboot occasionally above and in the next.
 
Raspberry Pi uses the UART as a serial console, which needs to be turned off
to use the UART for GPS. As root on the Raspberry Pi:
```
  cp /boot/cmdline.txt /boot/cmdline_backup.txt
```

Edit cmdline.txt to remove the serial interface. Delete 
```
   console=serial0,115200 
      (or  ttyAMA0,115200 or ttyS0,115200 )
```

and `/dev/ttyAMA0` is linked to the getty (console) service, so:
```
    sudo systemctl  stop   serial-getty@ttyAMA0.service
    sudo systemctl disable serial-getty@ttyAMA0.service
```

It may also be necessary to edit  /boot/config.txt  and add
  enable_uart=1

It should be possible to comfirm that the GPS is attached and working by
```
  python3
  >>>import serial  # from Pyserial
  >>>ser  = serial.Serial("/dev/serial0", baudrate = 9600, timeout = 0.5)
  >>>ser.readline().decode()
```

The last line should show a string of NMEA data, read from the GPS 
device on the serial port.

The `LoRaGPS_sensor.py` code now reads GPS directly though the serial USART.
An early version used gpsd, which may be more robust with different GPS
devices, and provides some other useful features. It can be a bit trickier 
to set up, but is very stable once working. The main reason for not using
gpsd is that the sensor system may eventually run on bare metal, and direct
read of serial is simpler.

[To use gpsd some small changes in the current code would be needed, 
 and (from old notes)
```
  sudo apt install gpsd gpsd-clients
  pip3  install  gpsd-py3
  #or git clone https://github.com/MartijnBraam/gpsd-py3.git
  and
  systemctl start gpsd
  systemctl enable gpsd
  systemctl status gpsd    # should be  loaded and active
  and check with
  gpsmon /dev/serial0 
  gpsmon 127.0.0.1:2947    # 2947 is default port
```

  may need to edit /etc/default/gpsd to
```
    DEVICES="/dev/serial0"    #serial  or /dev/ttyAMA0
    GPSD_OPTIONS="-n"
```
  Then
```
   systemctl daemon-reload; systemctl reenable gpsd.service
   systemctl restart gpsd
```

  Check running `python3`
```
    import gpsd
    gpsCon = gpsd.connect(host="127.0.0.1", port=2947) 
    z = gpsd.get_current() 
    z.lat
    z.lon
    z.time
```
]

Beware that there seems to be conflict between gpsd and serial access to the GPS. 
Do one or the other. The code is set up for using serial access, and in that case, 
if gpsd is installed, it may be necessary to do
```
  sudo systemctl stop  gpsd
  sudo systemctl disable  gpsd
```

Install LoRaGPS_sensor.py and run it
```
  python3 LoRaGPS_sensor.py
```



###  base station

As of May 2020 the base system is a Raspberry Pi 3B v1.2 running
Raspian 8 (jessie), but has also been occasionally tested on a Raspberry Pi 
Zero W running Raspian 10 (Buster Lite).

It has a no name LoRa 915 MHz SX1276 module with a small 915MHz antenna soldered in
place and solder connections with pins as above for the sensor system. 

In places where something other than 915 MHz should be used be sure to
check the settings in the code before running. 

Follow the normal instructions to download and burn an SD with Raspian.
Set up sshd if you want to run headless. 

The essential additional points are that it needs Python 3, python3-dev, and python modules RPi.GPIO,  spidev, and pySX127x:
```
  sudo apt install python3-dev python3-pip
  pip3 install RPi.GPIO   
  pip3 install spidev 
  sudo apt install git 
  git clone https://github.com/rpsreal/pySX127x # or another source
```
(some of the above may not be needed.

Depending on the install location put something like
```
   export PYTHONPATH=/home/pi/pySX127x/:/home/pi/LoRaGPS/lib
```
in .bashrc

Install LoRaGPS_base.py and run it
```
  python3 LoRaGPS_base.py
```

It might be possible to run OpenCPN on the base station, in which case the AIS feed from
`LoRaGPS_base.py` can go to the localhost with ni special configuration. (If the base station
is a Raspberry Pi, that may involve building OpenCPN rather than just installing it.)
Otherwise the `LoRaGPS_base.py` will need to broadcast from a network port on the base station
so that other computers can use the AIS feed. On a Raspberry Pi that may require setting up
iptables to allow the python code to open the port. See the 'Install a firewall' section of
https://www.raspberrypi.org/documentation/configuration/security.md. 
```
sudo apt install ufw
sudo ufw allow 22/tcp      # for ssh if running headless
sudo ufw allow 65433/udp   # The default port used by LoRaGPS_base.py
sudo ufw status
sudo ufw enable             # legacy command may not be needed?
sudo systemctl start ufw    # starts the service 
sudo systemctl enable ufw   # starts the service on boot
sudo systemctl status ufw
cat /etc/ufw/ufw.conf
sudo ufw logging medium
sudo ufw show listening
```

The whole document is good reading if the base station is to be connected to the Internet 
or publicly accessible. Other ufw commands

