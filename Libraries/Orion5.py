import threading
import queue
import serial
import time
import datetime as dt
from packet_test import bytes_to_hex_bytes_string
import copy


DEBUG = False
DEBUG_MODE = 'PRINT'

SERIAL_BAUD_RATE = 250000
SERIAL_TIMEOUT = 1  # seconds
QUEUE_SLEEP_TIME = 0.01  # seconds
READ_INTERVAL = 0.1  # seconds

QUEUE_LEN = 200
READ_PACKET_LEN = 7

CLAW_OPEN_POS = 300
CLAW_CLOSE_POS = 120

class ErrorIDs:
    INSTRUCTION_ERROR = 0x40
    OVERLOAD_ERROR = 0x20
    CHECKSUM_ERROR = 0x10
    RANGE_ERROR = 0x08
    OVERHEATING_ERROR = 0x04
    ANGLE_LIMIT_ERROR = 0x02
    INPUT_VOLTAGE_ERROR = 0x01

class ControlModes:
    SPEED, TIME, WHEEL = range(3)

class JointVars:
    CW_LIMIT, CCW_LIMIT, MARGIN, SLOPE, PUNCH, TORQUE_ENABLE,\
        GOAL_POS, SPEED, MODE, CURRENT_POS, CURRENT_SPEED, CURRENT_LOAD, CHECKER = range(13)

