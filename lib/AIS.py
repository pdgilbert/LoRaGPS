
'''
Utilities for converting LoRa broadcast of GPS information into AIS like messages.
The purpose of this is to feed the GPS information on a local or loopback network.
This can feed into into OpenCPN for viewing boat locations. The primary interest is
encoding to send to OpenCPN, but decoding code is included for testing.

These are not true AIS messages and should NOT be braodcast.
Only a very small subset of AIS is implemented. 
The code is fairly simple python and might be useful to help understand the
archaic AIS protocol. For testing purposes slightly more has been implemented
than is absolutely necessary for encoding GPS. (eg, the decode is only used for testing)
See https://gpsd.gitlab.io/gpsd/AIVDM.html for considerably more detail about AIS.

examples
# need  export PYTHONPATH=/path/to/LoRaGPS/lib

from AIS import *
cnb  =   AIS1_decode("!AIVDM,1,1,,A,13HOI:0P0000VOHLCnHQKwvL05Ip,0*23" )

# or use just the payload from above
cnb  =   AISpayload1_decode("13HOI:0P0000VOHLCnHQKwvL05Ip" )

AISpayload1_encode(mmsi=123456789, lat=49.40, lon=-72.0, tm=60)

AIS1_encode(mmsi=123456789, lat=49.40, lon=-72.0, tm=60)

In particular, regarding true AIS, this code does not address the standard for
radio transmission, and much gets done and undone by the AIS radio link layer at 
transmission time. Thus this code does not deal with any of the consideration in
https://gpsd.gitlab.io/gpsd/AIVDM.html#_ais_payload_byte_alignment_padding_and_bit_stuffing
which start saying "Warning: Here there be dragons."
'''



######## notes #############################

#https://gpsd.gitlab.io/gpsd/AIVDM.html#_aivdmaivdo_sentence_layer
#Types 1, 2 and 3: Position Report Class A or 18, 19 class B? or 25. 26?
##https://en.wikipedia.org/wiki/Automatic_identification_system#Messages_sent_to_other_equipment_in_the_ship

# MMSI has a country code part, which OpenCPN displays (I think)

# report type   only consider 1 and 18, and possibly 5 for more id info?

###############################################

def AIS1_encode(mmsi=123456789, navStat=8, ROT=128, SOG=1023, PosAcc=False, 
      lon=181.0, lat=91, COG=360, HDG=511, tm=60, mvInd=0,  
      spare=0, RAIM=False, RadStat=0, returnk=False):
   '''
   Call  AISpayload1_encode then add checksum and AIS sentence structure
   '''
   
   p = AISpayload1_encode(mmsi=mmsi, navStat=navStat, ROT=ROT, SOG=SOG, PosAcc=PosAcc, 
      lon=lon, lat=lat, COG=COG, HDG=HDG, tm=tm, mvInd=mvInd,  
      spare=spare, RAIM=RAIM, RadStat=RadStat, returnk=returnk)
   
   if returnk: return(p)
   
   p = 'AIVDM,1,1,,A,' + p + ',0'
   
   #checksum XOR in hex.  compare https://nmeachecksum.eqth.net/
   s= 0
   for c in p:
     s = s^ord(c)
   
   s = hex(s).replace('0x','*').upper()
   
   return(  '!' + p +  s )



