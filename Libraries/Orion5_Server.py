import socket
import select
import Orion5

orion = Orion5.Orion5('COM13')

HOST = 'localhost'
PORT = 42000

max_timeouts = 5
timeouts = 0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

while True:
    print('waiting for connection')
    s.settimeout(None)
    conn, addr = s.accept()
    s.settimeout(0)

    connected = True
    print('connected')

    while connected:
        data = ''

        ready = select.select([conn], [], [], 1)

        if ready[0]:
            data = conn.recv(1024).decode()
        
        if not data or len(data) == 0 or not ready[0]:
            timeouts += 1
            if timeouts > max_timeouts:
                connected = False
                print('timeout')
        else:
            timeouts = 0

            if data == 'p':
                conn.sendall('p'.encode())
            elif data == 'q':
                break
            else:
                data = data.split('+')
                data_dict = {
                    'jointIndex': int(data[0]),
                    'id1': data[1],
                    'id2': data[2]
                }

                if len(data) == 4:
                    orion.joints[data_dict['jointIndex']].setVariable(data_dict['id1'], data_dict['id2'], int(data[3]))
                elif len(data) == 3:
                    var = orion.joints[data_dict['jointIndex']].getVariable(data_dict['id1'], data_dict['id2'])
                    conn.sendall(str(var).encode())

    conn.close()
s.close()
