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
from ant.core import driver, node, event, message, log
from ant.core import driver
from ant.core import node
from ant.core.constants import *

LOG = log.LogWriter()
DEBUG = True

class HRM(event.EventCallback):

    def __init__(self, serial, netkey):
        self.serial = serial
        self.netkey = netkey
        self.antnode = None
        self.channel = None

    def start(self):
        print("starting node")
        self._start_antnode()
        self._setup_channel()
        self.channel.registerCallback(self)
        print("start listening for hr events")

    def stop(self):
        print("stopping node")
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
        self.channel.name = 'C:HRM'
        self.channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel.setID(119, 0, 0)
        self.channel.setSearchTimeout(TIMEOUT_NEVER)
        self.channel.setPeriod(8192)
        self.channel.setFrequency(57)
        self.channel.open()

    def process(self, msg):
        try:
            if isinstance(msg, message.ChannelBroadcastDataMessage):
                dataPage = ord(msg.payload[1])
                if dataPage == 1: # Body Weight
                    userProfile,capabilities,weight = struct.unpack('<xxHBxxH',bytearray(msg.payload))
                    print('Body Weight')
                    print('userProfile={0}, capabilities={1}, weight={2} ({3}').format(userProfile,capabilities,weight,weight/100)
                elif dataPage == 2: # Body Composition Percentage
                    userProfile,hydration,bodyFat = struct.unpack('<xxHxHH',bytearray(msg.payload))
                    print('Body Composition Percentage')
                    print('userProfile={0}, hydration={1}, bodyFat={2}').format(userProfile,hydration,bodyFat)
                elif dataPage == 3: # Metabolic Information
                    userProfile,activeMetabolicRate,basalMetabolicRate = struct.unpack('<xxHxHH',bytearray(msg.payload))
                    print('Metabolic Inforation')
                    print('userProfile={0}, activeMetabolicRate={1}, basalMetabolicRate={2}').format(userProfile,activeMetabolicRate,basalMetabolicRate)
                elif dataPage == 4: # Body Composition Mass
                    userProfile,muscleMass,boneMass = struct.unpack('<xxHxxHB',bytearray(msg.payload))
                    print('Body Composition Mass')
                    print('userProfile={0}, muscleMass={1}, boneMass={2}').format(userProfile,muscleMass,boneMass)
                elif dataPage == 58: # User Profile Data
                    userProfile,capabilities,genderAndAge,height,descriptive = struct.unpack('<xxHBxBBB',bytearray(msg.payload))
                    print('User Profile Data')
                    print('userProfile={0}, capabilities={1}, gender={2}, age={3}, height={4}, descriptive={5}').format(userProfile,capabilities,genderAndAge & 128,genderAndAge&127,height,descriptive)
                elif dataPage == 80: # Manufacturer
                    pass
                elif dataPage == 81: # Product Information
                    pass
                elif dataPage == 70: # Request Data
                    pass
        except Exception as e:
            print("Unexpected error:", e.__doc__)
            print("Unexpected error:", e.message)


SERIAL = '/dev/ttyUSB0'
NETKEY = 'B9A521FBBD72C345'.decode('hex')

with HRM(serial=SERIAL, netkey=NETKEY) as hrm:
    hrm.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
