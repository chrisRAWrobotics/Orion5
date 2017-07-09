import Orion5
import time

orion = Orion5.Orion5('COM3')

time.sleep(5)

orion.base.setVariable('control variables', 'enable', 0)

while True:
    time.sleep(0.1)
    print(orion.base.getVariable('feedback variables', 'currentPosition'))

orion.exit()