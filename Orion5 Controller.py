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

print('KEYBOARD CONTROLS:',
      '\n   Right - Extends tool point',
      '\n   Left - Retracts tool point\nUp - Tool point up',
      '\n   Down - Tool point down\nHome - Attack angle down',
      '\n   PageUp - Attack angle up\nPageDown - Claw close',
      '\n   END - Claw open\nDelete - Attack distance out',
      '\n   Backspace - Attack distance in',
      '\n   CTRL_Left - Slew left\nCTRL_Right - Slew right',
      '\n   CTRL_END - Read from arm',
      '\n   CTRL_HOME - Write to arm',
      '\n   A - toggle - Put the visualiser into "Arm controls model" mode',
      '\n   Q - toggle - Put the visualiser into "Model controls arm" mode',
      '\nMOUSE CONTROLS',
      '\n   Left click drag rotates model by X/Y axis',
      '\n   Shift+ Left click drag rotates model by X/Z axis',
      '\n   Right click drag moves the model around',
      '\nEXPERIMENTAL BELOW',
      '\n   D - Record position to current sequence in memory',
      '\n   E - Force current position to be current sequence element',
      '\n   S - cycle sequence toward the end (wraps)',
      '\n   W - Cycle sequence toward the start (wraps)',
      '\n   C - Save current sequence set to the txt file in the sequence folder TODOs here',
      '\n   X - Read the sequence in the sequence.txt in the sequence folder TODOs here',
      '\n   Z - Play sequence currently loaded...  major TODOs as it relies as it needs',
      '\n       the joint to get within X of angle to tick the sequence as having been reached')

ZONEWIDTH = 25
WindowProps = [800, 600]
WINDOW   = [WindowProps[0] + 4 * ZONEWIDTH, WindowProps[1] + 2 * ZONEWIDTH]
INCREMENT = 5
CONTROLZPOSITION = -100
CONTROLSCALER = 0.097
CONTROLSIZE = ZONEWIDTH*CONTROLSCALER

ZONES = [['Claw',[WINDOW[0] - ZONEWIDTH,
                       ZONEWIDTH,
                       WINDOW[0],
                       WINDOW[1]],
          [0,0]],  #Third Zone Second Left, Claw Open?
         ['Attack Angle', [ZONEWIDTH,
                           2 * ZONEWIDTH,
                           2 * ZONEWIDTH,
                           WINDOW[1]],
          [0,0]],  # Fifth Zone Second from Right, Attack Angle
         ['X', [0,
                0,
                WINDOW[0],
                ZONEWIDTH],
          [0,0]],  # Second zone bottom, X Position
         ['Y',[0,
               ZONEWIDTH,
               ZONEWIDTH,
               WINDOW[1]],
          [0,0]],  #First Zone Left, Y Position
         ['Attack Depth', [WINDOW[0] - 2 * ZONEWIDTH,
                           2 * ZONEWIDTH,
                           WINDOW[0] - ZONEWIDTH,
                           WINDOW[1]],
          [0,0]], #Sixth Zone Right, Attack Depth
         ['Turret',[ZONEWIDTH,
                          ZONEWIDTH,
                          WINDOW[0] - ZONEWIDTH,
                          2 * ZONEWIDTH],
          [0,0]]]  #Fourth Zone Second from Bottom, Turret Angle
