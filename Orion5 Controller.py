import sys
if not './Libraries/' in sys.path:
    sys.path.append('./Libraries/')
if not './Orion5/' in sys.path:
    sys.path.append('./Orion5/')
from TesselationImportExport import *
from MathADV import *
from pyglet.gl import *
from pyglet.window import key
import Orion5
import copy

print('Controls:\nRight - Extends tool point',
      '\nLeft - Retracts tool point\nUp - Tool point up',
      '\nDown - Tool point down\nHome - Attack angle down',
      '\nPageUp - Attack angle up\nPageDown - Claw close',
      '\nEND - Claw open\nDelete - Attack distance out',
      '\nBackspace - Attack distance in',
      '\nCTRL_Left - Slew left\nCTRL_Right - Slew right',
      '\nCTRL_END - Read from arm',
      '\nCTRL_HOME - Write to arm',
      '\nA - toggle - Put the visualiser into "Arm controls model" mode',
      '\nQ - toggle - Put the visualiser into "Model controls arm" mode',
      '\nMOUSE CONTROLS'
      '\nLeft click drag rotates model by X/Y axis',
      '\nShift+ Left click drag rotates model by X/Z axis',
      '\nRight click drag moves the model around',
      '\nEXPERIMENTAL BELOW',
      '\nD - Record position to current sequence in memory',
      '\nE - Force current position to be current sequence element',
      '\nS - cycle sequence toward the end (wraps)',
      '\nW - Cycle sequence toward the start (wraps)',
      '\nC - Save current sequence set to the txt file in the sequence folder TODOs here',
      '\nX - Read the sequence in the sequence.txt in the sequence folder TODOs here',
      '\nZ - Play sequence currently loaded...  major TODOs as it relies as it needs\n the joint to get within X of angle to tick the sequence as\n having been reached')

ZONEWIDTH = 25
WindowProps = [800, 800]
WINDOW   = [WindowProps[0] + 4 * ZONEWIDTH, WindowProps[1] + 2 * ZONEWIDTH]
INCREMENT = 5
CONTROLZPOSITION = 100
ZONES = {'Y':[0,
              0,
              ZONEWIDTH,
              WINDOW[1] - ZONEWIDTH], #First Zone Left, Y Position
         'X':[0,
              WINDOW[1] - ZONEWIDTH,
              WINDOW[0],
              WINDOW[1]], #Second zone bottom, X Position
         'Claw Open':[ZONEWIDTH,
                      0,
                      ZONEWIDTH*2,
                      WINDOW[1] - 2 * ZONEWIDTH], #Third Zone Second Left, Claw Open?
         'Turret Angle':[ZONEWIDTH,
                         WINDOW[1] - 2 * ZONEWIDTH,
                         WINDOW[0] - ZONEWIDTH,
                         WINDOW[1] - ZONEWIDTH], #Fourth Zone Second from Bottom, Turret Angle
         'Attack Angle':[WINDOW[0] - 2 * ZONEWIDTH,
                         0,
                         WINDOW[0] - ZONEWIDTH,
                         WINDOW[1] - 2 * ZONEWIDTH], #Fifth Zone Second from Right, Attack Angle
         'Attack Depth':[WINDOW[0] - ZONEWIDTH,
                         0,
                         WINDOW[0],
                         WINDOW[1] - ZONEWIDTH]} #Sixth Zone Right, Attack Depth
armConstants = {'X lims':[500.0,1.0,-250.0],
                'Z lims':[500.0,1.0,-250.0],
                'Att Ang Lims':[360.0,1.0,0.0],
                'Att Dep Lims':[500.0,1.0,-250.0],
                'Claw Open Lims':[300.0, 1.0, 120.0],
                'Turr Lims':[360.0,1.0,0.0],
                'Bicep Len':170.384,
                'Forearm Len':136.307,
                'Wrist 2 Claw':85.25}

Models = []
serialPortName = 'COM3'
STLSUBFOLDER =  './STLs'
FILEEXTENSION = 'stl'
fileSets = PullFileNames(FILEEXTENSION, STLSUBFOLDER)
Offsets = [[0.0,0.0,0.0],
           [0.0,0.0,0.0],
           [-30.309,0.0,45.0],
           [-170.384,0.0,0.0],
           [-136.307,0.0,0.0],
           [-136.307,0.0,0.0],
           [-136.307,0.0,0.0]]
