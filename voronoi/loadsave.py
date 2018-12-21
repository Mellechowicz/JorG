import re
import numpy as np
from os import system
from periodic import periodicTableNumber

def load_POSCAR(inputName):
    """
        Reading POSCAR file. Extensive testing required.
                                                        """
    data = {}

    # Returned data:
    comment       = ""  # first line of POSCAR file
    directions    = []  # crystal directions
    cell          = []  # cell read from POSCAR file
    cellSymmetry  = ([],[],[])   # input for spglib symmetry refiner
    cellVolume    = 0.0          # volume of cell
    cellCenter    = np.zeros(3)  # center of volume
    cellAtomsCopy = np.array([],dtype=np.int) # number of atoms in cell
    atomNames     = []                        # name of atoms in cell

    """ Templates:
        according to vasp.wiki:
          direct coords are for 6th lines starting with 'D' or 'd'
      carthesian coords are for 6th lines starting with 'C', 'c', 'K' or 'k' """
    directTemplate     = "Dd"
    carthTemplate      = "CcKk"
    selectiveTemplate  = "Ss"

    # additional variables
    cellAtoms     = np.array([],dtype=np.int)
    cellSize = 1
    cellInputType = 'x'
    ISDIRECT = -1 
    invDirections = []  # inverted crystal directions
    offset = 0
    with open(inputName,"r+") as inFile:
        for i,raw in enumerate(inFile.readlines()):
            line = re.sub("^\s*","",raw)  # remove all blank characters from begining of the line
            line = re.sub("\s+"," ",line) # replace all blank characters in a row to a single space
            if i == 0:
                comment = line[:-1]
            elif i == 1:
                scale = np.float64(line[:-1]) # scaling factor
                if(scale < 0.0):
                    scale = 1.0
            elif i in range(2,5):
                try:
                    directions.append(scale*np.fromstring(line,sep=" ")) # crystal directions
                except:
                    print("Error reading file %s in line %d:\nCan't convert crystal directions."%(inputName,i))
                    exit(-2)
                if(len(directions[-1]) != 3):   
                    print("Error reading file %s in line %d:\nCrystal directions has %d != 3 dimensions!"%(inputName,i,len(directions[-1])))
                    exit(-3)
                cellSymmetry[0].append(tuple(directions[-1]))
                cellCenter += 0.5*directions[-1]
            elif i == 5:
                cellVolume = np.abs(np.linalg.det(np.array(directions)))
                try:
                    invDirections = np.linalg.inv(directions)
                except:
                    print("Error reading file %s in line %d:\nCrystal directions are not basis in 3D!"%(inputName,i))
                    exit(-4)
                if re.match("\D",line):
                    offset += 1
                    atomNames=line[:-1].split(" ")
                else:    
                    cellAtoms = np.fromstring(line,sep=" ",dtype=np.int)
                    cellAtomsCopy = np.copy(cellAtoms)
                    cellSize = np.sum(cellAtoms)
            if i == 6 and offset == 1:
                cellAtoms = np.fromstring(line,sep=" ",dtype=np.int)
                cellAtomsCopy = np.copy(cellAtoms)
                cellSize = np.sum(cellAtoms)
            elif i == 6 + offset:
                cellInputType = line[0]
                if cellInputType in carthTemplate:
                    ISDIRECT = False
                elif cellInputType in directTemplate:
                    ISDIRECT = True
                elif cellInputType in selectiveTemplate:
                    offset += 1
                else:
                    print("Error in POSCAR: unknown input in line %d: %s"%(i,line[:-1]))
                    exit(-1)
            elif ISDIRECT == -1 and i == 7:
                cellInputType = line[0]
                if cellInputType in carthTemplate:
                    ISDIRECT = False
                elif cellInputType in directTemplate:
                    ISDIRECT = True
                else:
                    print("Error in POSCAR: unknown input in line %d: %s"%(i,line[:-1]))
                    exit(-1)
            elif i in range(7+offset,7+offset+cellSize):
                found = re.search("([\-\+]?\d+\.?\d*)\s([\-\+]?\d+\.?\d*)\s([\-\+]?\d+\.?\d*)",line)
                if found:
                    atomType = np.flatnonzero(cellAtoms)
                    cellAtoms[atomType[0]] -= 1
                    atom  = [atomType[0],np.zeros(3)]
                    coords = np.fromstring(found.group(0),sep=" ")
                    if ISDIRECT:
                        cellSymmetry[1].append(tuple(coords))
                        for coord,vector in zip(coords,directions):
                            atom[1] += coord*vector 
                    else:
                        cellSymmetry[1].append(tuple(np.dot(coords,invDirections)))
                        atom[1] = coords
                    cell.append(atom)    
                    cellSymmetry[2].append(atomType[0])
                found = re.search("[\-\+]?\d+\.?\d*\s[\-\+]?\d+\.?\d*\s[\-\+]?\d+\.?\d*\s([a-zA-Z]+)",line)
                if found:
                    if found.group(1) not in atomNames:
                        atomNames.append(found.group(1))
                    
    for i,e in enumerate(cellSymmetry[2]):
        cellSymmetry[2][i] = periodicTableNumber[atomNames[e]]

    data['comment']       = comment
    data['directions']    = directions
    data['cell']          = cell
    data['cellSymmetry']  = cellSymmetry
    data['cellVolume']    = cellVolume
    data['cellCenter']    = cellCenter
    data['cellAtoms']     = cellAtomsCopy
    data['atomNames']     = atomNames
    return data 

#
#
#
#
#

