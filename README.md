Tools used:
    Github
    Pycharm
Libraries and versions used:
    Python 3.6
    pip
    wheel
    pyserial (just try pip them, I recall having an issue)
    serial (just try pip them, I recall having an issue)
    pyglet

How to install things
Often we have multiple versions of python installed on our computers, so therefore the default 'pip' is always the
    older version of python, which is bloody annoying unless you have unpathed 2.7 and have pathed 3.5/3.6.....    best
    way to be sure is goto the location for IDLE for the version you wish to add libraries (we are working in V3.6),
    go into the scripts folder there and open a command window. Use 'pip install library_name', you'll need a whole bunch,
    your IDE will knock back the ones you need
'pip install pyglet, numpy, scipy, pandas, openG, pyserial, serial'  - not sure whatelse...
    need to come back and edit this

Controls:
    Right - Extends tool point
    Left - Retracts tool point
    Up - Tool point up
    Down - Tool point down
    Home - Attack angle down
    PageUp - Attack angle up
    PageDown - Claw close
    END - Claw open
    Delete - Attack distance out
    Backspace - Attack distance in
    CTRL_Left - Slew left
    CTRL_Right - Slew right
    CTRL_END - Read from arm
    CTRL_HOME - Write to arm
    A - toggle - Put the visualiser into "Arm controls model" mode
    Q - toggle - Put the visualiser into "Model controls arm" mode
MOUSE CONTROLS
    Left click drag rotates model by X/Y axis
    Shift+ Left click drag rotates model by X/Z axis
    Right click drag moves the model around
EXPERIMENTAL BELOW
    D - Record position to current sequence in memory
    E - Force current position to be current sequence element
    S - cycle sequence toward the end (wraps)
    W - Cycle sequence toward the start (wraps)
    C - Save current sequence set to the txt file in the sequence folder TODOs here
    X - Read the sequence in the sequence.txt in the sequence folder TODOs here
    Z - Play sequence currently loaded...  major TODOs as it relies as it needs
        the joint to get within X of angle to tick the sequence as
        having been reached

TODO: collision engine...
To do this I have several ideas in mind, a series of parametric limit fields driven from turret outward, so 5 of them.
First would have no limits... user defined spaces might be possible, but not scalable, best approach is proper STL
collision detection. So TURRET field with no limits.
Then we goto the SHOULDER and it would only have limits when ground was defined and depending on the angle of the
turret as a slice algo with the two 2d shapes of the top of the bases triangle and the outer edge of the arm closest
to it. Shoulder would of course have the limits wherein the gearbox ratio overcomes the position of the shoulder...
complex
Elbow following this would have a limit if the ground was defined.. again solved by plane slices interfacing..   it
would also have a 2d solvable collision limit with the bicep at the elbow...  and the case of the turret would have
to form part of that...
Wrist has the obvious limits with relation to the forearm, also can do slice limits with ground plane, here however
it gets complex with a parametric field against the robot body etc...   really need a proper STL collision system to
solve this properly

hmm, perhaps a nodal system of collision spheres for each 'object', where the first layer is a sphere centered at a
centroid either the normal avg or maybe a best fit sphere. then next layer down is spheres half that size