def AISpayload1_encode(mmsi=123456789, navStat=8, ROT=128, SOG=1023, PosAcc=False, 
      lon=181.0, lat=91, COG=360, HDG=511, tm=60, mvInd=0,  
      spare=0, RAIM=False, RadStat=0, returnk=False):
   '''
   from GPS info +
   TEST WITH TYPE 1, BUT REALLY CONSIDER 18 OR 19
   returnk=True only for debugging.
   
   See https://gpsd.gitlab.io/gpsd/AIVDM.html#_aivdmaivdo_payload_armoring
   and following sections. Especially 
   https://gpsd.gitlab.io/gpsd/AIVDM.html#_types_1_2_and_3_position_report_class_a
   and Table 6 Common Navigation Block, especially regarding interpretation of fields.
   
   tm 60 if time stamp is not available (default)
   longitude  181 degrees (0x6791AC0 hex) means NA (default).  
   latitude    91 degrees (0x3412140 hex) means NA (default).
   
   navStat = 8 # 'Under way sailing'
   ROT = 128   # rotation in degrees/min. 128 means no turn information available (default)
   SOG = 1023  # indicates speed is not available
   PosAcc = False # 0, the default, indicates an unaugmented GNSS fix with accuracy > 10m
   COG = 360   # data is not available
   HDG = 511   # True Heading data is not available
   mvInd = 0   # Maneuver Indicator NA
   RadStat
   '''
   
   # regarding 2's complement see
   # See https://www.cs.cornell.edu/~tomf/notes/cps104/twoscomp.html
   
   if ROT == -128: ROT = 128 # both mean NA but -128 causes extra char for -.
   
   # convert ROT from sensor measure to ais scale
   if ROT != 128:
      ROT  = int((4.733,  -4.733 )[ROT < 0] * abs(ROT)**0.5)
   
   #def bz(x, fill):  This does not work for negative numbers
   #   return(bin(x).replace('0b','').zfill(fill).replace('-','1') )
   
   def bz(x, fill):
      #see https://stackoverflow.com/questions/12946116/twos-complement-binary-in-python
      #Python does not store or convert to 2's complement. 
      #It uses 0b or -0b for the sign followed by abs value of number.
      c2 = bin(x & int("1"*fill, 2))[2:]
      return(("{0:0>%s}" % fill).format(c2))
  
   chunks = [ 
      bz(1,        6) ,    #0  Message Type	=1
      bz(0,        2) ,    #1  Repeat Indicator =0
      bz(mmsi,    30) ,    #2  MMSI
      bz(navStat,  4) ,    #3  Navigation Status
      bz(ROT,      8) ,    #4  Rate of Turn (ROT) scaled for AIS
      bz(int(SOG),10) ,    #5  Speed Over Ground (SOG)
      bz(PosAcc,   1) ,    #6  Position Accuracy
      bz(int(lon * 600000), 28) ,  #7  Longitude
      bz(int(lat * 600000), 27) ,  #8  Latitude
      bz(int(COG * 10),     12) ,#9  Course Over Ground (COG) Relative to true north
      bz(int(HDG), 9) ,    #10 True Heading (HDG)
      bz(tm,       6) ,    #11 Time Stamp  seconds
      bz(mvInd,    2) ,    #12 Maneuver Indicator NA
      bz(spare,    3) ,    #13 spare
      bz(RAIM,     1) ,    #14 RAIM 0 = not in use (default)
      bz(RadStat, 19) ,    #15 Radio Status
      ]									 
   k = ''.join(chunks) 
   
   if 168 != len(k):
      print('printing debug info.')
      print('length of k should be 168, actual = ', len(k))
      print('chunk lengths should be: 6  2  30 4  8  10 1  28 27 12 9  6  2  3  1 19 ')
      print('len(chunks) and chunks:')
      for ch in chunks:
        print(len(ch), ' "' + ch + '"')
   
   if returnk:  return(k)
   
   x = "0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW" +"`abcdefghijklmnopqrstuvw"
   
   split6 = []
   for i in range(0, 28):
      split6.append(x[int(k[i*6: i*6+6], 2)])
   
   return(''.join(split6))

#AISpayload1_encode(mmsi=123456789, lat=49.40, lon=-72.0, tm=60)
#  '11mg=5HP?wJnJ@0LA5@>4?wp0000'

#AIS1_encode(mmsi=123456789, lat=49.40, lon=-72.0, tm=60)


#sixbit_num  = [bin(i).replace('0b','').zfill(6) for i in range(0, 64)]
#sixbit_alpa = [bin(ord(i)).replace('0b','').zfill(6)  for i in
#    '@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_ !"#$%' + "&'()*+,-./0123456789:;<=>?" ]
#sixbit_alpa[int('000000', 2)]
#sixbit_num[int('000000', 2)]



def AIS1_decode(sentence, description=True, onlyValid=True, returnk=False):
   '''
   Check checksum, extract payload and call AISpayload1_decode
   '''
   m = sentence.split('*')[0][1:]
   
   #checksum XOR in hex.  compare https://nmeachecksum.eqth.net/
   s= 0
   for c in m:
      s = s^ord(c)
   s = hex(s).replace('0x', '').upper()
   
   if s != sentence.split('*')[1]: 
      print('indicated checksum ', sentence.split('*')[1], '. computed  checksum ', s)
      raise ValueError("Payload checksum failure.")
   
   p = m.split(',')[5]
   
   return(AISpayload1_decode(p, description=description, onlyValid=onlyValid, returnk=returnk))



