import threading
import queue
import serial
import time
import datetime as dt
import copy
import struct

# cool and also nice, not

DEBUG = False
DEBUG_MODE = 'PRINT'

SERIAL_BAUD_RATE = 500000
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

class JointVarsOld:
    CW_LIMIT, CCW_LIMIT, MARGIN, SLOPE, PUNCH, TORQUE_ENABLE,\
        GOAL_POS, SPEED, MODE, CURRENT_POS, CURRENT_SPEED, CURRENT_LOAD, CHECKER = range(13)

class JointVars:
    CURRENT_POS, CURRENT_SPEED, CURRENT_LOAD, GOAL_POS, SPEED, \
        TORQUE_ENABLE, CW_SLOPE, CCW_SLOPE, CW_MARGIN, CCW_MARGIN, \
        PUNCH, CW_LIMIT, CCW_LIMIT, LED, MODE = range(15)

class SerialThread(threading.Thread):
    '''
    Need to create an incoming and outgoing dynamic buffer.
    
    The main loop should first check if the usb is connected, if not then it should attempt connection
    If the main loop is connected, then the main functionality ensues, disconnection should be handled 
    dynamically.
    In the main loop one of the modules should pull all of the incomming USB buffer into the software buffer
    A module after that one should pull all meaningful packets out of the software buffer
    Following this there is the outbound comms...   this will get complex:
    There should be an outgoing buffer, it will be something like [timeout, [bytes]], when a set of bytes 
    is sent through, the timeout is set to current system time or whatever. After this we have almost start 
    condition again; all messages to be sent will be polled up in this buffer, so the main loops requests 
    to the ORION5 will go into here, any checkers to be returned will go into here, etc. If the buffer gets
     larger than 64bytes? then send the first/last... dyslexia 64bytes through and reset the timeout. If
     the timeout value vs the now time exceeds a certain time, then push what is in there through.
     
     The Checker...  The PC will send checker bytes in its packets, they will be handled the same on both 
     pc and ORION5 sides...  When the pc side here receives a packet, it will take the checker and add it
     to a registry of checkers. a seperate module in the main loop called the bureaucrat, will look at this 
     registry and build 'a' packet or multiple packets (if greater than 64bytes or some arbitrary number), 
     of checkerlist packettypes which it will dump into the outbound buffer.
     
     when the pc receives a checkerlist packettype, it will go through the flag variable in the joint 
     dictionaries and
    '''
    def __init__(self, orion5_reference, serialName, sendQueue, lock):
        threading.Thread.__init__(self)
        self._outboxIterator = [['misc variables', [['cwAngleLimit',JointVars.CW_LIMIT],
                                                    ['ccwAngleLimit',JointVars.CCW_LIMIT],
                                                    ['cwMargin', JointVars.CW_MARGIN],
                                                    ['cwwMargin', JointVars.CCW_MARGIN],
                                                    ['cwSlope', JointVars.CW_SLOPE],
                                                    ['cwwSlope', JointVars.CCW_SLOPE],
                                                    ['punch', JointVars.PUNCH]]],
                               ['control variables', [['enable',JointVars.TORQUE_ENABLE],
                                                      ['goalPosition', JointVars.GOAL_POS],
                                                      ['desiredSpeed', JointVars.SPEED],
                                                      ['controlMode', JointVars.MODE]]]]
        self._iter = [0,0,0]
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

    '''def SerialSController(self, Command):
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
            print('yolo')'''

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
        #self.processSend((1, JointVars.CHECKER, self._checker[0], self._checker[0]))
        while self.running:
            # time.sleep(.2)

            self.RequestInfo()

            for i in range(20):
                self._iter[2] += 1
                if len(self._outboxIterator[self._iter[1]][1]) <= self._iter[2]:
                    self._iter[2] = 0
                    self._iter[1] += 1
                    if self._iter[1] > 1:
                        self._iter[1] = 0
                        self._iter[0] += 1
                        if self._iter[0] > 4:
                            self._iter[0] = 0
                jointPTR = self.arm.joints[self._iter[0]]
                itemSETPTR = self._outboxIterator[self._iter[1]]
                itemPTR = self._outboxIterator[self._iter[1]][1][self._iter[2]]
                if jointPTR.checkVariable(itemSETPTR[0], itemPTR[0]):
                    ID = jointPTR.getVariable('constants', 'ID')
                    self.processSend((ID, itemPTR[1], jointPTR.getVariable(itemSETPTR[0], itemPTR[0]), self._checker[0]))
                    break

            while self.uart.in_waiting > 8:
                self.processRead()

    def CheckerAdvance(self):
        # Advance the Checker
        if self._checker[0] >= 255:
            self._checker[0] = 2
        else:
            self._checker[0] += 1

    def processSend(self, command):
        #retValue = True
        #BuildPacket(0x69, 4, [0, 3, (desiredPos & 0xFF), (desiredPos & 0xFF00) >> 8])
        packet = self.BuildPacket(0, 4, [command[0], command[1], (command[2] & 0xFF), (command[2] & 0xFF00) >> 8]) #need to add checker in???  XXXX
        #retValue = retValue and self.sendPacket(packet)
        #packet = self.buildPacket(command)
        retValue = self.sendPacket(packet)
        time.sleep(.01)
        return retValue

    def RequestInfo(self):
        self.sendPacket(self.BuildPacket(1, 2, [0, 0]))
        self.sendPacket(self.BuildPacket(1, 2, [0, 1]))
        self.sendPacket(self.BuildPacket(1, 2, [0, 2]))

    def GetChecksum(self, packet):
        checksum = 0
        for i in range(2, len(packet)):
            checksum += packet[i]
            if checksum > 0xFF:
                checksum -= 256
        return (~checksum) & 0xFF

    def processRead(self):
        valid = 0
        state = 0
        reset = 0
        byte = 0
        packetType1 = 0
        packetType2 = 0
        checker = 0
        data = []

        while True:
            if self.uart.in_waiting == 0:
                break
            try:
                byte = struct.unpack('B', self.uart.read(1))[0]
            except Exception as e:
                print(e)
                print('could not read byte')
                break

            if state < 2:
                # grab header bytes
                if byte == 0xF0:
                    state += 1
                else:
                    reset = 1;
            elif state == 2:
                # grab packet type 1
                packetType1 = byte
                state += 1
            elif state == 3:
                # grab packet type 2
                packetType2 = byte
                state += 1
            elif state == 4:
                # grab data bytes
                if len(data) == packetType2:
                    state += 1
                else:
                    data.append(byte)
            if state == 5:
                checker = byte
                state += 1
            elif state == 6:
                # get checksum
                valid = (self.GetChecksum([0xFF, 0xFF, packetType1, packetType2, checker] + data) == byte)
                if not valid:
                    reset = 1

            if valid:
                break

            if reset:
                # reset state vars
                valid = 0
                state = 0
                reset = 0
                data = []

        if valid:
            value = 0
            if len(data) == 3:
                value = struct.unpack('B', data[2])[0]
            elif len(data) == 4:
                value = struct.unpack('<H', bytes(data[2:4]))[0]

            self.arm.joints[data[0]].setVariable('misc variables', 'error', 0)
            if data[1] == 0:
                self.arm.joints[data[0]].setVariable('feedback variables', 'currentPosition', value)
            elif data[1] == 1:
                self.arm.joints[data[0]].setVariable('feedback variables', 'currentVelocity', value)
            elif data[1] == 2:
                self.arm.joints[data[0]].setVariable('feedback variables', 'currentLoad', value)

    def BuildPacket(self, type, length, data):
        # <0xF0> <0xF0> <packetType1> <packetType2> <data 1> ... <data n> <checksum>
        hexReg = [0x69, 0x36]
        packet = [0xF0, 0xF0, hexReg[type], length]
        for i in range(len(data)):
            packet.append(data[i])
        self.CheckerAdvance()
        packet.append(self._checker[0])
        packet.append(self.GetChecksum(packet))
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
        self.arm.joints[data['jointID']].setVariable('misc variables', 'error', data['errorID'])
        self.arm.joints[data['jointID']].setVariable('feedback variables', 'currentVelocity', data['speed'])
        self.arm.joints[data['jointID']].setVariable('feedback variables', 'currentLoad', data['load'])
        self.arm.joints[data['jointID']].setVariable('feedback variables', 'currentPosition', data['pos'])