Models = PopulateModels(fileSets, Offsets)
arm = None
ORION5 = None
SEQUENCEFOLDER = './Sequences/'
SEQUENCEBASENAME = 'Sequence'
SEQUENCEEXTENSION = '.txt'
MAXSERVOSPEEDS = [{'Turret':200.0,'Shoulder':300.0,'Elbow':400.0,'Wrist':300.0,'Claw':200.0}, ['Turret','Shoulder','Elbow','Wrist','Claw']]

def DifferentialWrapped360(arg1, arg2):
    retValue = arg1-arg2
    if retValue > 180:
        retValue -= 360
    if retValue < -180:
        retValue +=360
    return retValue

class Window(pyglet.window.Window):
    # Cube 3D start rotation
    xRotation = -80
    yRotation = 0
    zRotation = -150
    xOffset = 160
    yOffset = -100
    zOffset = -300
    controlState = [-1, -1, -1, False, False, False, False]
    _servoPositions = {'Turret':180.0,
                       'Shoulder':0.0,
                       'Elbow':0.0,
                       'Wrist':0.0,
                       'Claw':200.0}
    _armVARS = {'X':400.0,
                'Z':50.0,
                'Attack Angle':0.0,
                'Attack Depth':50.0,
                'Wrist Pos':[0.0,0.0,0.0],
                'Elbow Pos':[0.0,0.0,0.0],
                'Shoulder Pos':[-30.309,0.0,45.0],
                'Elbow Angle':0.0}
    arm = None
    _ModelIDs = []
    _ColourBank = []
    _ModelsLen = None
    _Objects = []
    _fileIterator = 0
    _sequenceIterator = -1
    _sequence = []
    _Controls = [['Claw Open',
                  'Attack Angle',
                  'Y',
                  'Attack Depth',
                  'Turret Angle'],
                 []]
    _ControlVars = {'Claw Open':[0,0,CONTROLZPOSITION],
                    'Attack Angle':[0,0,CONTROLZPOSITION],
                    'X':[0,0,CONTROLZPOSITION],
                    'Y':[0,0,CONTROLZPOSITION],
                    'Attack Depth':[0,0,CONTROLZPOSITION],
                    'Turret Angle':[0,0,CONTROLZPOSITION]}

    def __init__(self, width, height, title=''):
        global arm
        super(Window, self).__init__(width, height, title)
        glClearColor(0, 0, 0, 1)
        glEnable(GL_DEPTH_TEST)
        arm = Orion5.Orion5(serialPortName)
        arm.setTimeToGoal(1)
        self.on_text_motion(False)
        self._ModelsLen = len(Models)
        for iterator1 in self._Controls[0]:
            self._Controls[1].append(pyglet.graphics.Batch())
            vertices = [-ZONEWIDTH / 3, -ZONEWIDTH / 3, 0,
                        ZONEWIDTH / 3, -ZONEWIDTH / 3, 0,
                        -ZONEWIDTH / 3, ZONEWIDTH / 3, 0,
                        -ZONEWIDTH / 3, ZONEWIDTH / 3, 0,
                        ZONEWIDTH / 3, -ZONEWIDTH / 3, 0,
                        ZONEWIDTH / 3, ZONEWIDTH / 3, 0]
            normals = [0,0,1,
                       0,0,1]
            indices = 2
            '''self._Controls[1][-1].add_indexed(len(vertices) // 3,
                                          GL_TRIANGLES,
                                          None,  # group,
                                          indices,
                                          ('v3f/static', vertices),
                                          ('n3f/static', normals))'''
        for iterator1 in range(self._ModelsLen):
            self._ModelIDs.append(Models[iterator1][0][2])
            self._ColourBank.append(vec(Models[iterator1][0][3][0], Models[iterator1][0][3][1], Models[iterator1][0][3][2], Models[iterator1][0][3][3]))
            self._Objects.append(pyglet.graphics.Batch())
            vertices = []
            normals = []
            for iterator2 in range(len(Models[iterator1][1])):
                for iterator3 in range(1, 4):
                    vertices.extend(Models[iterator1][1][iterator2][iterator3])
                    normals.extend(Models[iterator1][1][iterator2][0])
            # Create a list of triangle indices.
            indices = range(3 * len(Models[iterator1][1]))  # [[3*i, 3*i+1, 3*i+2] for i in xrange(len(facets))]
            self._Objects[-1].add_indexed(len(vertices) // 3,
                                                 GL_TRIANGLES,
                                                 None,  # group,
                                                 indices,
                                                 ('v3f/static', vertices),
                                                 ('n3f/static', normals))
        pyglet.clock.schedule_interval(self.update, 1 / 30.0)

    def on_resize(self, width, height):
        # set the Viewport
        glViewport(0, 0, width, height)
        # using Projection mode
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspectRatio = width / height
        gluPerspective(35, aspectRatio, 1, 1000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -500)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.zOffset += scroll_y*10

    def on_mouse_press(self, x, y, button, modifiers):
        self.controlState[0] = button
        self.controlState[2] = modifiers
        self.controlState[1] = 2#iterator1
        '''for iterator1 in range(len(ZONES)):
            if ((x > ZONES[iterator1][0])
                and (x < ZONES[iterator1][2])
                and (y > ZONES[iterator1][1])
                and (y < ZONES[iterator1][3])):
                self.controlState[1] = iterator1'''

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if (self.controlState[0] == 1
            and self.controlState[1] == 2):
            self.xRotation -= dy * 0.25
            if self.controlState[2] == 0:
                self.yRotation += dx * 0.25
            else:
                self.zRotation += dx * 0.25
        if (self.controlState[0] == 4
            and self.controlState[1] == 2):
            self.xOffset += dx * .5
            self.yOffset += dy * .5

    def on_mouse_release(self, x, y, button, modifiers):
        self.controlState[0] = -1
        self.controlState[1] = -1
        self.controlState[2] = -1

    def on_key_press(self, symbol, modifiers):
        if symbol == key.Q:
            self.controlState[3] = not self.controlState[3]
            if self.controlState[3]:
                arm.enableTorque()
            else:
                arm.releaseTorque()
        elif symbol == key.A:
            self.controlState[4] = not self.controlState[4]
        elif symbol == key.E:
            if len(self._sequence) != 0:
                #Show entry toggle
                self.controlState[5] = not self.controlState[5]
                print(self._sequenceIterator, self._sequence[self._sequenceIterator])
        elif symbol == key.W:
            if len(self._sequence) != 0:
                self._sequenceIterator -= 1
            if self._sequenceIterator < -1:
                self._sequenceIterator = len(self._sequence)-2
            print(self._sequenceIterator, self._sequence[self._sequenceIterator])
        elif symbol == key.S:
            if len(self._sequence) != 0:
                self._sequenceIterator += 1
            if self._sequenceIterator > len(self._sequence)-2:
                self._sequenceIterator = -1
            print(self._sequenceIterator, self._sequence[self._sequenceIterator])
        elif symbol == key.D:
            # record entry
            self._sequence.append([['Turret', copy.copy(self._servoPositions['Turret'])],
                                   ['Shoulder', copy.copy(self._servoPositions['Shoulder'])],
                                   ['Elbow', copy.copy(self._servoPositions['Elbow'])],
                                   ['Wrist', copy.copy(self._servoPositions['Wrist'])],
                                   ['Claw', copy.copy(self._servoPositions['Claw'])]])
        elif symbol == key.Z:
            if len(self._sequence) != 0:
                #run sequence toggle
                self.controlState[6] = not self.controlState[6]
                if self.controlState[6]:
                    self.controlState[5] = True
                print(self._sequenceIterator, self._sequence[self._sequenceIterator])
        elif symbol == key.X:
            try:
                ID = ''
                entry = ''
                entryList = []
                self._sequence = []
                filePipe = open(SEQUENCEFOLDER + SEQUENCEBASENAME + SEQUENCEEXTENSION, 'r')
                while True:
                    entryList = []
                    entry = filePipe.readline()
                    if entry == '':
                        filePipe.close()
                        break
                    else:
                        for iterator in range(5):
                            ID = entry[:entry.find(' ')]
                            entry = entry[entry.find(' ')+1:]
                            entryList.append([ID, float(entry[:entry.find(' ')])])
                            entry = entry[entry.find(' ') + 1:]
                        self._sequence.append(entryList)
            except:
                print('File does not exist')
            print(self._sequence)
        elif symbol == key.C:
            if len(self._sequence) != 0:
                filePipe = open(SEQUENCEFOLDER + SEQUENCEBASENAME + SEQUENCEEXTENSION, 'w')
                for itemSet in self._sequence:
                    for item in itemSet:
                        filePipe.write(item[0]+' '+str(item[1])+' ')
                    filePipe.write('\n')
                filePipe.close()
        elif symbol == key.ESCAPE:
            self.controlState = [-1, -1, -1, False, False, False, False]
            arm.releaseTorque()
            pyglet.app.exit()

    def update(self, yoyo):
        if self.controlState[4]:
            self._servoPositions['Turret'] = -arm.base.getPosition()
            self._servoPositions['Shoulder'] = arm.shoulder.getPosition()
            self._servoPositions['Elbow'] = arm.elbow.getPosition()
            self._servoPositions['Wrist'] = arm.wrist.getPosition()
            self._servoPositions['Claw'] = arm.claw.getPosition()
        elif self.controlState[5]:
            self._servoPositions['Turret'] = copy.copy(self._sequence[self._sequenceIterator][0][1])
            self._servoPositions['Shoulder'] = copy.copy(self._sequence[self._sequenceIterator][1][1])
            self._servoPositions['Elbow'] = copy.copy(self._sequence[self._sequenceIterator][2][1])
            self._servoPositions['Wrist'] = copy.copy(self._sequence[self._sequenceIterator][3][1])
            self._servoPositions['Claw'] = copy.copy(self._sequence[self._sequenceIterator][4][1])

        if ((self.controlState[4] or self.controlState[5]) and self._servoPositions['Turret'] != None):
            self._armVARS['Elbow Angle'] = self._servoPositions['Elbow'] + self._servoPositions['Shoulder'] - 180.0
            self._armVARS['Attack Angle'] = self._servoPositions['Wrist'] - 180.0 + self._armVARS['Elbow Angle']
            self._armVARS['Elbow Pos'][0] = self._armVARS['Shoulder Pos'][0] + pol2rect(-armConstants['Bicep Len'],-self._servoPositions['Shoulder'], True)
            self._armVARS['Elbow Pos'][2] = self._armVARS['Shoulder Pos'][2] + pol2rect(-armConstants['Bicep Len'],-self._servoPositions['Shoulder'], False)
            self._armVARS['Wrist Pos'][0] = self._armVARS['Elbow Pos'][0] - pol2rect(armConstants['Forearm Len'],-self._armVARS['Elbow Angle'],True)
            self._armVARS['Wrist Pos'][2] = self._armVARS['Elbow Pos'][2] - pol2rect(armConstants['Forearm Len'],-self._armVARS['Elbow Angle'],False)
            self._armVARS['X'] = -self._armVARS['Wrist Pos'][0] + pol2rect((85.25 + self._armVARS['Attack Depth']),self._armVARS['Attack Angle'], True)
            self._armVARS['Z'] = self._armVARS['Wrist Pos'][2] + pol2rect((85.25 + self._armVARS['Attack Depth']),self._armVARS['Attack Angle'], False)

        if self.controlState[6]:
            #sequencer
            if (abs(DifferentialWrapped360(self._servoPositions['Turret'], -arm.base.getPosition()))
                    + abs(DifferentialWrapped360(self._servoPositions['Shoulder'], arm.shoulder.getPosition()))
                    + abs(DifferentialWrapped360(self._servoPositions['Elbow'], arm.elbow.getPosition()))
                    + abs(DifferentialWrapped360(self._servoPositions['Wrist'], arm.wrist.getPosition()))
                    + abs(DifferentialWrapped360(self._servoPositions['Claw'], arm.claw.getPosition()))) < 12:
                self._sequenceIterator += 1
                if self._sequenceIterator > len(self._sequence) - 2: #yo
                    self._sequenceIterator = -1
            '''else:
                print(abs(DifferentialWrapped360(self._servoPositions['Turret'], -arm.base.getPosition()))
                    , abs(DifferentialWrapped360(self._servoPositions['Shoulder'], arm.shoulder.getPosition()))
                    , abs(DifferentialWrapped360(self._servoPositions['Elbow'], arm.elbow.getPosition()))
                    , abs(DifferentialWrapped360(self._servoPositions['Wrist'], arm.wrist.getPosition()))
                    , abs(DifferentialWrapped360(self._servoPositions['Claw'], arm.claw.getPosition())))'''

        if (not self.controlState[4] and self.controlState[3]):
            temp = [abs(self._servoPositions['Turret'] + arm.base.getPosition()) / MAXSERVOSPEEDS[0]['Turret'],
                    abs(self._servoPositions['Shoulder'] - arm.shoulder.getPosition()) / MAXSERVOSPEEDS[0]['Shoulder'],
                    abs(self._servoPositions['Elbow'] - arm.elbow.getPosition()) / MAXSERVOSPEEDS[0]['Elbow'],
                    abs(self._servoPositions['Wrist'] - arm.wrist.getPosition()) / MAXSERVOSPEEDS[0]['Wrist'],
                    abs(self._servoPositions['Claw'] - arm.claw.getPosition()) / MAXSERVOSPEEDS[0]['Claw']]
            maxSpeed = 0
            for item in temp:
                if item > maxSpeed:
                    maxSpeed = 0.0 + item
            arm.setTimeToGoal(maxSpeed)
            arm.base.setGoalPosition(wrap360(-self._servoPositions['Turret']))
            arm.shoulder.setGoalPosition(wrap360(self._servoPositions['Shoulder']))
            arm.elbow.setGoalPosition(wrap360(self._servoPositions['Elbow']))
            arm.wrist.setGoalPosition(wrap360(self._servoPositions['Wrist']))
            arm.claw.setGoalPosition(wrap360(self._servoPositions['Claw']))

    def on_draw(self):
        global arm
        # Clear the current GL Window
        self.clear()
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        '''for item in self._Controls[1]:
            item.draw()'''
        for iterator1 in range(self._ModelsLen):
            glLoadIdentity()
            glTranslatef(self.xOffset, self.yOffset, self.zOffset-650)
            glRotatef(self.xRotation, 1, 0, 0)
            glRotatef(self.yRotation, 0, 1, 0)
            glRotatef(self.zRotation, 0, 0, 1)

            #Turret Rotate
            if self._ModelIDs[iterator1] > 0:
                glRotatef(self._servoPositions['Turret'], 0, 0, 1)

            #Part Move
            if self._ModelIDs[iterator1] == 2:
                glTranslatef(self._armVARS['Shoulder Pos'][0], self._armVARS['Shoulder Pos'][1], self._armVARS['Shoulder Pos'][2])
            elif self._ModelIDs[iterator1] == 3:
                glTranslatef(self._armVARS['Elbow Pos'][0], self._armVARS['Elbow Pos'][1], self._armVARS['Elbow Pos'][2])
            elif self._ModelIDs[iterator1] == 4:
                glTranslatef(self._armVARS['Wrist Pos'][0], self._armVARS['Wrist Pos'][1], self._armVARS['Wrist Pos'][2])
            elif self._ModelIDs[iterator1] == 5:
                glTranslatef(self._armVARS['Wrist Pos'][0], - (self._servoPositions['Claw'] - 120) / 7.2, self._armVARS['Wrist Pos'][2])
            elif self._ModelIDs[iterator1] == 6:
                glTranslatef(self._armVARS['Wrist Pos'][0], (self._servoPositions['Claw'] - 120) / 7.2, self._armVARS['Wrist Pos'][2])

            #Part Rotate
            if self._ModelIDs[iterator1] > 3:
                glRotatef(self._armVARS['Attack Angle'], 0, 1, 0)
            elif self._ModelIDs[iterator1] == 2:
                glRotatef(self._servoPositions['Shoulder'], 0, 1, 0)
            elif self._ModelIDs[iterator1] == 3:
                glRotatef(self._armVARS['Elbow Angle'], 0, 1, 0)

            #Draw the Thing
            glMaterialfv(GL_FRONT, GL_AMBIENT, self._ColourBank[iterator1])
            self._Objects[iterator1].draw()

    def on_text_motion(self, motion, BLAH = False):
        global arm
        #Check the keypress
        if motion == key.MOTION_END_OF_LINE:
            self._servoPositions['Claw'] += armConstants['Claw Open Lims'][1]
            if self._servoPositions['Claw'] > armConstants['Claw Open Lims'][0]:
                self._servoPositions['Claw'] = armConstants['Claw Open Lims'][0]
        elif motion == key.MOTION_NEXT_PAGE:
            self._servoPositions['Claw'] -= armConstants['Claw Open Lims'][1]
            if self._servoPositions['Claw'] < armConstants['Claw Open Lims'][2]:
                self._servoPositions['Claw'] = armConstants['Claw Open Lims'][2]
        elif motion == key.MOTION_UP:
            self._armVARS['Z'] += armConstants['Z lims'][1]
            if self._armVARS['Z'] > armConstants['Z lims'][0]:
                self._armVARS['Z'] = armConstants['Z lims'][0]
        elif motion == key.MOTION_DOWN:
            self._armVARS['Z'] -= armConstants['Z lims'][1]
            if self._armVARS['Z'] < armConstants['Z lims'][2]:
                self._armVARS['Z'] = armConstants['Z lims'][2]
        elif motion == key.MOTION_LEFT:
            self._armVARS['X'] -= armConstants['X lims'][1]
            if self._armVARS['X'] < armConstants['X lims'][2]:
                self._armVARS['X'] = armConstants['X lims'][2]
        elif motion == key.MOTION_RIGHT:
            self._armVARS['X'] += armConstants['X lims'][1]
            if self._armVARS['X'] > armConstants['X lims'][0]:
                self._armVARS['X'] = armConstants['X lims'][0]
        elif motion == key.MOTION_PREVIOUS_WORD:
            self._servoPositions['Turret'] += armConstants['Turr Lims'][1]
            if self._servoPositions['Turret'] > armConstants['Turr Lims'][0]:
                self._servoPositions['Turret'] -= armConstants['Turr Lims'][0]
        elif motion == key.MOTION_NEXT_WORD:
            self._servoPositions['Turret'] -= armConstants['Turr Lims'][1]
            if self._servoPositions['Turret'] < armConstants['Turr Lims'][2]:
                self._servoPositions['Turret'] += armConstants['Turr Lims'][0]
        elif motion == key.MOTION_PREVIOUS_PAGE:
            self._armVARS['Attack Angle'] -= armConstants['Att Ang Lims'][1]
            if self._armVARS['Attack Angle'] < armConstants['Att Ang Lims'][2]:
                self._armVARS['Attack Angle'] += armConstants['Att Ang Lims'][0]
        elif motion == key.MOTION_BEGINNING_OF_LINE:
            self._armVARS['Attack Angle'] += armConstants['Att Ang Lims'][1]
            if self._armVARS['Attack Angle'] > armConstants['Att Ang Lims'][0]:
                self._armVARS['Attack Angle'] -= armConstants['Att Ang Lims'][0]
        elif motion == key.MOTION_BACKSPACE:
            self._armVARS['Attack Depth'] += armConstants['Att Dep Lims'][1]
            if self._armVARS['Attack Depth'] > armConstants['Att Dep Lims'][0]:
                self._armVARS['Attack Depth'] = armConstants['Att Dep Lims'][0]
        elif motion == key.MOTION_DELETE:
            self._armVARS['Attack Depth'] -= armConstants['Att Dep Lims'][1]
            if self._armVARS['Attack Depth'] < armConstants['Att Dep Lims'][2]:
                self._armVARS['Attack Depth'] = armConstants['Att Dep Lims'][2]

        if self._servoPositions['Turret'] != None:
            # Find the Wrist Point
            self._armVARS['Wrist Pos'][0] = -self._armVARS['X'] + pol2rect((85.25 + self._armVARS['Attack Depth']) , self._armVARS['Attack Angle'], True)
            self._armVARS['Wrist Pos'][2] = self._armVARS['Z'] - pol2rect((85.25 + self._armVARS['Attack Depth']) , self._armVARS['Attack Angle'], False)
            # Check 1 if wrist is too far from shoulder

            b = math.sqrt((abs(self._armVARS['Wrist Pos'][0] - self._armVARS['Shoulder Pos'][0]) ** 2.0) + (abs(self._armVARS['Wrist Pos'][2] - self._armVARS['Shoulder Pos'][2]) ** 2.0))
            if b > (armConstants['Forearm Len'] + armConstants['Bicep Len']):
                self._armVARS['Elbow Pos'][0] = self._armVARS['Shoulder Pos'][0] + (armConstants['Bicep Len'] * (self._armVARS['Wrist Pos'][0] - self._armVARS['Shoulder Pos'][0]) / b)
                self._armVARS['Elbow Pos'][2] = self._armVARS['Shoulder Pos'][2] + (armConstants['Bicep Len'] * (self._armVARS['Wrist Pos'][2] - self._armVARS['Shoulder Pos'][2]) / b)
                self._armVARS['Wrist Pos'][0] = self._armVARS['Shoulder Pos'][0] + ((armConstants['Forearm Len'] + armConstants['Bicep Len']) * (self._armVARS['Wrist Pos'][0] - self._armVARS['Shoulder Pos'][0]) / b)
                self._armVARS['Wrist Pos'][2] = self._armVARS['Shoulder Pos'][2] + ((armConstants['Forearm Len'] + armConstants['Bicep Len']) * (self._armVARS['Wrist Pos'][2] - self._armVARS['Shoulder Pos'][2]) / b)
                self._armVARS['X'] = -self._armVARS['Wrist Pos'][0] + pol2rect((85.25 + self._armVARS['Attack Depth']), self._armVARS['Attack Angle'], True)
                self._armVARS['Z'] = self._armVARS['Wrist Pos'][2] + pol2rect((85.25 + self._armVARS['Attack Depth']), self._armVARS['Attack Angle'], False)
                self._servoPositions['Shoulder'] = 180.0 - rect2pol(self._armVARS['Wrist Pos'][0] - self._armVARS['Shoulder Pos'][0], self._armVARS['Wrist Pos'][2] - self._armVARS['Shoulder Pos'][2], False)
                self._armVARS['Elbow Angle'] = 0.0 + self._servoPositions['Shoulder']
            else:
                self._servoPositions['Shoulder'] = 180.0 - rect2pol(self._armVARS['Wrist Pos'][0] - self._armVARS['Shoulder Pos'][0], self._armVARS['Wrist Pos'][2] - self._armVARS['Shoulder Pos'][2], False) + math.acos(((b ** 2.0) + (armConstants['Bicep Len'] ** 2.0) - (armConstants['Forearm Len'] ** 2.0)) / (2.0 * b * armConstants['Bicep Len'])) * 180.0 / math.pi
                self._armVARS['Elbow Angle'] = self._servoPositions['Shoulder'] - 180 + math.acos(((armConstants['Forearm Len'] ** 2) + (armConstants['Bicep Len'] ** 2) - (b ** 2)) / (2 * armConstants['Forearm Len'] * armConstants['Bicep Len'])) * 180.0 / math.pi
                self._armVARS['Elbow Pos'][0] = self._armVARS['Shoulder Pos'][0] - pol2rect(armConstants['Bicep Len'] , -self._servoPositions['Shoulder'], True)
                self._armVARS['Elbow Pos'][2] = self._armVARS['Shoulder Pos'][2] - pol2rect(armConstants['Bicep Len'] , -self._servoPositions['Shoulder'], False)

            self._servoPositions['Shoulder'] = 0.0 + self._servoPositions['Shoulder']
            self._servoPositions['Elbow'] = self._armVARS['Elbow Angle'] - self._servoPositions['Shoulder'] + 180.0
            self._servoPositions['Wrist'] = self._armVARS['Attack Angle'] - self._armVARS['Elbow Angle'] + 180.0

def Main():
    global ORION5
    ORION5 = Window(WINDOW[0], WINDOW[1], 'Orion5 Visualiser and Controller')
    pyglet.app.run()

if __name__ == '__main__':
    Main()
arm.exit()