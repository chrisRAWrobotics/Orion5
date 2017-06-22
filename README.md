# Orion5

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