class SerialThread(threading.Thread):
    def __init__(self, orion5_reference, serialName, sendQueue, lock):
        threading.Thread.__init__(self)
        self._outboxIterator = [['misc variables', [['cwAngleLimit',JointVars.CW_LIMIT],
                                                   ['ccwAngleLimit',JointVars.CCW_LIMIT],
                                                   ['margin', JointVars.MARGIN],
                                                   ['slope', JointVars.SLOPE],
                                                   ['punch', JointVars.PUNCH]]],
                               ['control variables', [['enable',JointVars.TORQUE_ENABLE],
                                                      ['goalPosition', JointVars.GOAL_POS],
                                                      ['desiredSpeed', JointVars.SPEED],
                                                      ['controlMode', JointVars.MODE]]]]
        self.arm = orion5_reference
        self.sendQueue = sendQueue
        self.lock = lock
        self.running = True
        self.uart = None
        self.lastReadTime = time.perf_counter()
        self._checker = [0, 0, 0, 0]
        try:
            self.uart = serial.Serial(port=serialName,
                                      baudrate=SERIAL_BAUD_RATE,
                                      write_timeout=0,
                                      timeout=SERIAL_TIMEOUT)
        except serial.SerialException:
            debug("SerialThread: Unable to find serial device")
            debug("SerialThread: Thread will immediately exit")
            self.stop()

    def SerialSController(self, Command):
        if Command == 'Start':
            try:
                self.uart = serial.Serial(port=serialName,
                                          baudrate=SERIAL_BAUD_RATE,
                                          write_timeout=0,
                                          timeout=SERIAL_TIMEOUT)
                return True
            except serial.SerialException:
                #Do something else here, perhaps widen a delay on the thread for 'listen' mode
                debug("SerialThread: Unable to find serial device")
                debug("SerialThread: Thread will immediately exit")
                self.stop()
                return False
        elif Command == 'Stop':
            self.uart.close()
            self.uart = None
            print('yolo')
        elif Command == 'Status':
            print('yolo')

    def run(self):
        if self.uart is None:
            return
        debug("SerialThread: Thread started")
        self.main()
        self.uart.close()
        debug("SerialThread: Thread stopped")

    def stop(self):
        if self.running:
            debug("SerialThread: Stopping thread")
            self.running = False
        else:
            debug("SerialThread: Thread already stopped")

    def main(self):
        self.processSend((1, JointVars.CHECKER, self._checker[0], self._checker[0]))
        while self.running:
            time.sleep(.2)
            if self._checker[0] == self._checker[1]:
                #Send all the updates to the ARM
                self.SendUpdate()
                self.CheckerAdvance()
            while not(self.processSend((1, JointVars.CHECKER, self._checker[0], self._checker[0]))):
                debug('Failed to send checker')
            while self.uart.in_waiting >= READ_PACKET_LEN:
                self.processRead()
            else:
                debug('End Read')
            #time.sleep(QUEUE_SLEEP_TIME)
        self.SendUpdate()

    def CheckerAdvance(self):
        # Advance the Checker
        if self._checker[0] >= 255:
            self._checker[0] = 0
        else:
            self._checker[0] += 1

    def SendUpdate(self):
        # Send all the updates to the ARM
        for JointObj in self.arm.joints:
            for itemSet in self._outboxIterator:
                for item in itemSet[1]:
                    if JointObj.checkVariable(itemSet[0], item[0]):
                        ID = JointObj.getVariable('constants', 'ID')
                        if self._checker[0] >= 255:
                            self._checker[0] = 0
                        else:
                            self._checker[0] += 1
                        self.processSend((ID, item[1], JointObj.getVariable(itemSet[0], item[0]), self._checker[0]))
                        while True:
                            while self.uart.in_waiting >= 3:
                                self.processRead()
                            else:
                                debug('End Read')
                                if self._checker[0] == self._checker[1]:
                                    JointObj.TickVariable(itemSet[0], item[0])
                                    break
                                else:
                                    self.processSend((ID, item[1], JointObj.getVariable(itemSet[0], item[0]), self._checker[0]))

    def processSend(self, command):
        packet = self.buildPacket(command)
        retValue = self.sendPacket(packet)
        time.sleep(.01)
        return retValue

    def processRead(self):
        secondByte = None
        while True:
            try:
                firstByte = list(self.uart.read(1))[0]
            except:
                debug('could not read firstByte')
                return False
            if firstByte == 240:
                try:
                    secondByte = list(self.uart.read(1))[0]
                except:
                    debug('Could not read secondByte')
                if secondByte == 240:
                    break
            debug('Buffer Bytes   ' + str(firstByte)+'   '+str(secondByte))
        debug('Success Buffer Bytes   ' + str(firstByte) +'   '+ str(secondByte))
        try:
            header = list(self.uart.read(2))
            packetType = ((header[0] & 0xF0) >> 4)
            debug('Header   '+str(header)+'  Packet Type  '+str(packetType))
            if packetType == 0:
                # < Packet_type errorID > < jointID speedH > < speedM speedL > < loadH loadM > < loadL posH > < posM posL >
                packet = list(self.uart.read(4))
                debug('The packet held: '+str(packet)+str({'jointID': ((header[1] & 0xF0) >> 4),
                                   'errorID': (header[0] & 0x0F),
                                   'speed': (header[1] << 8) | packet[0],
                                   'load': (packet[1] << 4) | ((packet[2] & 0xF0) >> 4),
                                   'pos': ((packet[2] & 0x0F) << 8) | packet[3]}))
                self.updateJoints({'jointID': ((header[1] & 0xF0) >> 4),
                                   'errorID': (header[0] & 0x0F),
                                   'speed': (header[1] << 8) | packet[0],
                                   'load': (packet[1] << 4) | ((packet[2] & 0xF0) >> 4),
                                   'pos': ((packet[2] & 0x0F) << 8) | packet[3]})
            elif packetType == 1:
                # < Packet_type errorID > < Checker >
                self._checker[1] = header[1] #list(self.uart.read(1))[0]
                debug('Checker  '+str(self._checker))
            '''elif header[0] == 240:
                packet = list(self.uart.read(2))
                #The packetType number will stipulate which variable is being read... do things here XXXX'''
        except:
            debug('Could not read')

    def buildPacket(self, data):
        # <0000 0000> = 1 byte
        # send packets look like: <jointID varID> <varH> <varL>
        packet = [0] * 6
        packet[0] = (240 & 0x00FF)
        packet[1] = (240 & 0x00FF)
        packet[2] = ((data[0] & 0x000F) << 4) | (data[1] & 0x000F)
        packet[3] = ((data[2] & 0xFF00) >> 8)
        packet[4] = (data[2] & 0x00FF)
        packet[5] = (data[3] & 0x00FF)
        debug("SerialThread: processSend: sent " + str(packet) + ' ' + str(data))
        return bytes(packet)

    def sendPacket(self, packet):
        if self.uart is None:
            debug("SerialThread: sendPacket: uart is None")
            return False
        try:
            self.uart.write(packet)
            return True
        except serial.SerialTimeoutException:
            debug("SerialThread: sendPacket: timeout writing to serial port")
            return False

    def updateJoints(self, data):
        # TODO: make functions for conversion e.g. G15 pos to angle
        self.arm.joints[data['jointID'] - 1].setVariable('misc variables', 'error', data['errorID'])
        self.arm.joints[data['jointID'] - 1].setVariable('feedback variables', 'currentVelocity', data['speed'])
        self.arm.joints[data['jointID'] - 1].setVariable('feedback variables', 'currentLoad', data['load'])
        self.arm.joints[data['jointID'] - 1].setVariable('feedback variables', 'currentPosition', data['pos'])

