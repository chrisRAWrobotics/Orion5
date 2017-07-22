import struct, math

def STLRead(Models, fileName, offset, rotation, ModelID, ColorID = 1):
    filePipe = open(fileName, 'rb')
    colorcodes = [[.16, .16, .16, 1.0], [.12, .12, .12, 1.0], [.5, 0, 0, 0.1], [.38, .37, .4, 1]]
    headerLength = 80
    floatLength = 4
    endLength = 2
    header = filePipe.read(headerLength)
    facetNo = struct.unpack('L', filePipe.read(4))[0]
    Models.append([[offset,rotation, ModelID, colorcodes[ColorID]],[]])
    for data in range(facetNo):
        try:
            Normal = [struct.unpack('f', filePipe.read(floatLength))[0],
                      struct.unpack('f', filePipe.read(floatLength))[0],
                      struct.unpack('f', filePipe.read(floatLength))[0]]
            Vertex1 = [struct.unpack('f', filePipe.read(floatLength))[0],
                       struct.unpack('f', filePipe.read(floatLength))[0],
                       struct.unpack('f', filePipe.read(floatLength))[0]]
            Vertex2 = [struct.unpack('f', filePipe.read(floatLength))[0],
                       struct.unpack('f', filePipe.read(floatLength))[0],
                       struct.unpack('f', filePipe.read(floatLength))[0]]
            Vertex3 = [struct.unpack('f', filePipe.read(floatLength))[0],
                       struct.unpack('f', filePipe.read(floatLength))[0],
                       struct.unpack('f', filePipe.read(floatLength))[0]]
            filePipe.read(endLength)
            Models[-1][1].append([Normal, Vertex1, Vertex2, Vertex3])
        except:
            print("error reading facets")
            break
    filePipe.close()
    return Models

def PopulateModels(fileSets, Offsets):
    Models = []
    OffsetsNEW = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0],[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    for iterator1 in range(len(Offsets)-2):
        for iterator2 in range(iterator1+1):
            for iterator3 in range(3):
                OffsetsNEW[iterator1][iterator3] += Offsets[iterator2][iterator3]
    for iterator1 in range(2):
        for iterator2 in range(3):
            OffsetsNEW[-1-iterator1][iterator2] += OffsetsNEW[4][iterator2]
    for iterator1 in range(len(fileSets)):
        for iterator2 in range(len(fileSets[iterator1])):
            try:
                Models = STLRead(Models, fileSets[iterator1][iterator2], OffsetsNEW[iterator1], [[0.0, 0, 0, 1], [0.0, 0, 1, 0]], iterator1, int(fileSets[iterator1][iterator2][11:14]))
            except:
                Models = STLRead(Models, fileSets[iterator1][iterator2], OffsetsNEW[iterator1], [[0.0, 0, 0, 1], [0.0, 0, 1, 0]], iterator1)
    return Models

def PolyWrite(Models, fileName):
    filePipe = open(fileName, 'wb')
    filePipe.write(struct.pack('i', len(Models)))
    for iterator1 in range(len(Models)):
        filePipe.write(struct.pack('i', len(Models[iterator1][1])))
        filePipe.write(struct.pack('i', Models[iterator1][0][2]))
        for iterator2 in range(3):
            filePipe.write(struct.pack('f', Models[iterator1][0][0][iterator2]))
        for iterator2 in range(3):
            for iterator3 in range(3):
                filePipe.write(struct.pack('f', Models[iterator1][0][1][iterator2][iterator3]))
        for iterator2 in range(len(Models[iterator1][1])):
            filePipe.write(struct.pack('i', len(Models[iterator1][1][iterator2])-1))
            for iterator3 in range(len(Models[iterator1][1][iterator2])-1):
                for iterator4 in range(3):
                    filePipe.write(struct.pack('f', Models[iterator1][1][iterator2][iterator3][iterator4]))      
    filePipe.close()
    
def PolyRead(Models, fileName):
    filePipe = open(fileName, 'rb')
    ModelsNo = struct.unpack('i', filePipe.read(4))[0]
    for iterator1 in range(ModelsNo):
        FacetsNo = struct.unpack('i', filePipe.read(4))[0]
        Models.append([[[0.0,0.0,0.0],[[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]], 0],[]])
        Models[-1][0][2] = struct.unpack('i', filePipe.read(4))[0]
        for iterator2 in range(3):
            Models[-1][0][0][iterator2] = struct.unpack('f', filePipe.read(4))[0]
        for iterator2 in range(3):
            for iterator3 in range(3):
                Models[-1][0][1][iterator2][iterator3] = struct.unpack('f', filePipe.read(4))[0]
        for iterator2 in range(FacetsNo):
            ElementsNo = struct.unpack('i', filePipe.read(4))[0]
            Models[-1][1].append([])
            for iterator3 in range(ElementsNo):
                Models[-1][1][iterator2].append([0.0,0.0,0.0])
                for iterator4 in range(3):
                    Models[-1][1][iterator2][iterator3][iterator4] = struct.unpack('f', filePipe.read(4))[0]
    filePipe.close()
    return Models

from os import listdir
from os.path import isfile, join
def PullFileNames(extension, subFolder):
    fileNames = [f for f in listdir(subFolder) if isfile(join(subFolder, f))]
    iterator = 0
    while iterator < len(fileNames):
        if fileNames[iterator].find(extension) == -1:
            del fileNames[iterator]
        else:
            iterator +=1
    fileSets = [[], [], [], [], [], [], []]
    for iterator1 in range(len(fileNames)):
        fileSets[int(fileNames[iterator1][:3])].append(subFolder+'/'+fileNames[iterator1])
    return fileSets