def AISpayload1_decode(payload, description=True, onlyValid=True, returnk=False):
   '''
   If description=False the numeric values for all fields are returned.
   If description=True then some fields are replaced by decriptive values.
   onlyValid=True checks result by running cnbValid before returning. If set
   False then this check is skipped (mainly for debugging).
   returnk=True only for debugging.
   
   See https://gpsd.gitlab.io/gpsd/AIVDM.html#_aivdmaivdo_payload_armoring
   and following sections. Especially 
   https://gpsd.gitlab.io/gpsd/AIVDM.html#_types_1_2_and_3_position_report_class_a
   and Table 6 Common Navigation Block, especially regarding interpretation of fields.
   '''
   
   if not 0 < len(payload) :
      raise ValueError("Payload checksum failure.")
   
   # Do not think of x1 and x2 characters as meaning much other than the 6-bit ascii display
   # of an encoded message. They are convenient to build the decoding used for constructing 
   # the bit string k which is parsed to get the message.
   
   x1 = "0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW"
   x2 = "`abcdefghijklmnopqrstuvw"
   
   y  = [ord(ch)-48 for ch in x1] + [ord(ch)-56 for ch in x2] 
   
   z = ['{:006b}'.format(i) for i in y]
   
   k = ''.join([z[(x1 + x2).index(i)] for i in payload])
   
   # IT IS POSSIBLE ROT NEEDS TO BE SQUARED AND SCALED
   #ROT is 8 bit 2's compliment, first bit is the sign.
   #lat and lon are 2's compliment in 27 and 28 bit fields,  first bit is the sign.
   #The lat and lon  seem to be handled ok by int( ,2). TO CONFIRM MORE CAREFULLY
   #But for ROT 128 gives (negative) 0 (as it should) but that needs to be 128 meaning NA.
   # m = bin(128).replace('0b','') .zfill(8) .replace('-','1')
   # (1, -1)[m[0]=='1'] * int(m[1:],  2)  # this gives (negative) 0 for 128 
   # so define rot
   
   def I(m):
      #For ROT '10000000' needs for give 128 rather than -0.
      if m ==  '10000000' :
         return(128)
      elif m[0]=='1' :
         # 2s complement in string
         return(-int(m[1:].replace('1','x').replace('0','1').replace('x','0'), 2) +1)
      else :
         return( int(m[1:],  2) )
   
   
   cnb = [
     int(k[0:6],       2),    #0  Message Type
     int(k[6:8],       2),    #1  Repeat Indicator
     int(k[8:38],      2),    #2  MMSI
     int(k[38:42],     2),    #3  Navigation Status
     I(  k[42:50]       ),    #4  Rate of Turn (ROT) AIS
     int(k[50:60],2)  /10,    #5  Speed Over Ground (SOG)
     bool(int(k[60],  2)),    #6  Position Accuracy
     I(k[61:89] ) /600000,    #7  Longitude
     I(k[89:116]) /600000,    #8  Latitude
     int(k[116:128],2)/10,    #9  Course Over Ground (COG) Relative to true north,
     int(k[128:137],   2),    #10 True Heading (HDG)
     int(k[137:143],   2),    #11 Time Stamp
     int(k[143:145],   2),    #12 Maneuver Indicator
     k[145:148]          ,                           #13 Spare
     bool(int(k[148], 2)),                 #14 RAIM flag
     int(k[149:168], 2)  ]                  #15 Radio status
   
   # NOT SURE ABOUT RESCALING FOR SPECIAL VALUES?
   
   if cnb[5] == 102.2:  cnb[5] = 1022  # 1022 means > 102.0 knots
   if cnb[5] == 102.3:  cnb[5] = 1023  # 1023 means NA
   if cnb[9] == 360.0:  cnb[9] = 3600  # 3600 means NA
   
   if description:
      navStat = (
   	 "Under way using engine", "At anchor", "Not under command", "Restricted manoeuverability",
   	 "Constrained by her draught", "Moored", "Aground", "Engaged in Fishing", 
   	 "Under way sailing",	 "Reserved for future amendment of Navigational Status for HSC", 
   	 "Reserved for future amendment of Navigational Status for WIG", 
   	 "Reserved for future use", "Reserved for future use", "Reserved for future use", 
   	 "AIS-SART is active", "Not defined (default)" )
      
      
      mvInd = (
   	 "Not available (default)", "No special maneuver", 
   	 "Special maneuver (such as regional passing arrangement)" )
   
      cnb[3]  = navStat[cnb[3]]
      cnb[12] = mvInd[cnb[12]]
   
   if returnk:
      return(k)
   
   if onlyValid:
      cnbValid(cnb) 
     
   return(cnb)