class Joint(object):
    def __init__(self, name, ID, cwAngleLimit, ccwAngleLimit, margin, slope, punch, speed, mode):
        # TODO: make all vars private and create getters/setters
        # constants
        self._jointLock = threading.Lock()
        self._datam = {'constants':{'ID':[ID, 1],
                                    'name':[name, 1]},
                       'misc variables':{'cwAngleLimit':[cwAngleLimit, 1],
                                         'ccwAngleLimit':[ccwAngleLimit, 1],
                                         'cwMargin':[margin, 1],
                                         'cwwMargin':[margin, 1],
                                         'cwSlope':[slope, 1],
                                         'cwwSlope':[slope, 1],
                                         'punch':[punch, 1],
                                         'error':[None, 0]},
                       'control variables':{'enable':[0, 1],
                                            'goalPosition':[None, 0],
                                            'desiredSpeed':[speed, 1],
                                            'controlMode':[mode, 1]},
                       'feedback variables':{'currentPosition':[None, 0],
                                             'currentVelocity':[None, 0],
                                             'currentLoad':[None, 0]}}

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
        self._datam[id1][id2] = [datum, 1]
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
        if self._datam[id1][id2][1] == 0:
            self._datam[id1][id2][1] = 1
        else:
            self._datam[id1][id2][1] = 0
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
        self.setVariable('control variables', 'goalPosition', int(goalPosition))

    def setTorqueEnable(self, enable):
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

        self.base = Joint('base', 0, 0, 1087, 1, 100, 0, 20, 0)
        self.shoulder = Joint('shoulder', 1, 0, 359, 1, 100, 0, 20, 0)
        self.elbow = Joint('elbow', 2, 0, 359, 1, 100, 0, 20, 0)
        self.wrist = Joint('wrist', 3, 0, 359, 1, 100, 0, 20, 0)
        self.claw = Claw('claw', 4, 0, 359, 1, 100, 0, 20, 0)

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