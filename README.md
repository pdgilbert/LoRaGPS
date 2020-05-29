# LoRaGPS
Transmit GPS and other information with LoRa

##  Contents
- [Summary and Status](#summary-and-status)
- [Pseudo AIS and OpenCPN Notes](#Pseudo-AIS-and-OpenCPN-notes)
- [Tracking and GPX Notes](#Tracking-and-GPX-Notes)
- [Hardware Setup Notes](#hardware-setup-notes)
- [sensor system](#sensor-system)
- [base station](#base-station)

##  Summary and Status

The code is in an alpha stage. It is working but not extensively tested.

There are two main parts, a "sensor system" and a "base station".
The eventual configuration envisages a large number of sensor systems
(e.g. a large fleet of small boats) while there would be only one or a 
few base stations. In that configuration the sensor systems would be 
headless and without a consistent network connection and the base station(s)
could have monitors or be headless with a network connection.
There are many applications that might use a similar setup.

In development and for installation both systems will need a monitor or
network access with ssh.

The main special requirements of the hardware are that the sensor systems need
a GPS unit and both the sensor systems and the base station need a LoRa module.
More details of the hardware used in development are provided in a section below.

The code is Python 3. 
The main programs, `LoRaGPS_sensor` and `LoRaGPS_base`, use `SX127x` from `pySX127x`.
Following is a brief decription of files in the  project. 

- `LoRaGPS_sensor` -  transmit message over LoRa (not LoRaWAN).
                       Status: working alpha version (on Raspberry Pi Zero W).

- `LoRaGPS_base`   -  receive message over LoRa.
                       Status: working alpha version (on Raspberry Pi 3Bv1.2).

- `lib/AIS.py`    -  Not real AIS! Utilities for converting LoRa broadcast of GPS   
                information into AIS messages to feed into OpenCPN. 
                Status: working but possible precision problem with lon and lat.

- `ais-fake-tx-udp.py` - For testing sending of data to OpenCPN. 
                       Establish UDP multicast group and send some (AIS) messages
                       on thet IFACE/PORT. Status: working.

- `ais-fake-rx-udp.py` - For testing UDP multicast from ais-fake-tx-udp.py and
                       LoRaGPS_base. Wait for UDP  multicasts and print them.
                       Status: working.

- `track2gpx`          - Utility to convert recorded tracks to gpx format.

- `HOSTNAME_MMSIs.json.example`  - Example HOSTNAME_MMSIs.json file.

- `TRACK.json.example`  - Example TRACK.json file.


The unit testing for `AIS.py` is run by   `python3 lib/AIS.py`
 
Examples of starting the base station are
```
   python3 LoRaGPS_base                # use default settings
  ./LoRaGPS_base                       #file needs execute permission
  ./LoRaGPS_base --channel='CH_00_900' # set channel
```
Examples of starting the sensor system are
```
  python3 LoRaGPS_sensor                 # use default settings
  ./LoRaGPS_sensor                       #file needs execute permission
  ./LoRaGPS_sensor --channel='CH_00_900' # set channel
```
The programs could be started in locations other than the program directory (./) but
beware that the base station will look for some files in the directory where it
is started. (See more below.)

If the sensor system is to move in a way that the shell will disconnect, for example,
if the session starting  `LoRaGPS_sensor` is by ssh over wifi and the sensor system
will be move out of wifi range, then try starting with `nohup`, for example
```
  nohup  ./LoRaGPS_sensor --quiet=True  --report=15.0 &
```
and note the pid to stop it with
```
  kill pid 
```

##  LoRaGPS Software Notes

Both `LoRaGPS_sensor` and ` LoRaGPS_base`  take command line arguments to set the
frequency, bandwidth, coding rate, and spreading factor. Use the `--help` argument for
more details. There are trade offs among competing objectives: distance, date rate, 
data reliability, channel congestion, battery life ... . 
These are affected by the various settings.
The best is difficult to determined and will depend on the application. 
For more information, see for example:
[exploratory engineering](https://docs.exploratory.engineering/lora/dr_sf/)
and
[Mark Zachmann blog](https://medium.com/home-wireless/testing-lora-radios-with-the-limesdr-mini-part-2-37fa481217ff)


##  Pseudo AIS and OpenCPN Notes

The `LoRaGPS_sensor` reads NMEA from the GPS, decodes location messages, and transmits
the location data, time stamp, and an identifier (hostname) over LoRa. The `LoRaGPS_base`
receives the messages and constructs a pseudo AIS message that is output over the local
network and is good enough that it can be input into OpenCPN. Do *NOT*
broadcast this over VHF radio, it is not real AIS and would confuse true AIS receivers.

To view in OpenCPN  go to tools>connections and add UDP network connection using
the multicast group (default '224.1.1.4') as the network address and the port (default 65433)
Then 'enable' and 'apply'. 
(Note that the multicast group(s) take the place of a host IP address.)

The group and port can be set as command line arguments to `LoRaGPS_base`. 
If `mcast_group` is set to "NA" then AIS output is turned off.

If AIS output is not turned off then a file `HOSTNAME_MMSIs.json` will be read from the
local directory. If this file does not exist then the code will fail.
This file must give a json dict of the hostname to mmsi mapping, for example
```
{
 "mqtt1": 316456789 , 
 "BT-1" : 338654321
}
```
One important reason *NOT* to broadcast the pseudo AIS over VHF radio is that these MMSI 
need not be legitimate. These are only used locally to identify the sensor systems (which
may be on boats but do not have registered MMSI identifiers). The first three digits of the
MMSI is a MID country code (in the message type used). This can be used to get OpenCPN to
indicate a country flag (316 is Canada, 338 is USA).

The  utility `ais-fake-tx-udp.py` may be useful for testing the `OpenCPN` setup, and
the  utility `ais-fake-rx-udp.py` is for testing the `ais-fake-tx-udp.py`setup.


##  Tracking and GPX Notes

When `LoRaGPS_base` receives a messages it can record it in files in the subdirectory
`TRACKS_time_stamp/` with names determined by the hostnames (e.g. `BT-1.txt`). 
The time stamp is the time LoRaGPS_base is started. Recording is controlled
by the existence and contents of files: `TRACK.json`, `NOT_TRACK.json` and `HOSTNAME_MMSIs.json`.
If `TRACK.json` exists then its contents should be a list of hostnames of sensor systems
for which the gps reports should be recorded, for example 
```
[
 "BT-1", 
 "mqtt1"
]

```
Note that json files are sensitive to the use of double quotes rather than single quotes.
If `TRACK.json` exists then `NOT_TRACK.json` is ignored and tracking is done on the 
indicated sensor systems.

If `TRACK.json` does not exist but file `HOSTNAME_MMSIs.json` exist, 
then sensor systems with hostname keys in `HOSTNAME_MMSIs.json` will be tracked unless
they are listed in `NOT_TRACK.json`. 
(The format of `NOT_TRACK.json` is the same as `TRACK.json`.)
If `NOT_TRACK.json` does not exist then the full list of hostname keys 
in `HOSTNAME_MMSIs.json` will be tracked.
 
The utility `track2gpx` can be used to convert the recorded location information into a
standard `gpx` file that can be displayed in mapping software. 
```
  track2gpx infile.txt  outfile.gpx 
```
The `gpx` track file can be imported into OpenCPN: go to "Route & Mark Manager"> "Tracks" tab,
and click "Import GPX file" at the bottom. Then select and open the file.

There are online utilities to convert `gpx` to a format used by Google Maps, and there are
mapping programs that can use `gpx` directly. (I have been using GPXSee.)


##  Hardware Setup Notes

Below is a description of the setup as initially being tested. 
Many other options are possible but some aspects of the code will need
adjustment if the hardware is configured differently.

In addition to the processors in each, the sensor system has a GPS 
and a LoRa module which transmits information to the base station. 
The base station has a LoRa module to receive information,
and also needs whatever is necessary to do something with that information. 
Typically that would be a network connection to broadcast it, or a monitor
and software to display the information. In some contexts the sensor 
system might be referred to as the "transmitter" and the base station as 
the "receiver" however, some communication in the opposite direction may
eventually be done.


###  sensor system 

As of May 2020 the sensor system is a Raspberry Pi Zero W running
Raspian 10 (Buster Lite). 

It has a Ublox Neo-6M GPS on a no name board "GY-GPS6MV2" with VCC, RX, TX, 
and GND solder points. These are connected to Pi pins as follows.

|  GPS   |Pi pin| Pi BCM |
|:-------|:-----|:---------|
|  VCC |   1  |  3v3      |
|  GND |   6  | GND   |
|  TX  |   8  | BCM 14   |
|  RX  |  10  | BCM 15   |

It also has a no name RFM95 style LoRa 915 MHz module with solder points connected to
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
module will be needed and be sure to check the command line arguments as the
defaults in the code will not be correct. 

Follow the normal instructions to download and burn an SD with Raspian.
Set up sshd if you want to run headless. 

The essential additional points are that it needs Python 3, python3-dev, and 
python modules RPi.GPIO, spidev, Pyserial and pySX127x:

```
  sudo apt install python3-dev python3-pip
  pip3 install RPi.GPIO
  pip3 install spidev 
  pip3 install Pyserial
  sudo apt install git 
  git clone https://github.com/rpsreal/pySX127x # or another source?
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

The `LoRaGPS_sensor` code now reads GPS directly though the serial USART.
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
The sensor system identifies itself using its hostname. (See notes on AIS and on tracking.)
Be sure to set a different hostname for each sensor system, and keep the information for
setting up AIS and tracking.

Install LoRaGPS_sensor and run it
```
  python3 LoRaGPS_sensor
```



###  base station

As of May 2020 the base system is a Raspberry Pi 3B v1.2 running
Raspian 8 (jessie), but has also been occasionally tested on a Raspberry Pi 
Zero W running Raspian 10 (Buster Lite).

It has a no name RFM95 style LoRa 915 MHz SX1276 module with a small 915MHz antenna soldered in
place and solder connections with pins as above for the sensor system. 

In places where something other than 915 MHz should be used be sure to
check the settings in the code before running. 

Follow the normal instructions to download and burn an SD with Raspian.
Set up sshd if you want to run headless. 

The essential additional points are that it needs Python 3, python3-dev, and python 
modules RPi.GPIO,  spidev, and pySX127x:
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

Install LoRaGPS_base and run it
```
  python3 LoRaGPS_base
```

It might be possible to run OpenCPN on the base station, in which case the AIS feed from
`LoRaGPS_base` can go to localhost with no special iptables configuration as below.
(If the base station is a Raspberry Pi, that may involve building OpenCPN rather than 
just installing it.)
Otherwise the `LoRaGPS_base` will need to broadcast from a network port on the base station
so that other computers can use the AIS feed. On a Raspberry Pi that may require setting up
iptables to allow the python code to open the port. See the 'Install a firewall' section of
https://www.raspberrypi.org/documentation/configuration/security.md. 
The whole document is good reading if the base station is to be connected to the Internet 
or publicly accessible.
```
sudo apt install ufw
sudo ufw allow 22/tcp      # for ssh if running headless
sudo ufw allow 65433/udp   # The default port used by LoRaGPS_base
sudo ufw status
sudo ufw enable             # legacy command may not be needed?
sudo systemctl start ufw    # starts the service 
sudo systemctl enable ufw   # starts the service on boot
sudo systemctl status ufw
cat /etc/ufw/ufw.conf
sudo ufw logging medium
sudo ufw show listening
```
The utilities `ais-fake-tx-udp.py` and `ais-fake-rx-udp.py` may be helpful for debugging
the setup.


