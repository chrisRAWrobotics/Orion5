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
import copy, math, ctypes

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
print(WINDOW)
INCREMENT = 5
CONTROLZPOSITION = -100
CONTROLSCALER = 0.097
CONTROLSIZE = ZONEWIDTH*CONTROLSCALER

armConstants = {'X lims':[500.0,1.0,-250.0, False],
                'Z lims':[500.0,1.0,-250.0, False],
                'Attack Angle lims':[360.0,1.0,0.0, True],
                'Attack Depth lims':[500.0,1.0,-250.0, False],
                'Claw lims':[250.0, 1.0, 20.0, False],
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
           [-30.309,0.0,53.0],
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

def ComQuery():
    global comListObj, comObj
    import tkinter, tkinter.ttk
    font_size = 14
    comQuery = tkinter.Tk()
    comQuery.title('Com port selector')
    comQuery.minsize(width=100, height=100)
    goButton = tkinter.Button(comQuery, text="Select", font = ("Arial", font_size, "bold"))
    comList = tkinter.StringVar()
    comPorts = tkinter.ttk.Combobox(comQuery, font = ("Arial", font_size, "bold"), width = 40, textvariable = comList, state = 'readonly')
    comListObj = None
    comObj = None
    def RefreshComs(pokeThrough):
        global comListObj
        import serial.tools.list_ports
        comListObj = serial.tools.list_ports.comports()
        thing2 = ['None']
        for item in comListObj:
            thing2.append(str(item))
        for iterator1 in range(len(thing2)):
            if iterator1 == 0:
                thing3 = (str(iterator1)+' '+thing2[iterator1],)
            elif (comListObj[iterator1-1].vid == 1027 and comListObj[iterator1-1].pid == 24597):
                thing3 = thing3 + (str(iterator1)+' '+thing2[iterator1],)
        comPorts['values'] = thing3
    RefreshComs('pelicanCase')
    comPorts.grid(row=1, column=1, columnspan=4)
    goButton.grid(row=2, column=1, columnspan=3)
    comPorts.bind('<<ComboboxSelected>>', RefreshComs)
    def GoButton():
        global comListObj, comObj
        try:
            comListObj.append(None)
            comObj = comListObj[int(comList.get()[:comList.get().find(' ')]) - 1]
        except:
            print('Error picking com port')
        comQuery.quit()
        comQuery.destroy()
    goButton.configure(command=GoButton)
    comQuery.mainloop()
    return comObj

class Window(pyglet.window.Window):
    # Cube 3D start rotation
    xRotation = -80
    yRotation = 0
    zRotation = -150
    xOffset = 160
    yOffset = -100
    zOffset = -300
    controlState = [-1, -1, -1, False, False, False, False]
    _scalers = {'Shoulder': (1+(52/28))}
    _zonewidth = 25
    _controlzposition = -100
    _controlscaler = 0.097
    _controlsize = None
    _window = None
    _zones = None
    _MousePos = [0,0]
    _armVARS = {'X': 400.0,
                'Z': 50.0,
                'Attack Angle': 0.0,
                'Attack Depth': 50.0,
                'Wrist Pos': [0.0, 0.0, 0.0],
                'Elbow Pos': [0.0, 0.0, 0.0],
                'Shoulder Pos': [-30.309, 0.0, 53.0],
                'Elbow Angle': 0.0,
                'Turret': 180.0,
                'Shoulder': 0.0,
                'Elbow': 0.0,
                'Wrist': 0.0,
                'Claw': 200.0,
                'OLD': {'X': 400.0,
                        'Z': 50.0,
                        'Attack Angle': 0.0,
                        'Attack Depth': 50.0,
                        'Wrist Pos': [0.0, 0.0, 0.0],
                        'Elbow Pos': [0.0, 0.0, 0.0],
                        'Shoulder Pos': [-30.309, 0.0, 53.0],
                        'Elbow Angle': 0.0,
                        'Turret': 180.0,
                        'Shoulder': 0.0,
                        'Elbow': 0.0,
                        'Wrist': 0.0,
                        'Claw': 200.0, },
                'Iter': ['X',
                         'Z',
                         'Attack Angle',
                         'Attack Depth',
                         'Wrist Pos',
                         'Elbow Pos',
                         'Shoulder Pos',
                         'Elbow Angle',
                         'Turret',
                         'Shoulder',
                         'Elbow',
                         'Wrist',
                         'Claw']}
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
    _ControlVars = None

    def __init__(self, width, height, title=''):
        global arm
        super(Window, self).__init__(width, height, title, resizable=True)

        # select libExtension based on platform
        libExtension = '.dll' # windows as default
        if sys.platform == 'darwin':
            libName = '.dylib' # Mac OS
        elif 'linux' in sys.platform:
            libExtension = '.so'# linux based

        # load functions from C dynamic library
        clib = ctypes.cdll.LoadLibrary('Libraries/libOrion5Kinematics' + libExtension)
        self.IKinematics = clib.IKinematics
        self.IKinematics.restype = C_ArmVars
        self.CollisionCheck = clib.CollisionCheck
        self.CollisionCheck.restype = ctypes.c_int

        self._window = [WINDOW[0], WINDOW[1]]
        self.set_minimum_size(self._window[0], self._window[1])
        self._zones = [['Claw', [self._window[0] - self._zonewidth,
                                 self._zonewidth,
                                 self._window[0],
                                 self._window[1]],
              [0, 0]],  # Third Zone Second Left, Claw Open?
             ['Attack Angle', [self._zonewidth,
                               2 * self._zonewidth,
                               2 * self._zonewidth,
                               self._window[1]],
              [0, 0]],  # Fifth Zone Second from Right, Attack Angle
             ['X', [0,
                    0,
                    self._window[0],
                    self._zonewidth],
              [0, 0]],  # Second zone bottom, X Position
             ['Y', [0,
                    self._zonewidth,
                    self._zonewidth,
                    self._window[1]],
              [0, 0]],  # First Zone Left, Y Position
             ['Attack Depth', [self._window[0] - 2 * self._zonewidth,
                               2 * self._zonewidth,
                               self._window[0] - self._zonewidth,
                               self._window[1]],
              [0, 0]],  # Sixth Zone Right, Attack Depth
             ['Turret', [self._zonewidth,
                         self._zonewidth,
                         self._window[0] - self._zonewidth,
                         2 * self._zonewidth],
              [0, 0]]]  # Fourth Zone Second from Bottom, Turret Angle
        self._ControlVars = {'Claw':[(self._window[0]/2)-self._zonewidth/2,
                                 (self._zonewidth - self._window[1] / 2) + self._zonewidth / 2,
                                 0,
                                 abs((self._zonewidth - self._window[1] / 2) + self._zonewidth/2)*2 + self._zonewidth,
                                 armConstants['Claw lims'][2],
                                 armConstants['Claw lims'][0]-armConstants['Claw lims'][2],
                                 'Claw',
                                 0],
                    'Attack Angle':[(self._zonewidth-self._window[0]/2)+self._zonewidth/2,
                                    (2 * self._zonewidth - self._window[1] / 2) + self._zonewidth / 2,
                                    0,
                                    abs((2 * self._zonewidth - self._window[1] / 2) + self._zonewidth / 2)*2 + 2 * self._zonewidth,
                                    armConstants['Attack Angle lims'][2],
                                    armConstants['Attack Angle lims'][0] - armConstants['Attack Angle lims'][2],
                                    'Attack Angle',
                                    .5],
                    'X':[(-self._window[0]/2)+self._zonewidth/2,
                         (-self._window[1]/2)+self._zonewidth/2,
                         abs((-self._window[0]/2)+self._zonewidth/2)*2,
                         0,
                         armConstants['X lims'][2],
                         armConstants['X lims'][0] - armConstants['X lims'][2],
                         'X',
                         0],
                    'Y':[(-self._window[0]/2)+self._zonewidth/2,
                         (self._zonewidth - self._window[1] / 2) + self._zonewidth / 2,
                         0,
                         abs((self._zonewidth - self._window[1] / 2) + self._zonewidth / 2)*2 + self._zonewidth,
                         armConstants['Z lims'][2],
                         armConstants['Z lims'][0] - armConstants['Z lims'][2],
                         'Z',
                         0],
                    'Attack Depth':[(self._window[0]/2-self._zonewidth)-self._zonewidth/2,
                                    (2*self._zonewidth-self._window[1] / 2) + self._zonewidth / 2,
                                    0,
                                    abs((2*self._zonewidth-self._window[1] / 2) + self._zonewidth / 2)*2 + 2 * self._zonewidth,
                                    armConstants['Attack Depth lims'][2],
                                    armConstants['Attack Depth lims'][0] - armConstants['Attack Depth lims'][2],
                                    'Attack Depth',
                                    0],
                    'Turret':[(self._zonewidth-self._window[0]/2)+self._zonewidth/2,
                                    (self._zonewidth-self._window[1]/2)+self._zonewidth/2,
                                    abs((self._zonewidth - self._window[0] / 2) + self._zonewidth / 2) * 2,
                                    0,
                                    armConstants['Turret lims'][2],
                                    armConstants['Turret lims'][0] - armConstants['Turret lims'][2],
                                    'Turret',
                                    0]}
        self._controlsize = self._zonewidth * self._controlscaler

        glClearColor(0, 0, 0, 1)
        glEnable(GL_DEPTH_TEST)
        #gluPerspective(45, 1, 1, 2)
        arm = Orion5.Orion5(serialPortName)
        #arm.setTimeToGoal(1)
        self.on_text_motion(False)
        self._ModelsLen = len(Models)
        for iterator1 in self._Controls[0]:
            self._Controls[1].append(pyglet.graphics.Batch())
            div = 3
            vertices = [-self._controlsize / div, -self._controlsize / div, 0,
                        self._controlsize / div, -self._controlsize / div, 0,
                        -self._controlsize / div, self._controlsize / div, 0,
                        -self._controlsize / div, self._controlsize / div, 0,
                        self._controlsize / div, -self._controlsize / div, 0,
                        self._controlsize / div, self._controlsize / div, 0]
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
            #self._ColourBank.append(vec(Models[iterator1][0][3][0], Models[iterator1][0][3][1], Models[iterator1][0][3][2], Models[iterator1][0][3][3]))
            self._ColourBank.append(
                [Models[iterator1][0][3][0], Models[iterator1][0][3][1], Models[iterator1][0][3][2],
                    Models[iterator1][0][3][3]])
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
        for item1 in self._Controls[2]:
            self.on_text_motion(item1[3])
            self.on_text_motion(item1[4])
        #print(self._ControlVars)

    def on_resize(self, width, height):
        # set the Viewport
        glViewport(0, 0, width, height)
        self._window = [width, height]
        self.set_size(width, height)
        self._controlsize = self._zonewidth * self._controlscaler
        self._zones = [['Claw', [self._window[0] - self._zonewidth,
                                 self._zonewidth,
                                 self._window[0],
                                 self._window[1]],
                        [0, 0]],  # Third Zone Second Left, Claw Open?
                       ['Attack Angle', [self._zonewidth,
                                         2 * self._zonewidth,
                                         2 * self._zonewidth,
                                         self._window[1]],
                        [0, 0]],  # Fifth Zone Second from Right, Attack Angle
                       ['X', [0,
                              0,
                              self._window[0],
                              self._zonewidth],
                        [0, 0]],  # Second zone bottom, X Position
                       ['Y', [0,
                              self._zonewidth,
                              self._zonewidth,
                              self._window[1]],
                        [0, 0]],  # First Zone Left, Y Position
                       ['Attack Depth', [self._window[0] - 2 * self._zonewidth,
                                         2 * self._zonewidth,
                                         self._window[0] - self._zonewidth,
                                         self._window[1]],
                        [0, 0]],  # Sixth Zone Right, Attack Depth
                       ['Turret', [self._zonewidth,
                                   self._zonewidth,
                                   self._window[0] - self._zonewidth,
                                   2 * self._zonewidth],
                        [0, 0]]]  # Fourth Zone Second from Bottom, Turret Angle
        self._ControlVars = {'Claw': [(self._window[0] / 2) - self._zonewidth / 2,
                                      (self._zonewidth - self._window[1] / 2) + self._zonewidth / 2,
                                      0,
                                      abs((self._zonewidth - self._window[
                                          1] / 2) + self._zonewidth / 2) * 2 + self._zonewidth,
                                      armConstants['Claw lims'][2],
                                      armConstants['Claw lims'][0] - armConstants['Claw lims'][2],
                                      'Claw',
                                      0],
                             'Attack Angle': [(self._zonewidth - self._window[0] / 2) + self._zonewidth / 2,
                                              (2 * self._zonewidth - self._window[1] / 2) + self._zonewidth / 2,
                                              0,
                                              abs((2 * self._zonewidth - self._window[
                                                  1] / 2) + self._zonewidth / 2) * 2 + 2 * self._zonewidth,
                                              armConstants['Attack Angle lims'][2],
                                              armConstants['Attack Angle lims'][0] - armConstants['Attack Angle lims'][
                                                  2],
                                              'Attack Angle',
                                              .5],
                             'X': [(-self._window[0] / 2) + self._zonewidth / 2,
                                   (-self._window[1] / 2) + self._zonewidth / 2,
                                   abs((-self._window[0] / 2) + self._zonewidth / 2) * 2,
                                   0,
                                   armConstants['X lims'][2],
                                   armConstants['X lims'][0] - armConstants['X lims'][2],
                                   'X',
                                   0],
                             'Y': [(-self._window[0] / 2) + self._zonewidth / 2,
                                   (self._zonewidth - self._window[1] / 2) + self._zonewidth / 2,
                                   0,
                                   abs((self._zonewidth - self._window[
                                       1] / 2) + self._zonewidth / 2) * 2 + self._zonewidth,
                                   armConstants['Z lims'][2],
                                   armConstants['Z lims'][0] - armConstants['Z lims'][2],
                                   'Z',
                                   0],
                             'Attack Depth': [(self._window[0] / 2 - self._zonewidth) - self._zonewidth / 2,
                                              (2 * self._zonewidth - self._window[1] / 2) + self._zonewidth / 2,
                                              0,
                                              abs((2 * self._zonewidth - self._window[
                                                  1] / 2) + self._zonewidth / 2) * 2 + 2 * self._zonewidth,
                                              armConstants['Attack Depth lims'][2],
                                              armConstants['Attack Depth lims'][0] - armConstants['Attack Depth lims'][
                                                  2],
                                              'Attack Depth',
                                              0],
                             'Turret': [(self._zonewidth - self._window[0] / 2) + self._zonewidth / 2,
                                        (self._zonewidth - self._window[1] / 2) + self._zonewidth / 2,
                                        abs((self._zonewidth - self._window[0] / 2) + self._zonewidth / 2) * 2,
                                        0,
                                        armConstants['Turret lims'][2],
                                        armConstants['Turret lims'][0] - armConstants['Turret lims'][2],
                                        'Turret',
                                        0]}
        smaller = width
        if width > height:
            smaller = height
        self._controlzposition = - (100 + ((smaller-650)*.153))

        # using Projection mode
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspectRatio = width / height
        gluPerspective(35, aspectRatio, 1, 10000)
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
        for iterator1 in range(len(self._zones)):
            if ((abs((x - self._window[0] / 2) * self._controlscaler - self._Controls[2][iterator1][0]) < (self._zonewidth / 2)*self._controlscaler)
                and (abs((y - self._window[1] / 2) * self._controlscaler - self._Controls[2][iterator1][1]) < (self._zonewidth / 2)*self._controlscaler)):
                self.controlState[1] = iterator1 + 1
                '''
                if self.controlState[1] != 0:
                    print(self.controlState[1])'''
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
            self.controlState[4] = False
            self.controlState[3] = not self.controlState[3]
            if self.controlState[3]:
                arm.enableTorque()
            else:
                arm.releaseTorque()
        elif symbol == key.A:
            arm.releaseTorque()
            self.controlState[3] = False
            self.controlState[4] = not self.controlState[4]
        elif symbol == key.E:
            if len(self._sequence) != 0:
                #Show entry toggle
                self.controlState[5] = not self.controlState[5]
                #print(self._sequenceIterator, self._sequence[self._sequenceIterator])
        elif symbol == key.W:
            if len(self._sequence) != 0:
                self._sequenceIterator -= 1
            if self._sequenceIterator < -1:
                self._sequenceIterator = len(self._sequence)-2
            #print(self._sequenceIterator, self._sequence[self._sequenceIterator])
        elif symbol == key.S:
            if len(self._sequence) != 0:
                self._sequenceIterator += 1
            if self._sequenceIterator > len(self._sequence)-2:
                self._sequenceIterator = -1
            #print(self._sequenceIterator, self._sequence[self._sequenceIterator])
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
                #print(self._sequenceIterator, self._sequence[self._sequenceIterator])
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
            self._armVARS['Shoulder'] = arm.shoulder.getPosition() / self._scalers['Shoulder']
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
                    + abs(DifferentialWrapped360(self._armVARS['Shoulder'], arm.shoulder.getPosition() / self._scalers['Shoulder']) )
                    + abs(DifferentialWrapped360(self._armVARS['Elbow'], arm.elbow.getPosition()))
                    + abs(DifferentialWrapped360(self._armVARS['Wrist'], arm.wrist.getPosition()))
                    + abs(DifferentialWrapped360(self._armVARS['Claw'], arm.claw.getPosition()))) < 12:
                self._sequenceIterator += 1
                if self._sequenceIterator > len(self._sequence) - 2: #yo
                    self._sequenceIterator = -1
            '''else:
                print(abs(DifferentialWrapped360(self._armVARS['Turret'], -arm.base.getPosition()))
                    , abs(DifferentialWrapped360(self._armVARS['Shoulder'], arm.shoulder.getPosition()/ self._scalers['Shoulder']))
                    , abs(DifferentialWrapped360(self._armVARS['Elbow'], arm.elbow.getPosition()))
                    , abs(DifferentialWrapped360(self._armVARS['Wrist'], arm.wrist.getPosition()))
                    , abs(DifferentialWrapped360(self._armVARS['Claw'], arm.claw.getPosition())))'''
        if (not self.controlState[4] and self.controlState[3]):
            temp = [abs(self._armVARS['Turret'] + arm.base.getPosition()) / MAXSERVOSPEEDS[0]['Turret'],
                    abs(self._armVARS['Shoulder'] - (arm.shoulder.getPosition()/ self._scalers['Shoulder'])) / MAXSERVOSPEEDS[0]['Shoulder'],
                    abs(self._armVARS['Elbow'] - arm.elbow.getPosition()) / MAXSERVOSPEEDS[0]['Elbow'],
                    abs(self._armVARS['Wrist'] - arm.wrist.getPosition()) / MAXSERVOSPEEDS[0]['Wrist'],
                    abs(self._armVARS['Claw'] - arm.claw.getPosition()) / MAXSERVOSPEEDS[0]['Claw']]
            maxSpeed = 0
            for item in temp:
                if item > maxSpeed:
                    maxSpeed = 0.0 + item
            #arm.setTimeToGoal(maxSpeed)
            arm.base.setGoalPosition(wrap360f(-self._armVARS['Turret']))
            arm.shoulder.setGoalPosition(wrap360f(self._armVARS['Shoulder'] * self._scalers['Shoulder']))
            arm.elbow.setGoalPosition(wrap360f(self._armVARS['Elbow']))
            arm.wrist.setGoalPosition(wrap360f(self._armVARS['Wrist']))
            arm.claw.setGoalPosition(wrap360f(self._armVARS['Claw']))

    def on_draw(self):
        global arm
        # Clear the current GL Window
        self.clear()
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        for iterator in range(len(self._Controls[0])):
            glLoadIdentity()
            scaler = ((self._armVARS[self._ControlVars[self._Controls[0][iterator]][6]]
                       - self._ControlVars[self._Controls[0][iterator]][4])
                      / self._ControlVars[self._Controls[0][iterator]][5]
                      + self._ControlVars[self._Controls[0][iterator]][7])
            if scaler > 1:
                scaler -= 1
            self._Controls[2][iterator][0] = ((self._ControlVars[self._Controls[0][iterator]][0]
                                               * self._controlscaler)
                                              + (self._ControlVars[self._Controls[0][iterator]][2]
                                                 * self._controlscaler
                                                 * scaler))
            self._Controls[2][iterator][1] = ((self._ControlVars[self._Controls[0][iterator]][1]
                                               * self._controlscaler)
                                              + (self._ControlVars[self._Controls[0][iterator]][3]
                                                 * self._controlscaler
                                                 * scaler))
            glTranslatef(self._Controls[2][iterator][0],
                         self._Controls[2][iterator][1],
                         self._controlzposition)
            glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
            glEnable(GL_COLOR_MATERIAL)
            glColor3f(.6,.6,.6)
            self._Controls[1][iterator].draw()
            glDisable(GL_COLOR_MATERIAL)

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
                glTranslatef(self._armVARS['Wrist Pos'][0], - (self._armVARS['Claw'] - 20) / 11, self._armVARS['Wrist Pos'][2])
            elif self._ModelIDs[iterator1] == 6:
                glTranslatef(self._armVARS['Wrist Pos'][0], (self._armVARS['Claw'] - 20) / 11, self._armVARS['Wrist Pos'][2])

            #Part Rotate
            if self._ModelIDs[iterator1] > 3:
                glRotatef(self._armVARS['Attack Angle'], 0, 1, 0)
            elif self._ModelIDs[iterator1] == 2:
                glRotatef(self._armVARS['Shoulder'], 0, 1, 0)
            elif self._ModelIDs[iterator1] == 3:
                glRotatef(self._armVARS['Elbow Angle'], 0, 1, 0)

            #Draw the Thing
            glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
            glEnable(GL_COLOR_MATERIAL)
            glColor3f(self._ColourBank[iterator1][0],
                      self._ColourBank[iterator1][1],
                      self._ColourBank[iterator1][2])
            #glMaterialfv(GL_FRONT, GL_AMBIENT, self._ColourBank[iterator1])
            self._Objects[iterator1].draw()
            glDisable(GL_COLOR_MATERIAL)

    def on_text_motion(self, motion, BLAH = False, Setting = None):
        global arm
        #Check the keypress
        '''
        TODO: build a temporary holder for the old value of the thing being changed, 
        along with a loop around this entire thing
        '''
        for item in self._armVARS['Iter']:
            if ((type(self._armVARS['OLD'][item]) == float) or (type(self._armVARS['OLD'][item]) == int)):
                self._armVARS['OLD'][item] = 0.0 + self._armVARS[item]
            elif (type(self._armVARS['OLD'][item]) == list):
                for iterator in range(len(self._armVARS[item])):
                    self._armVARS['OLD'][item][iterator] = 0.0 + self._armVARS[item][iterator]
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
        try:

            c_armVars = self.IKinematics(self.PythonArmVarsToC());
            self.CArmVarsToPython(c_armVars);

        except Exception as e:
            print(e)
            for item in self._armVARS['Iter']:
                if ((type(self._armVARS['OLD'][item]) == float) or (type(self._armVARS['OLD'][item]) == int)):
                    self._armVARS[item] = 0.0 + self._armVARS['OLD'][item]
                elif (type(self._armVARS['OLD'][item]) == list):
                    for iterator in range(len(self._armVARS[item])):
                        self._armVARS[item][iterator] = 0.0 + self._armVARS['OLD'][item][iterator]
            return

        if self.CollisionCheck(self.PythonArmVarsToC()):
            for item in self._armVARS['Iter']:
                if ((type(self._armVARS['OLD'][item]) == float) or (type(self._armVARS['OLD'][item]) == int)):
                    self._armVARS[item] = 0.0 + self._armVARS['OLD'][item]
                elif (type(self._armVARS['OLD'][item]) == list):
                    for iterator in range(len(self._armVARS[item])):
                        self._armVARS[item][iterator] = 0.0 + self._armVARS['OLD'][item][iterator]


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
                thepercent = (((y - self._zones[self.controlState[1] - 1][1][1]+(self._zonewidth/2))
                               / (self._zones[self.controlState[1] - 1][1][3] - self._zones[self.controlState[1] - 1][1][1]))
                              +  self._ControlVars[self._Controls[0][self.controlState[1] - 1]][7])
            else:
                thepercent = (((x - self._zones[self.controlState[1] - 1][1][0] + (self._zonewidth / 2))
                              / (self._zones[self.controlState[1] - 1][1][2] - self._zones[self.controlState[1] - 1][1][0]))
                              + self._ControlVars[self._Controls[0][self.controlState[1] - 1]][7])
            if ((self._ControlVars[self._Controls[0][self.controlState[1] - 1]][7] != 0) and (thepercent > 1)):
                thepercent -= 1
            self.on_text_motion(self._Controls[2][self.controlState[1] - 1][3], False,
                                (self._ControlVars[self._Controls[0][self.controlState[1] - 1]][5]
                                 * thepercent
                                 + self._ControlVars[self._Controls[0][self.controlState[1] - 1]][4])
                                )


    def PythonArmVarsToC(self):
        c_armVars = C_ArmVars()
        for key in self._armVARS['Iter']:
            value = self._armVARS[key]
            if type(value) == list:
                value = (ctypes.c_double * 3)(value[0], value[1], value[2])
            else:
                value = ctypes.c_double(value)
            setattr(c_armVars, key.replace(' ', ''), value)
        return c_armVars


    def CArmVarsToPython(self, c_armVars):
        for key in self._armVARS['Iter']:
            value = getattr(c_armVars, key.replace(' ', ''))
            if type(value) == float:
                self._armVARS[key] = value
            else:
                self._armVARS[key] = [value[0], value[1], value[2]]


# C compatible structure from armVARS dictionary
# not including the OLD and Iter sections
class C_ArmVars(ctypes.Structure):
    _fields_ = []
    for key in Window._armVARS['Iter']:
        cType = ctypes.c_double
        if type(Window._armVARS[key]) == list:
            cType = ctypes.POINTER(ctypes.c_double)
        _fields_.append((key.replace(' ', ''), cType))

def Main():
    global serialPortName
    comObj = ComQuery()
    print(comObj)
    try:
        serialPortName = str(comObj.device)
        #if comObj != None:
        print(comObj.device, comObj.name, comObj.vid, comObj.pid)
    except:
        pass


    global ORION5
    ORION5 = Window(WINDOW[0], WINDOW[1], 'Orion5 Visualiser and Controller')
    icon1 = pyglet.image.load('RR_logo_512x512.png')
    ORION5.set_icon(icon1)
    pyglet.app.run()

if __name__ == '__main__':
    Main()

arm.exit()