armConstants = {'X lims':[500.0,1.0,-250.0, False],
                'Z lims':[500.0,1.0,-250.0, False],
                'Attack Angle lims':[360.0,1.0,0.0, True],
                'Attack Depth lims':[500.0,1.0,-250.0, False],
                'Claw lims':[300.0, 1.0, 120.0, False],
                'Turret lims':[360.0,1.0,0.0, True],
                'Shoulder lims':[360.0,1.0,0.0, True],
                'Bicep lims':[360.0,1.0,0.0, True],
                'Wrist lims':[360.0,1.0,0.0, True],
                'Bicep Len':170.384,
                'Forearm Len':136.307,
                'Wrist 2 Claw':85.25,
                'Key IDs':[[key.MOTION_END_OF_LINE, 'Claw', True],
                           [key.MOTION_NEXT_PAGE, 'Claw', False],
                           [key.MOTION_UP, 'Z', True],
                           [key.MOTION_DOWN, 'Z', False],
                           [key.MOTION_LEFT,'X', True],
                           [key.MOTION_RIGHT, 'X', False],
                           [key.MOTION_PREVIOUS_WORD,'Turret', True],
                           [key.MOTION_NEXT_WORD,'Turret', False],
                           [key.MOTION_PREVIOUS_PAGE,'Attack Angle', True],
                           [key.MOTION_BEGINNING_OF_LINE,'Attack Angle', False],
                           [key.MOTION_BACKSPACE,'Attack Depth', True],
                           [key.MOTION_DELETE,'Attack Depth', False]]}

Models = []
serialPortName = 'COM8'
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