def cnbValid(x):
   # This check is for local use (eg what is/might be implemented)
   # Lots of these are are more restrictive than the standard
   # 181 degrees (0x6791AC0 hex) longitude means NA (default).  
   #  91 degrees (0x3412140 hex)  latitude means NA (default).
   
   assert x[0] in range(1, 27 )        , " x[0] failed."  # standard
   assert x[0] in (1, 2, 3, 5, 18)     , " x[0] failed 2."# local restricted to types
   assert x[1] in (0,)                 , " x[1] failed."  # local no multi sentence messages
   #assert 99999999 < x[2] < 1000000000, " x[2] failed."  # MMSI range
   #MMSI   seem to be shorter sometimes and (US vessels travelling in the US omit country code.)
   assert     99999 < x[2] < 1000000000 , " x[2] failed."  # MMSI range
   
   #assert  x[3] in navStat or x[3] in range(0, 16) , " x[3] failed."
   
   assert   x[3] in range(0, 16)       , " x[3] failed."
   assert  -128  <= x[4]  <= 128       , " x[4] failed."  # standard ROT values +/-128 for NA
   
   assert (0.0 <=  x[5]  <= 102) or x[5]  in (1022, 1023) , " x[5] failed." # standard SOG
   assert isinstance(x[6], bool)       , " x[6] failed."
   assert   -180 <= x[7] <= 181        , " x[7] failed."  # standard 181 degrees for NA
   assert    -90 <= x[8] <=  91        , " x[8] failed."  # standard  91 degrees for NA
   assert ( -360 <= x[9] <= 360) or x[9]  == 3600  , " x[9] failed."  # standard COG 3600 for NA
   assert   ( 0 <= x[10] <= 359) or x[10] == 511   , " x[10] failed."   # standard 511 for NA
   assert x[11] in range(1, 63 )       , " x[11] failed."  # 60=NA, 61=manual, 62=est., 62=inoperative
   #assert x[12] in mvInd  or x[12] in range(0, 3 ) , " x[12] failed."      # standard
   assert x[12] in range(0, 3 )        , " x[12] failed."      # standard
   assert isinstance(x[14], bool)      , " x[14] failed."      
   
   return(True)


def cnbCompare(x, y, fuzz=1e-7):
   '''
   Check x and y are equal. Return True or False
   128 and -128 are the same for ROT
   '''
   # this is needed in case  x or y is a tuple 
   rotx = x[4]
   roty = y[4]
   if rotx == -128 : rotx = 128 
   if roty == -128 : roty = 128 
   
   ok = True
   
   if x[ 0] != y[ 0] :
      print("message type comparison failed. ", x[0], " vs ", y[0] )
      ok = False 
   
   if x[ 1] != y[ 1] :
      print("multi sentence comparison failed. ", x[1], " vs ", y[1] )  
      ok = False 
   
   if x[ 2] != y[ 2] :
      print("MMSI comparison failed. ", x[2], " vs ", y[2] ) 
      ok = False 
   
   if x[ 3] != y[ 3] :
      print("navStat comparison failed. ", x[3], " vs ", y[3] ) 
      ok = False 
   
   if abs(rotx - roty) > fuzz  :
      print("ROT comparison failed. ", x[4], " vs ", y[4] ) 
      print("difference. ", abs(x[4] - y[4]) ) 
      ok = False 
   
   if x[ 5] != y[ 5] :
      print("SOG comparison failed. ", x[5], " vs ", y[5] ) 
      ok = False 
   
   if x[ 6] != y[ 6] :
      print("Position accuracy comparison failed. ", x[6], " vs ", y[6] ) 
      ok = False 
   
   if abs(x[ 7] - y[ 7]) > fuzz :
      print("longitude comparison failed. ", x[7], " vs ", y[7] ) 
      print("difference. ", abs(x[7] - y[7]) ) 
      ok = False 
   
   if abs(x[ 8] - y[ 8]) > fuzz :
      print("latitude comparison failed. ", x[8], " vs ", y[8] ) 
      print("difference. ", abs(x[8] - y[8]) ) 
      ok = False 
   
   if x[ 9] != y [9] :
      print("COG comparison failed. ", x[9], " vs ", y[9] ) 
      ok = False 
   
   if x[10] != y[10] :
      print("True Heading (HDG) comparison failed. ", x[10], " vs ", y[10] )
      ok = False 
   
   if x[11] != y[11] :
      print("Time stamp seconds comparison failed. ", x[11], " vs ", y[11] ) 
      ok = False 
   
   if x[12] != y[12] :
      print("Maneuver Indicator comparison failed. ", x[12], " vs ", y[12] )  
      ok = False 
   
   #if x[13] != y[13] :
   #   print("spare comparison failed. ", x[13], " vs ", y[13] ) 
   #   ok = False 
   
   if x[14] != y[14] :
      print("RAIM flag comparison failed. ", x[14], " vs ", y[14] ) 
      ok = False 
   
   #if x[15] != y[15] :
   #   print("Radio status comparison failed. ", x[15], " vs ", y[15] ) 
   #   ok = False 
   
   return(ok)

