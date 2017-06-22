import binascii
import struct


# <0000 0000> = 1 byte
# recv packets look like: <jointID errorID> <blank speedH> <speedL> <loadH loadL2> <loadL1 posH> <posL>
# send packets look like: <jointID varID> <varH> <varL>



def uint8_to_byte(u):
    """
    :param i: uint8 number
    :return: byte representation of the number
    """
    return struct.pack('B', u)


def bytes_to_hex_bytes_string(packet):
    """
    Takes a byte string and returns a human readable string of hex bytes
    :param packet: string of bytes
    :return: human readable hex bytes string
    """
    return '0x' + ' 0x'.join([binascii.hexlify(uint8_to_byte(byte)).decode().upper() for byte in packet])


def build_send_packet(jointID, varID, value):
    packet = [0] * 3
    packet[0] = ((jointID & 0x0F) << 4) | (varID & 0x0F)
    packet[1] = ((value & 0xFF00) >> 8)
    packet[2] = (value & 0xFF)
    return bytes(packet)


def build_recv_packet(jointID, errorID, speed, load, pos):
    """
    this function will happen onboard Orion5 in C
    it is here for testing purposes
    """
    packet = [0] * 6
    packet[0] = ((jointID & 0x0F) << 4) | (errorID & 0x0F)
    packet[1] = ((speed & 0x0F00) >> 8)
    packet[2] = (speed & 0xFF)
    packet[3] = ((load & 0x0F00) >> 4) | ((load & 0x00F0) >> 4)
    packet[4] = ((load & 0x000F) << 4) | ((pos & 0x0F00) >> 8)
    packet[5] = (pos & 0xFF)
    return bytes(packet)


def unpack_recv_packet(packet):
    packet = list(packet)
    jointID = ((packet[0] & 0xF0) >> 4)
    errorID = (packet[0] & 0x0F)
    speed = (packet[1] << 8) | packet[2]
    load = (packet[3] << 4) | ((packet[4] & 0xF0) >> 4)
    pos = ((packet[4] & 0x0F) << 8) | packet[5]
    return {'jointID': jointID, 'errorID': errorID, 'speed': speed, 'load': load, 'pos': pos}

if __name__ == '__main__':
    send_packet = build_send_packet(3, 2, 500)
    recv_packet = build_recv_packet(3, 2, 500, 300, 544)
    recv_data = unpack_recv_packet(recv_packet)

    print('send_packet str: {}'.format(send_packet))
    print('send_packet hex: {}\n'.format(bytes_to_hex_bytes_string(send_packet)))

    print('recv_packet str: {}'.format(recv_packet))
    print('recv_packet hex: {}\n'.format(bytes_to_hex_bytes_string(recv_packet)))

    print('recv_data: {}'.format(recv_data))
