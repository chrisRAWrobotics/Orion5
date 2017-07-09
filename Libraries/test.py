import Orion5
import time

orion = Orion5.Orion5('COM3')
orion.base.setVariable('control variables', 'enable', 1)

currentPos = 0
desiredPos = 0
lastTime = 0
count = 0

while count < 10:
    if time.time() - lastTime > 2:
        desiredPos += 108
        desiredPos %= 1088
        orion.base.setVariable('control variables', 'goalPosition', desiredPos)
        print('move to', desiredPos)
        lastTime = time.time()
        count += 1

    newCurrentPos = orion.base.getVariable('feedback variables', 'currentPosition')
    if newCurrentPos != currentPos:
        currentPos = newCurrentPos
        print(currentPos)

    time.sleep(0.01)

orion.exit()
