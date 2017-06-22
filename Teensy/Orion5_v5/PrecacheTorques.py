from math import *

DEG2RAD = 0.0174533
SHOULDERGEARINGMIN = 45
SHOULDERGEARINGMAX = 160
ELBOWMIN = 20
ELBOWMAX = 320
WRISTMIN = 80
WRISTMAX = 280

torque_constants = [0.2324266505, 0.146343472, 0.093242, 0] #// {0.2324266505, 0.146343472, 0.093242, 0}; // XXXX Torque Constants
max_torque = torque_constants[0] + torque_constants[1] + torque_constants[2]
desired_max = 5
desired_min = 0
curve_driver = 30
torque_C2 = (desired_min - curve_driver) / (-max_torque) - (((desired_min - curve_driver) / (-max_torque) - (desired_max - curve_driver) / max_torque) / ((-max_torque) - max_torque)) * (-max_torque)
torque_C3 = ((desired_min - curve_driver) / (-max_torque) - (desired_max - curve_driver) / max_torque) / ((-max_torque) - max_torque)
#Linear Equation Torque*|cosine|*c2 + c1, c1 = desired_min, whole of each summed = desired_max,
# desired_max = Torque[0]*|cosine|*c2 + c1 + Torque[1]*|cosine|*c2 + c1 + Torque[2]*|cosine|*c2 + c1
# desired_max = Torque[0]*|cosine|*c2 + Torque[1]*|cosine|*c2 + Torque[2]*|cosine|*c2 + 3*c1
# desired_max = (Torque[0] + Torque[1] + Torque[2])*|cosine|*c2 + 3*c1
# desired_max - 3*c1 = (Torque[0] + Torque[1] + Torque[2])*|cosine|*c2
# (desired_max - 3*c1)/(Torque[0] + Torque[1] + Torque[2]) = |cosine|*c2, cosine is largest one for each so it is 1
punchC2 = (desired_max - 3*desired_min) /(torque_constants[0]+torque_constants[1]+torque_constants[0])
Slope_Max = 200
Slope_Min = 10
#Slope = C1 + C2*|cosine|*dir**Torque........
#Slope_Max = 3*slopeC1 - slopeC2*(torque_constants[0]+torque_constants[1]+torque_constants[0]), when dir is -1
#Slope_Min = 3*slopeC1 + slopeC2*(torque_constants[0]+torque_constants[1]+torque_constants[0]), when dir is +1
#slopeC1 = (Slope_Max + slopeC2*(torque_constants[0]+torque_constants[1]+torque_constants[0]))/3
#slopeC2 = (Slope_Min - 3*slopeC1)/(torque_constants[0]+torque_constants[1]+torque_constants[0])
#slopeC1 = (Slope_Max
#           + (Slope_Min - 3*slopeC1)
#           / (torque_constants[0]+torque_constants[1]+torque_constants[0])
#           * (torque_constants[0]+torque_constants[1]+torque_constants[0]))/3
#slopeC1 = Slope_Max/3 + Slope_Min/3 - slopeC1
#2 * slopeC1 = Slope_Max/3 + Slope_Min/3
slopeC1 = (Slope_Max/3 + Slope_Min/3) / 2
slopeC2 = (Slope_Min - 3*((Slope_Max/3 + Slope_Min/3) / 2))/(torque_constants[0]+torque_constants[1]+torque_constants[0])


TorqueShoulder = [[],[],[], [], []]
TorqueElbow = [[],[],[], [], []]
TorqueWrist = [[],[],[], [], []]

for i in range(360):
    TorqueShoulder[2].append(int(desired_min + punchC2* abs(cos(DEG2RAD * (i))) * torque_constants[0]))
    TorqueShoulder[3].append(int(slopeC1 + slopeC2 * abs(cos(DEG2RAD * (i))) * torque_constants[0]))
    TorqueShoulder[4].append(int(slopeC1 - slopeC2 * abs(cos(DEG2RAD * (i))) * torque_constants[0]))
for i in range(360):
    TorqueElbow[2].append(int(desired_min + punchC2* abs(cos(DEG2RAD * (i))) * torque_constants[1]))
    TorqueElbow[3].append(int(slopeC1 + slopeC2 * abs(cos(DEG2RAD * (i))) * torque_constants[1]))
    TorqueElbow[4].append(int(slopeC1 - slopeC2 * abs(cos(DEG2RAD * (i))) * torque_constants[1]))
for i in range(360):
    TorqueWrist[2].append(int(desired_min + punchC2* abs(cos(DEG2RAD * (i))) * torque_constants[2]))
    TorqueWrist[3].append(int(slopeC1 + slopeC2 * abs(cos(DEG2RAD * (i))) * torque_constants[2]))
    TorqueWrist[4].append(int(slopeC1 - slopeC2 * abs(cos(DEG2RAD * (i))) * torque_constants[2]))

print(TorqueShoulder[3], '\n')
print(TorqueShoulder[4], '\n')
print(TorqueShoulder[2], '\n')
print(TorqueElbow[3], '\n')
print(TorqueElbow[4], '\n')
print(TorqueElbow[2], '\n')
print(TorqueWrist[3], '\n')
print(TorqueWrist[4], '\n')
print(TorqueWrist[2], '\n')

filePipe = open('TorqueConstants.h', 'w')
filePipe.write('#include <avr/pgmspace.h>\n')

filePipe.write('const PROGMEM  int16_t  PunchShoulder[] = {')
for item in TorqueShoulder[2][:-1]:
	filePipe.write(str(item)+', ')
filePipe.write(str(TorqueShoulder[2][-1])+'};\n')
filePipe.write('const PROGMEM  int16_t  SlopePosShoulder[] = {')
for item in TorqueShoulder[3][:-1]:
	filePipe.write(str(item)+', ')
filePipe.write(str(TorqueShoulder[3][-1])+'};\n')
filePipe.write('const PROGMEM  int16_t  SlopeNegShoulder[] = {')
for item in TorqueShoulder[4][:-1]:
	filePipe.write(str(item)+', ')
filePipe.write(str(TorqueShoulder[4][-1])+'};\n')

filePipe.write('const PROGMEM  int16_t  PunchElbow[] = {')
for item in TorqueElbow[2][:-1]:
	filePipe.write(str(item)+', ')
filePipe.write(str(TorqueElbow[2][-1])+'};\n')
filePipe.write('const PROGMEM  int16_t  SlopePosElbow[] = {')
for item in TorqueElbow[3][:-1]:
	filePipe.write(str(item)+', ')
filePipe.write(str(TorqueElbow[3][-1])+'};\n')
filePipe.write('const PROGMEM  int16_t  SlopeNegElbow[] = {')
for item in TorqueElbow[4][:-1]:
	filePipe.write(str(item)+', ')
filePipe.write(str(TorqueElbow[4][-1])+'};\n')

filePipe.write('const PROGMEM  int16_t  PunchWrist[] = {')
for item in TorqueWrist[2][:-1]:
	filePipe.write(str(item)+', ')
filePipe.write(str(TorqueWrist[2][-1])+'};\n')
filePipe.write('const PROGMEM  int16_t  SlopePosWrist[] = {')
for item in TorqueWrist[3][:-1]:
	filePipe.write(str(item)+', ')
filePipe.write(str(TorqueWrist[3][-1])+'};\n')
filePipe.write('const PROGMEM  int16_t  SlopeNegWrist[] = {')
for item in TorqueWrist[4][:-1]:
	filePipe.write(str(item)+', ')
filePipe.write(str(TorqueWrist[4][-1])+'};\n')

filePipe.close()

