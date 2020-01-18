"""
    Code based on:
        https://github.com/mvillalba/python-ant/blob/develop/demos/ant.core/03-basicchannel.py
    in the python-ant repository and
        https://github.com/tomwardill/developerhealth
    by Tom Wardill
"""
import sys
import time
import struct
import json
from datetime import datetime
from ant.core import driver, node, event, message, log
from ant.core import driver
from ant.core import node
from ant.core.constants import *

LOG = log.LogWriter()
DEBUG = True

def log(msg):
    print(msg)

def getTimestamp():
    return datetime.now()

class Weight:
    DATAPAGE01_BODY_WEIGHT                 = 0x01
    DATAPAGE02_BODY_COMPOSITION_PERCENTAGE = 0x02
    DATAPAGE03_METABOLIC_INFORMATION       = 0x04
    DATAPAGE04_BODY_COMPOSITION_MASS       = 0x08
    DATAPAGE58_USER_PROFILE                = 0x10

    EXPECTED_DATAPAGES =(DATAPAGE01_BODY_WEIGHT |
                         DATAPAGE02_BODY_COMPOSITION_PERCENTAGE |
                         DATAPAGE03_METABOLIC_INFORMATION  |
                         DATAPAGE04_BODY_COMPOSITION_MASS |
                         DATAPAGE58_USER_PROFILE)

    def __init__(self):
        self.timestamp = ''
        self.userProfile = 0
        self.weight = 0.0
        self.gender = ''
        self.age = 0
        self.height = 0
        self.hydrationPercent = 0.0
        self.bodyFatPercent = 0.0
        self.activeMetabolicRate = 0.0
        self.basalMetabolicRate = 0.0
        self.muscleMass = 0.0
        self.boneMass = 0.0
        self.dataPages = 0

    def MakeJSON(self):
        s =  '{ '
        s += '"timestamp": "{0}", '.format(self.timestamp.isoformat())
        s += '"userProfile": {0}, '.format(self.userProfile)
        s += '"weight": {0}, '.format(self.weight)
        s += '"gender": "{0}", '.format(self.gender)
        s += '"age": {0}, '.format(self.age)
        s += '"height": {0}, '.format(self.height)
        s += '"hydrationPercentage": {0}, '.format(self.hydrationPercentage)
        s += '"bodyFatPercentage": {0}, '.format(self.bodyFatPercentage)
        s += '"activeMetabolicRate": {0}, '.format(self.activeMetabolicRate)
        s += '"basalMetabolicRate": {0}, '.format(self.basalMetabolicRate)
        s += '"muscleMass": {0}, '.format(self.muscleMass)
        s += '"boneMass": {0}'.format(self.boneMass)
        s += ' }'
        return s

    def UpdateDataPage1BodyWeight(self,userProfile,weight):
        self.timestamp = getTimestamp()
        self.userProfile = userProfile
        self.weight = weight
        self.dataPages = self.dataPages | Weight.DATAPAGE01_BODY_WEIGHT

    def UpdateDataPage2BodyCompositionPercentage(self,userProfile,hydrationPercentage, bodyFatPercentage):
        self.timestamp = getTimestamp()
        self.userProfile = userProfile
        self.hydrationPercentage = hydrationPercentage
        self.bodyFatPercentage = bodyFatPercentage
        self.dataPages = self.dataPages | Weight.DATAPAGE02_BODY_COMPOSITION_PERCENTAGE

    def UpdateDataPage3MetabolicInformation(self,userProfile,activeMetabolicRate,basalMetabolicRate):
        self.timestamp = getTimestamp()
        self.userProfile = userProfile
        self.activeMetabolicRate = activeMetabolicRate
        self.basalMetabolicRate = basalMetabolicRate
        self.dataPages = self.dataPages | Weight.DATAPAGE03_METABOLIC_INFORMATION

    def UpdateDataPage4BodyCompositionMass(self,userProfile,muscleMass,boneMass):
        self.timestamp = getTimestamp()
        self.userProfile = userProfile
        self.muscleMass = muscleMass
        self.boneMass = boneMass
        self.dataPages = self.dataPages | Weight.DATAPAGE04_BODY_COMPOSITION_MASS

    def UpdateDataPage58UserProfile(self,userProfile,gender,age,height):
        self.timestamp = getTimestamp()
        self.userProfile = userProfile
        self.gender = gender
        self.age = age
        self.height = height
        self.dataPages = self.dataPages | Weight.DATAPAGE58_USER_PROFILE

 