#Hah

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
    _MousePos = [0,0]
    _armVARS = {'X':400.0,
                'Z':50.0,
                'Attack Angle':0.0,
                'Attack Depth':50.0,
                'Wrist Pos':[0.0,0.0,0.0],
                'Elbow Pos':[0.0,0.0,0.0],
                'Shoulder Pos':[-30.309,0.0,45.0],
                'Elbow Angle':0.0,
                'Turret': 180.0,
                'Shoulder': 0.0,
                'Elbow': 0.0,
                'Wrist': 0.0,
                'Claw': 200.0}
    arm = None
    _ModelIDs = []
    _ColourBank = []
    _ModelsLen = None
    _Objects = []
    _fileIterator = 0
    _sequenceIterator = -1
    _sequence = []
    _Controls = [['Claw',
                  'Attack Angle',
                  'X',
                  'Y',
                  'Attack Depth',
                  'Turret'],
                 [],
                 [[0, 0, True, key.MOTION_END_OF_LINE, key.MOTION_NEXT_PAGE],
                  [0, 0, True, key.MOTION_PREVIOUS_PAGE, key.MOTION_BEGINNING_OF_LINE],
                  [0, 0, False, key.MOTION_LEFT, key.MOTION_RIGHT],
                  [0, 0, True, key.MOTION_UP, key.MOTION_DOWN],
                  [0, 0, True, key.MOTION_BACKSPACE, key.MOTION_DELETE],
                  [0, 0, False, key.MOTION_PREVIOUS_WORD, key.MOTION_NEXT_WORD]]]
    _ControlVars = {'Claw':[(WINDOW[0]/2)-ZONEWIDTH/2,
                                 (ZONEWIDTH - WINDOW[1] / 2) + ZONEWIDTH / 2,
                                 0,
                                 abs((ZONEWIDTH - WINDOW[1] / 2) + ZONEWIDTH/2)*2 + ZONEWIDTH,
                                 armConstants['Claw lims'][2],
                                 armConstants['Claw lims'][0]-armConstants['Claw lims'][2],
                                 'Claw',
                                 0],
                    'Attack Angle':[(ZONEWIDTH-WINDOW[0]/2)+ZONEWIDTH/2,
                                    (2 * ZONEWIDTH - WINDOW[1] / 2) + ZONEWIDTH / 2,
                                    0,
                                    abs((2 * ZONEWIDTH - WINDOW[1] / 2) + ZONEWIDTH / 2)*2 + 2 * ZONEWIDTH,
                                    armConstants['Attack Angle lims'][2],
                                    armConstants['Attack Angle lims'][0] - armConstants['Attack Angle lims'][2],
                                    'Attack Angle',
                                    .5],
                    'X':[(-WINDOW[0]/2)+ZONEWIDTH/2,
                         (-WINDOW[1]/2)+ZONEWIDTH/2,
                         abs((-WINDOW[0]/2)+ZONEWIDTH/2)*2,
                         0,
                         armConstants['X lims'][2],
                         armConstants['X lims'][0] - armConstants['X lims'][2],
                         'X',
                         0],
                    'Y':[(-WINDOW[0]/2)+ZONEWIDTH/2,
                         (ZONEWIDTH - WINDOW[1] / 2) + ZONEWIDTH / 2,
                         0,
                         abs((ZONEWIDTH - WINDOW[1] / 2) + ZONEWIDTH / 2)*2 + ZONEWIDTH,
                         armConstants['Z lims'][2],
                         armConstants['Z lims'][0] - armConstants['Z lims'][2],
                         'Z',
                         0],
                    'Attack Depth':[(WINDOW[0]/2-ZONEWIDTH)-ZONEWIDTH/2,
                                    (2*ZONEWIDTH-WINDOW[1] / 2) + ZONEWIDTH / 2,
                                    0,
                                    abs((2*ZONEWIDTH-WINDOW[1] / 2) + ZONEWIDTH / 2)*2 + 2 * ZONEWIDTH,
                                    armConstants['Attack Depth lims'][2],
                                    armConstants['Attack Depth lims'][0] - armConstants['Attack Depth lims'][2],
                                    'Attack Depth',
                                    0],
                    'Turret':[(ZONEWIDTH-WINDOW[0]/2)+ZONEWIDTH/2,
                                    (ZONEWIDTH-WINDOW[1]/2)+ZONEWIDTH/2,
                                    abs((ZONEWIDTH - WINDOW[0] / 2) + ZONEWIDTH / 2) * 2,
                                    0,
                                    armConstants['Turret lims'][2],
                                    armConstants['Turret lims'][0] - armConstants['Turret lims'][2],
                                    'Turret',
                                    0]}

    def __init__(self, width, height, title=''):
        global arm
        super(Window, self).__init__(width, height, title)
        glClearColor(0, 0, 0, 1)
        glEnable(GL_DEPTH_TEST)
        arm = Orion5.Orion5(serialPortName)
        #arm.setTimeToGoal(1)
        self.on_text_motion(False)
        self._ModelsLen = len(Models)
        for iterator1 in self._Controls[0]:
            self._Controls[1].append(pyglet.graphics.Batch())
            div = 3
            vertices = [-CONTROLSIZE / div, -CONTROLSIZE / div, 0,
                        CONTROLSIZE / div, -CONTROLSIZE / div, 0,
                        -CONTROLSIZE / div, CONTROLSIZE / div, 0,
                        -CONTROLSIZE / div, CONTROLSIZE / div, 0,
                        CONTROLSIZE / div, -CONTROLSIZE / div, 0,
                        CONTROLSIZE / div, CONTROLSIZE / div, 0]
            normals = [0.0,0.0,1.0,
                       0.0,0.0,1.0,
                       0.0,0.0,1.0,
                       0.0,0.0,1.0,
                       0.0,0.0,1.0,
                       0.0,0.0,1.0]
            indices = range(6)
            self._Controls[1][-1].add_indexed(len(vertices) // 3,
                                          GL_TRIANGLES,
                                          None,  # group,
                                          indices,
                                          ('v3f/static', vertices),
                                          ('n3f/static', normals))
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
                    '''print(len(vertices), vertices, '\n', len(normals), normals, '\n')
                    input('yes')'''
            # Create a list of triangle indices.
            indices = range(3 * len(Models[iterator1][1]))  # [[3*i, 3*i+1, 3*i+2] for i in xrange(len(facets))]
            self._Objects[-1].add_indexed(len(vertices) // 3,
                                                 GL_TRIANGLES,
                                                 None,  # group,
                                                 indices,
                                                 ('v3f/static', vertices),
                                                 ('n3f/static', normals))
        pyglet.clock.schedule_interval(self.update, 1 / 30.0)
        print(self._ControlVars)

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
        self._MousePos[0] = x
        self._MousePos[1] = y

    def on_mouse_press(self, x, y, button, modifiers):
        self.controlState[0] = button
        self.controlState[2] = modifiers
        self.controlState[1] = 0#iterator1
        self._MousePos[0] = x
        self._MousePos[1] = y
        for iterator1 in range(len(ZONES)):
            if ((abs((x - WINDOW[0] / 2) * CONTROLSCALER - self._Controls[2][iterator1][0]) < (ZONEWIDTH / 2)*CONTROLSCALER)
                and (abs((y - WINDOW[1] / 2) * CONTROLSCALER - self._Controls[2][iterator1][1]) < (ZONEWIDTH / 2)*CONTROLSCALER)):
                self.controlState[1] = iterator1 + 1
                if self.controlState[1] != 0:
                    print(self.controlState[1])
        self._MousePos[0] = x
        self._MousePos[1] = y

    def on_mouse_release(self, x, y, button, modifiers):
        self.controlState[0] = -1
        self.controlState[1] = -1
        self.controlState[2] = -1
        self._MousePos[0] = x
        self._MousePos[1] = y

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
            self._sequence.append([['Turret', copy.copy(self._armVARS['Turret'])],
                                   ['Shoulder', copy.copy(self._armVARS['Shoulder'])],
                                   ['Elbow', copy.copy(self._armVARS['Elbow'])],
                                   ['Wrist', copy.copy(self._armVARS['Wrist'])],
                                   ['Claw', copy.copy(self._armVARS['Claw'])]])
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
            self._armVARS['Turret'] = -arm.base.getPosition()
            self._armVARS['Shoulder'] = arm.shoulder.getPosition()
            self._armVARS['Elbow'] = arm.elbow.getPosition()
            self._armVARS['Wrist'] = arm.wrist.getPosition()
            self._armVARS['Claw'] = arm.claw.getPosition()
        elif self.controlState[5]:
            self._armVARS['Turret'] = copy.copy(self._sequence[self._sequenceIterator][0][1])
            self._armVARS['Shoulder'] = copy.copy(self._sequence[self._sequenceIterator][1][1])
            self._armVARS['Elbow'] = copy.copy(self._sequence[self._sequenceIterator][2][1])
            self._armVARS['Wrist'] = copy.copy(self._sequence[self._sequenceIterator][3][1])
            self._armVARS['Claw'] = copy.copy(self._sequence[self._sequenceIterator][4][1])
        if ((self.controlState[4] or self.controlState[5]) and self._armVARS['Turret'] != None):
            self._armVARS['Elbow Angle'] = self._armVARS['Elbow'] + self._armVARS['Shoulder'] - 180.0
            self._armVARS['Attack Angle'] = self._armVARS['Wrist'] - 180.0 + self._armVARS['Elbow Angle']
            self._armVARS['Elbow Pos'][0] = self._armVARS['Shoulder Pos'][0] + pol2rect(-armConstants['Bicep Len'],-self._armVARS['Shoulder'], True)
            self._armVARS['Elbow Pos'][2] = self._armVARS['Shoulder Pos'][2] + pol2rect(-armConstants['Bicep Len'],-self._armVARS['Shoulder'], False)
            self._armVARS['Wrist Pos'][0] = self._armVARS['Elbow Pos'][0] - pol2rect(armConstants['Forearm Len'],-self._armVARS['Elbow Angle'],True)
            self._armVARS['Wrist Pos'][2] = self._armVARS['Elbow Pos'][2] - pol2rect(armConstants['Forearm Len'],-self._armVARS['Elbow Angle'],False)
            self._armVARS['X'] = -self._armVARS['Wrist Pos'][0] + pol2rect((85.25 + self._armVARS['Attack Depth']),self._armVARS['Attack Angle'], True)
            self._armVARS['Z'] = self._armVARS['Wrist Pos'][2] + pol2rect((85.25 + self._armVARS['Attack Depth']),self._armVARS['Attack Angle'], False)
        if self.controlState[6]:
            #sequencer
            if (abs(DifferentialWrapped360(self._armVARS['Turret'], -arm.base.getPosition()))
                    + abs(DifferentialWrapped360(self._armVARS['Shoulder'], arm.shoulder.getPosition()))
                    + abs(DifferentialWrapped360(self._armVARS['Elbow'], arm.elbow.getPosition()))
                    + abs(DifferentialWrapped360(self._armVARS['Wrist'], arm.wrist.getPosition()))
                    + abs(DifferentialWrapped360(self._armVARS['Claw'], arm.claw.getPosition()))) < 12:
                self._sequenceIterator += 1
                if self._sequenceIterator > len(self._sequence) - 2: #yo
                    self._sequenceIterator = -1
            '''else:
                print(abs(DifferentialWrapped360(self._armVARS['Turret'], -arm.base.getPosition()))
                    , abs(DifferentialWrapped360(self._armVARS['Shoulder'], arm.shoulder.getPosition()))
                    , abs(DifferentialWrapped360(self._armVARS['Elbow'], arm.elbow.getPosition()))
                    , abs(DifferentialWrapped360(self._armVARS['Wrist'], arm.wrist.getPosition()))
                    , abs(DifferentialWrapped360(self._armVARS['Claw'], arm.claw.getPosition())))'''
        if (not self.controlState[4] and self.controlState[3]):
            temp = [abs(self._armVARS['Turret'] + arm.base.getPosition()) / MAXSERVOSPEEDS[0]['Turret'],
                    abs(self._armVARS['Shoulder'] - arm.shoulder.getPosition()) / MAXSERVOSPEEDS[0]['Shoulder'],
                    abs(self._armVARS['Elbow'] - arm.elbow.getPosition()) / MAXSERVOSPEEDS[0]['Elbow'],
                    abs(self._armVARS['Wrist'] - arm.wrist.getPosition()) / MAXSERVOSPEEDS[0]['Wrist'],
                    abs(self._armVARS['Claw'] - arm.claw.getPosition()) / MAXSERVOSPEEDS[0]['Claw']]
            maxSpeed = 0
            for item in temp:
                if item > maxSpeed:
                    maxSpeed = 0.0 + item
            #arm.setTimeToGoal(maxSpeed)
            arm.base.setGoalPosition(wrap360(-self._armVARS['Turret']))
            arm.shoulder.setGoalPosition(wrap360(self._armVARS['Shoulder']))
            arm.elbow.setGoalPosition(wrap360(self._armVARS['Elbow']))
            arm.wrist.setGoalPosition(wrap360(self._armVARS['Wrist']))
            arm.claw.setGoalPosition(wrap360(self._armVARS['Claw']))

    def on_draw(self):
        global arm
        # Clear the current GL Window
        self.clear()
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        for iterator in range(len(self._Controls[0])):
            glLoadIdentity()
            scaler = (self._armVARS[self._ControlVars[self._Controls[0][iterator]][6]]
                      - self._ControlVars[self._Controls[0][iterator]][4]) \
                     / self._ControlVars[self._Controls[0][iterator]][5] \
                     + self._ControlVars[self._Controls[0][iterator]][7]
            if scaler > 1:
                scaler -= 1
            self._Controls[2][iterator][0] = ((self._ControlVars[self._Controls[0][iterator]][0]
                                               * CONTROLSCALER)
                                              + (self._ControlVars[self._Controls[0][iterator]][2]
                                                 * CONTROLSCALER
                                                 * scaler))
            self._Controls[2][iterator][1] = ((self._ControlVars[self._Controls[0][iterator]][1]
                                               * CONTROLSCALER)
                                              + (self._ControlVars[self._Controls[0][iterator]][3]
                                                 * CONTROLSCALER
                                                 * scaler))
            glTranslatef(self._Controls[2][iterator][0],
                         self._Controls[2][iterator][1],
                         CONTROLZPOSITION)
            '''glTranslatef(self._ControlVars[self._Controls[0][iterator]][0] * CONTROLSCALER,
                         self._ControlVars[self._Controls[0][iterator]][1] * CONTROLSCALER,
                         CONTROLZPOSITION)
            
            glTranslatef(self._ControlVars[self._Controls[0][iterator]][2] * CONTROLSCALER * scaler,
                         self._ControlVars[self._Controls[0][iterator]][3] * CONTROLSCALER * scaler,
                         0)'''
            glMaterialfv(GL_FRONT, GL_AMBIENT, self._ColourBank[1])
            self._Controls[1][iterator].draw()

        for iterator1 in range(self._ModelsLen):
            glLoadIdentity()
            glTranslatef(self.xOffset, self.yOffset, self.zOffset-650)
            glRotatef(self.xRotation, 1, 0, 0)
            glRotatef(self.yRotation, 0, 1, 0)
            glRotatef(self.zRotation, 0, 0, 1)

            #Turret Rotate
            if self._ModelIDs[iterator1] > 0:
                glRotatef(self._armVARS['Turret'], 0, 0, 1)

            #Part Move
            if self._ModelIDs[iterator1] == 2:
                glTranslatef(self._armVARS['Shoulder Pos'][0], self._armVARS['Shoulder Pos'][1], self._armVARS['Shoulder Pos'][2])
            elif self._ModelIDs[iterator1] == 3:
                glTranslatef(self._armVARS['Elbow Pos'][0], self._armVARS['Elbow Pos'][1], self._armVARS['Elbow Pos'][2])
            elif self._ModelIDs[iterator1] == 4:
                glTranslatef(self._armVARS['Wrist Pos'][0], self._armVARS['Wrist Pos'][1], self._armVARS['Wrist Pos'][2])
            elif self._ModelIDs[iterator1] == 5:
                glTranslatef(self._armVARS['Wrist Pos'][0], - (self._armVARS['Claw'] - 120) / 7.2, self._armVARS['Wrist Pos'][2])
            elif self._ModelIDs[iterator1] == 6:
                glTranslatef(self._armVARS['Wrist Pos'][0], (self._armVARS['Claw'] - 120) / 7.2, self._armVARS['Wrist Pos'][2])

            #Part Rotate
            if self._ModelIDs[iterator1] > 3:
                glRotatef(self._armVARS['Attack Angle'], 0, 1, 0)
            elif self._ModelIDs[iterator1] == 2:
                glRotatef(self._armVARS['Shoulder'], 0, 1, 0)
            elif self._ModelIDs[iterator1] == 3:
                glRotatef(self._armVARS['Elbow Angle'], 0, 1, 0)

            #Draw the Thing
            glMaterialfv(GL_FRONT, GL_AMBIENT, self._ColourBank[iterator1])
            self._Objects[iterator1].draw()

    def on_text_motion(self, motion, BLAH = False, Setting = None):
        global arm
        #Check the keypress
        '''
        TODO: build a temporary holder for the old value of the thing being changed, 
        along with a loop around this entire thing
        '''
        for item in armConstants['Key IDs']:
            if motion == item[0]:
                if Setting == None:
                    Setting = armConstants[item[1]+' lims'][1]
                    if not item[2]:
                        Setting *= -1
                    self._armVARS[item[1]] += Setting
                else:
                    self._armVARS[item[1]] = Setting
                if self._armVARS[item[1]] > armConstants[item[1] + ' lims'][0]:
                    if armConstants[item[1] + ' lims'][3]:
                        self._armVARS[item[1]] -= armConstants[item[1] + ' lims'][0]
                    else:
                        self._armVARS[item[1]] = armConstants[item[1] + ' lims'][0]
                elif self._armVARS[item[1]] < armConstants[item[1]+ ' lims'][2]:
                    if armConstants[item[1] + ' lims'][3]:
                        self._armVARS[item[1]] += armConstants[item[1] + ' lims'][0]
                    else:
                        self._armVARS[item[1]] = armConstants[item[1] + ' lims'][2]

        #if self._armVARS['Turret'] != None: #uneeded check since fixing the ORION5.py
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
            self._armVARS['Shoulder'] = 180.0 - rect2pol(self._armVARS['Wrist Pos'][0] - self._armVARS['Shoulder Pos'][0], self._armVARS['Wrist Pos'][2] - self._armVARS['Shoulder Pos'][2], False)
            self._armVARS['Elbow Angle'] = 0.0 + self._armVARS['Shoulder']
        else:
            self._armVARS['Shoulder'] = 180.0 - rect2pol(self._armVARS['Wrist Pos'][0] - self._armVARS['Shoulder Pos'][0], self._armVARS['Wrist Pos'][2] - self._armVARS['Shoulder Pos'][2], False) + math.acos(((b ** 2.0) + (armConstants['Bicep Len'] ** 2.0) - (armConstants['Forearm Len'] ** 2.0)) / (2.0 * b * armConstants['Bicep Len'])) * 180.0 / math.pi
            self._armVARS['Elbow Angle'] = self._armVARS['Shoulder'] - 180 + math.acos(((armConstants['Forearm Len'] ** 2) + (armConstants['Bicep Len'] ** 2) - (b ** 2)) / (2 * armConstants['Forearm Len'] * armConstants['Bicep Len'])) * 180.0 / math.pi
            self._armVARS['Elbow Pos'][0] = self._armVARS['Shoulder Pos'][0] - pol2rect(armConstants['Bicep Len'] , -self._armVARS['Shoulder'], True)
            self._armVARS['Elbow Pos'][2] = self._armVARS['Shoulder Pos'][2] - pol2rect(armConstants['Bicep Len'] , -self._armVARS['Shoulder'], False)

        self._armVARS['Shoulder'] = 0.0 + self._armVARS['Shoulder']
        self._armVARS['Elbow'] = self._armVARS['Elbow Angle'] - self._armVARS['Shoulder'] + 180.0
        self._armVARS['Wrist'] = self._armVARS['Attack Angle'] - self._armVARS['Elbow Angle'] + 180.0

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self._MousePos[0] = x
        self._MousePos[1] = y
        if (self.controlState[0] == 1
            and self.controlState[1] == 0):
            self.xRotation -= dy * 0.25
            if self.controlState[2] == 0:
                self.yRotation += dx * 0.25
            else:
                self.zRotation += dx * 0.25
        if (self.controlState[0] == 4
            and self.controlState[1] == 0):
            self.xOffset += dx * .5
            self.yOffset += dy * .5
        if self.controlState[1] > 0:
            if self._Controls[2][self.controlState[1] - 1][2]:
                thepercent = (((y - ZONES[self.controlState[1] - 1][1][1]+(ZONEWIDTH/2))
                               / (ZONES[self.controlState[1] - 1][1][3] - ZONES[self.controlState[1] - 1][1][1]))
                              +  self._ControlVars[self._Controls[0][self.controlState[1] - 1]][7])
            else:
                thepercent = (((x - ZONES[self.controlState[1] - 1][1][0] + (ZONEWIDTH / 2))
                              / (ZONES[self.controlState[1] - 1][1][2] - ZONES[self.controlState[1] - 1][1][0]))
                              + self._ControlVars[self._Controls[0][self.controlState[1] - 1]][7])
            if ((self._ControlVars[self._Controls[0][self.controlState[1] - 1]][7] != 0) and (thepercent > 1)):
                thepercent -= 1
            self.on_text_motion(self._Controls[2][self.controlState[1] - 1][3], False,
                                (self._ControlVars[self._Controls[0][self.controlState[1] - 1]][5]
                                 * thepercent
                                 + self._ControlVars[self._Controls[0][self.controlState[1] - 1]][4])
                                )

def Main():
    global ORION5
    ORION5 = Window(WINDOW[0], WINDOW[1], 'Orion5 Visualiser and Controller')
    pyglet.app.run()

if __name__ == '__main__':
    Main()

arm.exit()