###########################################################################
####################### unittest  tests  ##################################
###########################################################################

# Values for some of these tests are obtained using the 
#  online decoder facility and example sentences at
#  https://www.maritec.co.za/tools/aisvdmvdodecoding/
#  Note that E/W and N/S at that site are indicated in the LIST OF MESSAGE TYPE 1,2,3
#  at the bottom of the maritec report, and NOT with a +/- sign in the 'Position Report'

import unittest


class TestAIS(unittest.TestCase):

    #self.assertEqual(x, y, message)
    #self.assertTrue(x, message)
    
    def test_E_1(self):
        # need to confirm this is a correct test
        self.assertEqual(
           AISpayload1_encode(mmsi=123456789, lon=-72.0, lat=49.40, tm=60), 
           '11mg=5HP?wJnJ@0LA5@>4?wp0000', 
           "encoding test E_1 failed.")

    def test_E_D_1(self):
        self.assertTrue(
           cnbCompare(
              AISpayload1_decode( AISpayload1_encode(
                 mmsi=123456789, lon=-72.0, lat=49.40, tm=60), description=False),
     [1, 0, 123456789, 8, 128, 1023, False, -72.0, 49.4, 3600, 511, 60, 0, '000', False, 0],  
              fuzz=1e-5),  "encode and decoding test E_D_1 failed.")

    
    #     !AIVDM,1,1,,A,13HOI:0P0000VOHLCnHQKwvL05Ip,0*23

    def test_D_1(self):    
        self.assertTrue(
           cnbCompare(
              AISpayload1_decode("13HOI:0P0000VOHLCnHQKwvL05Ip" , description=False),
      ( 1, 0, 227006760, 0, -128.0, 0.0, 0, 0.1313800, 49.4755767, 36.7, 511, 14, 0, 0, 0 )),
            "decoding test D_1 failed.")
 
    def test_D_2(self):    
        self.assertTrue(
           cnbCompare(
              AIS1_decode("!AIVDM,1,1,,A,13HOI:0P0000VOHLCnHQKwvL05Ip,0*23" , description=False),
      ( 1, 0, 227006760, 0, -128.0, 0.0, 0, 0.1313800, 49.4755767, 36.7, 511, 14, 0, 0, 0 )),
            "decoding test D_2 failed.")


    #       !AIVDM,1,1,,A,133sVfPP00PD>hRMDH@jNOvN20S8,0*7F

    def test_D_3(self):    
        self.assertTrue(
           cnbCompare(
              AISpayload1_decode("133sVfPP00PD>hRMDH@jNOvN20S8" , description=False),
       ( 1, 0, 205448890, 0, -128.0, 0.0, 1, 4.4194417, 51.2376583, 63.3, 511, 15, 0, 0, 1 )),
            "decoding test D_3 failed.")

    def test_D_4(self):    
        self.assertTrue(
           cnbCompare(
              AIS1_decode("!AIVDM,1,1,,A,133sVfPP00PD>hRMDH@jNOvN20S8,0*7F" , description=False),
       ( 1, 0, 205448890, 0, -128.0, 0.0, 1, 4.4194417, 51.2376583, 63.3, 511, 15, 0, 0, 1 )),
            "decoding test D_4 failed.")


    #       !AIVDM,1,1,,A,133sVfPP00SbS242Qn4@?wvN2000,0*3B

    # next should all give same (payload) result

    def test_E_2(self):
        self.assertEqual(
           '133sVfPP00SbS242Qn4@?wvN2000',
           AISpayload1_encode(
              205448890, 0, -128, 0.0, 1, 51.2376583, 4.4194417, 6.3, 511, 15, 0, 0, 1, 0 ),
           "encoding test E_2 failed.")
    # 51.2376583 vs 51.2376567 on test site

    def test_E_3(self):
        self.assertEqual(
           '133sVfPP00SbS242Qn4@?wvN2000',
           AISpayload1_encode(
              mmsi=205448890, navStat=0, ROT=-128, SOG=0.0, PosAcc=1, 
              lon=51.2376583, lat=4.4194417, COG=6.3, HDG=511, tm=15, mvInd=0,  
              spare=0, RAIM=True, RadStat=0, returnk=False),
           "encoding test E_3 failed.")

    def test_E_4(self):
        self.assertEqual(
           '!AIVDM,1,1,,A,133sVfPP00SbS242Qn4@?wvN2000,0*3B',
           AIS1_encode(
              205448890, 0, -128, 0.0, 1, 51.2376583, 4.4194417, 6.3, 511, 15, 0, 0, 1, 0 ),
           "encoding test E_4 failed.")


    def test_E_5(self):
        self.assertEqual(
           '!AIVDM,1,1,,A,133sVfPP00SbS242Qn4@?wvN2000,0*3B',
           AIS1_encode(
              mmsi=205448890, navStat=0, ROT=-128, SOG=0.0, PosAcc=1, 
              lon=51.2376583, lat=4.4194417, COG=6.3, HDG=511, tm=15, mvInd=0,  
              spare=0, RAIM=True, RadStat=0, returnk=False),
           "encoding test E_5 failed.")

    def test_E_6(self):
        self.assertEqual(
           '!AIVDM,1,1,,A,133sVfPP00SbS242Qn4@?wvN2000,0*3B',
           AIS1_encode(
              205448890, 0, -128, 0.0, 1, 51.2376583, 4.4194417, 6.3, 511, 15, 0, 0, 1, 0 ),
           "encoding test E_6 failed.")

    def test_D_5(self):    
        self.assertTrue(
           cnbCompare(
              AIS1_decode('!AIVDM,1,1,,A,133sVfPP00SbS242Qn4@?wvN2000,0*3B' , description=False), 
   [1, 0, 205448890, 0, -128, 0.0, 1, 51.2376583, 4.4194417, 6.3, 511, 15, 0, 0, 1, 0 ] ,
              fuzz=1e-5 ),  #reduced tolerance for longitude comparison
              "decoding test D_5 failed.")


    #       !AIVDM,1,1,,B,100h00PP0@PHFV`Mg5gTH?vNPUIp,0*3B

    def test_D_6(self):    
        self.assertTrue(
           cnbCompare(
              AISpayload1_decode(
                 "100h00PP0@PHFV`Mg5gTH?vNPUIp" , description=False),
      ( 1, 0, 786434, 0, -128.0, 1.6, 1, 5.3200333, 51.9670367, 112.0, 511, 15, 1, 0, 0 )),
              "decoding test D_6 failed.")

    def test_D_7(self):    
        self.assertTrue(
           cnbCompare(
              AIS1_decode(
                 "!AIVDM,1,1,,B,100h00PP0@PHFV`Mg5gTH?vNPUIp,0*3B" , description=False),
      ( 1, 0, 786434, 0, -128.0, 1.6, 1, 5.3200333, 51.9670367, 112.0, 511, 15, 1, 0, 0 )),
              "decoding test D_7 failed.")

    #       !AIVDM,1,1,,B,13eaJF0P00Qd388Eew6aagvH85Ip,0*45

    def test_D_8(self):    
        self.assertTrue(
           cnbCompare(
              AISpayload1_decode(
                 "13eaJF0P00Qd388Eew6aagvH85Ip" , description=False),
      ( 1, 0, 249191000, 0, -128.0, 0.0, 1, 23.6036333, 37.9558833, 247.0, 511, 12, 0, 2, 0 )),
              "decoding test D_8 failed.")

    def test_D_9(self):    
        self.assertTrue(
           cnbCompare(
              AIS1_decode(
                 "!AIVDM,1,1,,B,13eaJF0P00Qd388Eew6aagvH85Ip,0*45" , description=False),
      ( 1, 0, 249191000, 0, -128.0, 0.0, 1, 23.6036333, 37.9558833, 247.0, 511, 12, 0, 2, 0 )),
              "decoding test D_9 failed.")

    # AISpayload1_decode("13eaJF0P00Qd388Eew6aagvH85Ip" , returnk=True)[61:89]
    # x='0000110110000001100100000100'   



    #       !AIVDM,1,1,,A,14eGrSPP00ncMJTO5C6aBwvP2D0?,0*7A

    def test_E_7(self):
        self.assertEqual(
           '!AIVDM,1,1,,A,14eGrSPP00ncMJTO5C6aBwvP2D0?,0*7A',
           AIS1_encode(
              mmsi=316013198, navStat=0, ROT=-128, SOG=0.0, PosAcc=1, 
              lon= -130.3162367, lat= 54.3211100, COG=237.9, HDG=511, tm=16, mvInd=0,  
              spare=0, RAIM=True, RadStat=81935, returnk=False),
           "encoding test E_7 failed.")

    # radio status not reported at maritec but the value needed for the same checksum above is
    #int(AISpayload1_decode("14eGrSPP00ncMJTO5C6aBwvP2D0?" , returnk=True)[149:] , 2)  # 81935

    
    def test_D_10(self):    
        self.assertTrue(
           cnbCompare(
              AISpayload1_decode(
                 "14eGrSPP00ncMJTO5C6aBwvP2D0?" , description=False),
  (1,0, 316013198, 0, -128.0, 0.0, 1, -130.3162367, 54.3211100, 237.9, 511, 16, 0, 0, 1, 81935),
              fuzz=1e-5 ),  #reduced tolerance for longitude comparison
              "decoding test D_10 failed.")


    #       test positive ROT 

    def test_E_8(self):
        self.assertEqual(
           '!AIVDM,1,1,,A,133sVfP5@0SbS242Qn4@?wvN2000,0*2E',
           AIS1_encode(
              205448890, 0, 20, 0.0, 1, 51.2376583, 4.4194417, 6.3, 511, 15, 0, 0, 1, 0 ),
           "encoding test E_8 failed.")

    #maritec shows +19.7 vs 20 ; 51.2376567 vs 51.2376583 
    #OpenCPN says   20  deg/min right


    def test_E_9(self):
        self.assertEqual(
           '!AIVDM,1,1,,A,133sVfh<@0P00002Qn4@?wvN2000,0*2B',
           AIS1_encode(
              205448891, 0, 108, 0.0, 1, 0.000000, 4.4194417, 6.3, 511, 15, 0, 0, 1, 0 ),
           "encoding test E_9 failed.")

    #maritec shows  +107.2 vs 108 
    #OpenCPN says    107  deg/min right


    #       test negative ROT

    def test_E_6(self):
        self.assertEqual(
           '!AIVDM,1,1,,A,133sVg0rh0rAjP02Qn4@?wvN2000,0*7D',
           AIS1_encode(
              205448892, 0, -20, 0.0, 1, -80.0000, 4.4194417, 6.3, 511, 15, 0, 0, 1, 0 ),
           "encoding test E_6 failed.")

    #maritec shows  -19.7  vs  -20 
    #OpenCPN says    20  deg/min left


    def test_D_11(self):    
        self.assertTrue(
           cnbCompare(
              AISpayload1_decode(
                 "15MrVH0000KH<:V:NtBLoqFP2H9:" , description=False),
  ( 1, 0, 366913120, 0, 0.0, 0.0, 0, -64.6206617, 18.3211883, 329.5, 299, 16, 0, 0, 1 ),
              fuzz = 1e-5), # fuzz increased for longitude comparison -64.62065833333334  vs  -64.6206617
              "decoding test D_11 failed.")


    def test_D_12(self):    
        self.assertTrue(
           cnbCompare(
              AISpayload1_decode(
                 "15N9NLPP01IS<RFF7fLVmgvN00Rv" , description=False),
  ( 1, 0, 367156850, 0, -128.0, 0.1, 0, -90.1784350, 38.6587500, 175.0, 511, 15, 0, 0, 0 ),
                  fuzz = 1e-5), # fuzz increased for lon comparison -90.17843166666667  vs  -90.178435
              "decoding test D_12 failed.")


###########       country code tests

## ADD CORK EXAMPLES WITH COUNTRY CODES and small gps differences




########################################################################################

if __name__ == '__main__':
    unittest.main()

# run this using
# python3 lib/AIS.py
