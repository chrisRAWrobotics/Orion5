# Orion5

## MATLAB Library
Libraries directory contains `Orion5.m`, this MATLAB library interfaces with a Python server that will need to be launched before using the MATLAB library.
1. Install dependencies for Python server using `pip3 install pyserial`.
2. Launch the Python server using `python3 Orion5_Server.py`.
3. Now when the `Orion5.m` class is used in MATLAB it will interface with Python.

### Basic Usage
MATLAB library is still under development and robustness of interface will improve in a future revision.  
The library pings the Python server every second if no other library functions are being called, this is like a watchdog timer, if Python server doesn't hear anything for 5 seconds, it will return to waiting for a new connection.  
The MATLAB script `test_script.m` demonstrates some of the functionality.

#### Create an instance of the library
```matlab
orion = Orion5()
```

#### Read a joint position
This will return an angle in degrees in the range 0-359
```matlab
shoulder_pos = orion.getJointPosition(Orion5.SHOULDER)
```

#### Set a joint position
This takes an angle in degrees in the range 0-359
```matlab
orion.setJointPosition(Orion5.ELBOW, 135)
```

#### Set a time to position
This function will set the speed such that the joint will arrive at the goal position in `time` seconds
```matlab
orion.setJointTimeToPosition(Orion5.SHOULDER, time)
```

#### Turn on/off torque
```matlab
% turn on
orion.setJointTorqueEnable(Orion5.WRIST, 1)

% turn off
orion.setJointTorqueEnable(Orion5.BASE, 0)
```

### Issues
* If MATLAB code calling the library crashes, the *keep alive* ping will keep happening in the background. Can stop this by running `<library_instance>.stop()` in MATLAB console.
* Not all functionality is present yet, however structure is in place ready for this development.
* Values are only in units of degrees from 0-360, future revision will allow radians and negative angles.

## Python Visualiser Controller

### Libraries and versions used:
* Python 3.6
* pip
* wheel
* pyserial
* pyglet
* numpy
* scipy

### How to install things
Often we have multiple versions of python installed on our computers, so therefore the default 'pip' is always the older version of python, which is annoying.
Best way to be sure is goto the location of IDLE for the version you wish to add libraries (we are working in Python 3.6), go into the scripts folder there and open a command window `pip install <library_name>`

```
pip install wheel, pyglet, numpy, scipy, pyserial
```

### Controls:
* Right - Extends tool point
* Left - Retracts tool point
* Up - Tool point up
* Down - Tool point down
* Home - Attack angle down
* PageUp - Attack angle up
* PageDown - Claw close
* END - Claw open
* Delete - Attack distance out
* Backspace - Attack distance in
* CTRL_Left - Slew left
* CTRL_Right - Slew right
* CTRL_END - Read from arm
* CTRL_HOME - Write to arm
* A - toggle - Put the visualiser into "Arm controls model" mode
* Q - toggle - Put the visualiser into "Model controls arm" mode

### Mouse Controls
* Left click drag rotates model by X/Y axis
* Shift + Left click drag rotates model by X/Z axis
* Right click drag pans the model around

### Experimental Controls
* D - Record position to current sequence in memory
* E - Force current position to be current sequence element
* S - cycle sequence toward the end (wraps)
* W - Cycle sequence toward the start (wraps)
* C - Save current sequence set to the txt file in the sequence folder TODOs here
* X - Read the sequence in the sequence.txt in the sequence folder TODOs here
* Z - Play sequence currently loaded... Major TODOs as it relies as it needs the joint to get within X of angle to tick the sequence as having been reached