class Joint(object):
    def __init__(self, name, ID, cwAngleLimit, ccwAngleLimit, margin, slope, punch, speed, mode):
        # TODO: make all vars private and create getters/setters
        # constants
        self._jointLock = threading.Lock()
        self._datam = {'constants':{'ID':[ID, True],
                                    'name':[name, True]},
                       'misc variables':{'cwAngleLimit':[cwAngleLimit, True],
                                         'ccwAngleLimit':[ccwAngleLimit, True],
                                         'margin':[margin, True],
                                         'slope':[slope, True],
                                         'punch':[punch, True],
                                         'error':[None, False]},
                       'control variables':{'enable':[0, True],
                                            'goalPosition':[None, False],
                                            'desiredSpeed':[speed, True],
                                            'controlMode':[mode, True]},
                       'feedback variables':{'currentPosition':[None, False],
                                             'currentVelocity':[None, False],
                                             'currentLoad':[None, False]}}

    def init(self):
        self.setTorqueEnable(0)
        print(self.getVariable('control variables', 'controlMode'), ControlModes.TIME)
        self.setControlMode(self.getVariable('control variables', 'controlMode'))
        print(self.getVariable('control variables', 'controlMode'), ControlModes.TIME)
        if self.getVariable('control variables', 'controlMode') == ControlModes.TIME:
            self.setTimeToGoal(self.getVariable('control variables', 'desiredSpeed'))
        else:
            self.setSpeed(self.getVariable('control variables', 'desiredSpeed'))

    def setVariable(self, id1, id2, datum):
        self._jointLock.acquire()
        self._datam[id1][id2] = [datum, True]
        self._jointLock.release()
        return

    def getVariable(self, id1, id2):
        self._jointLock.acquire()
        retValue = copy.copy(self._datam[id1][id2][0])
        self._jointLock.release()
        return retValue

    def checkVariable(self, id1, id2):
        self._jointLock.acquire()
        retValue = copy.copy(self._datam[id1][id2][1])
        self._jointLock.release()
        return retValue

    def TickVariable(self, id1, id2):
        self._jointLock.acquire()
        self._datam[id1][id2][1] = not self._datam[id1][id2][1]
        self._jointLock.release()
        return

    def setControlMode(self, mode):
        self.setVariable('control variables', 'controlMode', mode)

    def setTimeToGoal(self, seconds):
        seconds = int(seconds * 10)
        assert self.getVariable('control variables', 'controlMode') == ControlModes.TIME, "Control mode not set to time"
        assert 0 <= seconds <= 1023, "Time outside valid range: 0-1024"
        self.setVariable('control variables', 'desiredSpeed', seconds)

    def setSpeed(self, RPM):
        assert self.getVariable('control variables', 'controlMode') in [ControlModes.WHEEL, ControlModes.SPEED], "Control mode set to time"
        assert 0 <= RPM <= 100, "RPM value outside valid range: 0-100"
        self.setVariable('control variables', 'desiredSpeed', int(1023.0 * RPM / 112.83))

    def setGoalPosition(self, goalPosition):
        assert 0 <= goalPosition <= 360, "goalPosition outside valid range: 0-360"
        self.setVariable('control variables', 'goalPosition', int(goalPosition))

    def setTorqueEnable(self, enable): #Clean
        self.setVariable('control variables', 'enable', int(enable))

    def getPosition(self):
        retValue = self.getVariable('feedback variables', 'currentPosition')
        if retValue == None:
            retValue = 0.0
        return retValue