class Scales(event.EventCallback):

    def __init__(self, serial, netkey):
        self.serial = serial
        self.netkey = netkey
        self.antnode = None
        self.channel = None
        self.connected = False
        self.readings = Weight()

    def start(self):
        log("starting node")
        self._start_antnode()
        self._setup_channel()
        self.channel.registerCallback(self)
        log("start listening for hr events")

    def stop(self):
        log("stopping node")
        if self.channel:
            self.channel.close()
            self.channel.unassign()
        if self.antnode:
            self.antnode.stop()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.stop()

    def _start_antnode(self):
        stick = driver.USB2Driver(SERIAL, log=LOG, debug=DEBUG)
        self.antnode = node.Node(stick)
        self.antnode.start()

    def _setup_channel(self):
        key = node.NetworkKey('N:ANT+', self.netkey)
        self.antnode.setNetworkKey(0, key)
        self.channel = self.antnode.getFreeChannel()
        self.channel.name = 'C:Scales'
        self.channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel.setID(119, 0, 0)
        #self.channel.setSearchTimeout(4)
        self.channel.setSearchTimeout(TIMEOUT_NEVER)
        self.channel.setPeriod(8192)
        self.channel.setFrequency(57)
        self.channel.open()

    def processReadings(self):
        if self.readings.dataPages <> Weight.EXPECTED_DATAPAGES:
            print("Didn't receive all datapages {0}".format(self.readings.dataPages))
        else:
            print("Readings...")
            print( self.readings.MakeJSON())

    def process(self, msg):
        try:
            if isinstance(msg, message.ChannelBroadcastDataMessage):
                if not self.connected:
                    self.readings = Weight()
                    self.connected = True

                dataPage = ord(msg.payload[1])
                if dataPage == 1: # Body Weight
                    userProfile,capabilities,weight = struct.unpack('<xxHBxxH',bytearray(msg.payload))
                    log('Body Weight')
                    log('userProfile={0}, capabilities={1}, weight={2}'.format(userProfile,capabilities,weight/100.0))
                    self.readings.UpdateDataPage1BodyWeight(userProfile,weight*0.01)

                elif dataPage == 2: # Body Composition Percentage
                    userProfile,hydration,bodyFat = struct.unpack('<xxHxHH',bytearray(msg.payload))
                    log('Body Composition Percentage')
                    log('userProfile={0}, hydration={1}, bodyFat={2}'.format(userProfile,hydration/100.0,bodyFat/100.0))
                    self.readings.UpdateDataPage2BodyCompositionPercentage(userProfile,hydration*0.01, bodyFat*0.01)

                elif dataPage == 3: # Metabolic Information
                    userProfile,activeMetabolicRate,basalMetabolicRate = struct.unpack('<xxHxHH',bytearray(msg.payload))
                    log('Metabolic Inforation')
                    log('userProfile={0}, activeMetabolicRate={1}, basalMetabolicRate={2}'.format(userProfile,activeMetabolicRate*0.25,basalMetabolicRate*0.25))
                    self.readings.UpdateDataPage3MetabolicInformation(userProfile,activeMetabolicRate*0.25,basalMetabolicRate*0.25)

                elif dataPage == 4: # Body Composition Mass
                    userProfile,muscleMass,boneMass = struct.unpack('<xxHxxHB',bytearray(msg.payload))
                    log('Body Composition Mass')
                    log('userProfile={0}, muscleMass={1}, boneMass={2}'.format(userProfile,muscleMass*0.01,boneMass*0.1))
                    self.readings.UpdateDataPage4BodyCompositionMass(userProfile,muscleMass*0.01,boneMass*0.1)

                elif dataPage == 58: # User Profile Data
                    userProfile,capabilities,genderAndAge,height,descriptive = struct.unpack('<xxHBxBBB',bytearray(msg.payload))
                    log('User Profile Data')
                    log('userProfile={0}, capabilities={1}, gender={2}, age={3}, height={4} cm, descriptive={5}'.format(userProfile,capabilities,'male' if genderAndAge & 128 <> 0 else 'female',genderAndAge&127,height,descriptive) )
                    self.readings.UpdateDataPage58UserProfile(userProfile,'M' if (genderAndAge & 128) <> 0 else 'F', genderAndAge & 127,height)

                elif dataPage == 80: # Manufacturer
                    pass

                elif dataPage == 81: # Product Information
                    pass

                elif dataPage == 70: # Request Data
                    pass

            elif isinstance(msg, message.ChannelEventMessage) and ord(msg.payload[1]) == 1:
                # Channel event
                log('Channel Event')
                messageCode = ord(msg.payload[2])
                if messageCode in (EVENT_RX_SEARCH_TIMEOUT,EVENT_CHANNEL_CLOSED,EVENT_RX_FAIL_GO_TO_SEARCH):
                    log('Disconnected')
                    if messageCode == EVENT_RX_SEARCH_TIMEOUT:
                        log('RX Search Timeout')
                    elif messageCode == EVENT_CHANNEL_CLOSED:
                        log('Channel Closed')
                    elif messageCode == EVENT_RX_FAIL_GO_TO_SEARCH:
                        log('Rx Fail go to search')
                    if self.connected:
                        self.connected = False
                        self.processReadings();
                
        except Exception as e:
            log("Unexpected error:"+ e.__doc__)
            log("Unexpected error:"+ e.message)


SERIAL = '/dev/ttyUSB0'
NETKEY = 'B9A521FBBD72C345'.decode('hex')

with Scales(serial=SERIAL, netkey=NETKEY) as scales:
    scales.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)

 
