import serial
import struct
import time


def GetChecksum(packet):
    checksum = 0
    for i in range(2, len(packet)):
        checksum += packet[i]
        if checksum > 0xFF:
            checksum -= 256
    return (~checksum) & 0xFF


def BuildPacket(type1, type2, data):
    # <0xF0> <0xF0> <packetType1> <packetType2> <data 1> ... <data n> <checksum>
    packet = [0xF0, 0xF0, type1, type2]
    for i in range(len(data)):
        packet.append(data[i])
    packet.append(GetChecksum(packet))
    return bytes(packet)


def ProcessRead():
    valid = 0
    state = 0
    reset = 0
    byte = 0
    packetType1 = 0
    packetType2 = 0
    data = []

    while True:

        if s.in_waiting == 0:
            break

        try:
            byte = struct.unpack('B', s.read(1))[0]
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
            # get checksum
            valid = (
            GetChecksum([0xFF, 0xFF, packetType1, packetType2] + data) == byte)
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
        servos[data[0]][data[1]] = value


s = serial.Serial('COM3', 500000, timeout=2, write_timeout=2, writeTimeout=2)

servos = [[0, 0, 0]]

desiredPos = 0
last_time = 0

while 1:
    if time.time() - last_time > 2:
        desiredPos += 108
        desiredPos %= 1088
        s.write(BuildPacket(0x69, 4, [0, 3, (desiredPos & 0xFF),
                                      (desiredPos & 0xFF00) >> 8]))
        last_time = time.time()

    s.write(BuildPacket(0x36, 2, [0, 0]))
    s.write(BuildPacket(0x36, 2, [0, 1]))
    s.write(BuildPacket(0x36, 2, [0, 2]))

    while s.in_waiting >= 8:
        ProcessRead()
    print(servos)
    time.sleep(0.01)

s.close()


