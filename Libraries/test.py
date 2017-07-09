import Orion5
import time

orion = Orion5.Orion5('COM3')

time.sleep(5)

for joint in orion.joints:
    joint.setVariable('control variables', 'enable', 1)
    joint.setVariable('control variables', 'desiredSpeed', 100)

i = 0
desiredPos = [90, 120, 150, 180, 210, 240, 270]
lastTime = 0

while True:
    if time.time() - lastTime > 2:
        orion.wrist.setGoalPosition(desiredPos[i])
        print('move to', desiredPos[i])
        i += 1
        if i >= len(desiredPos):
            i = 0
        lastTime = time.time()

    time.sleep(0.05)

orion.exit()