class Claw(Joint):
    def __init__(self, name, ID, cwAngleLimit, ccwAngleLimit, margin, slope, punch, speed, mode):
        super().__init__(name, ID, cwAngleLimit, ccwAngleLimit, margin, slope, punch, speed, mode)

    def open(self):
        self.setGoalPosition(CLAW_OPEN_POS)

    def close(self):
        self.setGoalPosition(CLAW_CLOSE_POS)

class Orion5(object):
    def __init__(self, serialName):
        self.serialLock = threading.Lock()
        self.sendQueue = queue.Queue(QUEUE_LEN)
        self.serial = SerialThread(self, serialName, self.sendQueue, self.serialLock)
        self.serial.start()

        self.base = Joint('base', 1, 0, 359, 1, 100, 0, 20, ControlModes.TIME)
        self.shoulder = Joint('shoulder', 2, 0, 359, 1, 100, 0, 20, ControlModes.TIME)
        self.elbow = Joint('elbow', 3, 0, 359, 1, 100, 0, 20, ControlModes.TIME)
        self.wrist = Joint('wrist', 4, 0, 359, 1, 100, 0, 20, ControlModes.TIME)
        self.claw = Claw('claw', 5, 0, 359, 1, 100, 0, 20, ControlModes.TIME)

        self.joints = [self.base, self.shoulder, self.elbow, self.wrist, self.claw]

        for joint in self.joints:
            joint.init()

    def setJointAngles(self, base, shoulder, elbow, wrist):
        self.base.setGoalPosition(base)
        self.shoulder.setGoalPosition(shoulder)
        self.elbow.setGoalPosition(elbow)
        self.wrist.setGoalPosition(wrist)

    def setJointAnglesArray(self, angles):
        assert 4 <= len(angles) <= 5
        for i in range(len(angles)):
            self.joints[i].setGoalPosition(angles[i])

    def getJointAngles(self):
        return [joint.getPosition() for joint in self.joints]

    def releaseTorque(self):
        for joint in self.joints:
            joint.setTorqueEnable(0)

    def enableTorque(self):
        for joint in self.joints:
            joint.setTorqueEnable(1)

    def setTimeToGoal(self, seconds):
        for joint in self.joints:
            joint.setTimeToGoal(seconds)

    def exit(self):
        debug("Orion5: exit: joining threads")
        if self.serial.running:
            self.sendQueue.join()
        self.serial.stop()
        self.serial.join()
        debug("Orion5: exit: finished")

# LIBRARY FUNCTIONS

def angle2pos(angle):
    return int(angle * 1088 / 360)

def pos2angle(pos):
    return pos * 360.0 / 1088.0

def debug(message):
    if DEBUG:
        timestamp = dt.datetime.now().strftime("%x-%X: ")
        if DEBUG_MODE == "FILE":
            with open('log.txt', 'a') as log:
                log.write(timestamp + message + "\n")
        elif DEBUG_MODE == "PRINT":
            print(timestamp + message)