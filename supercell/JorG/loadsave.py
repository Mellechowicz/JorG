import re
import numpy as np
from aux.periodic import periodicTableNumber

def load(inputName):
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
 

from itertools import permutations as per
def get_number_of_pictures(directions,cutOff):
    multiplyers = []
    
    bestScore = 0.0
    bestPermutation = (0,1,2) 
    for p in per(range(3)):
        score = 1.0
        for i,d in enumerate(directions):
            score *= d[p[i]]
        if np.abs(score) > bestScore:
            bestScore = np.abs(score)
            bestPermutation = p
    
    for d,p in zip(directions,
                   bestPermutation):
        multiplyers.append(int(cutOff/d[p]))
    
    return multiplyers

from aux.periodic import periodicTableNumber
def generate_crystal(multiplyers,cell,directions,atomNames):
    crystal = []
    cellSymmetryFull = ([],[],[])

    invDirections = np.dot(np.diag(1.0/(1.0+np.array(multiplyers))),np.linalg.inv(directions))

    for m,d in zip(multiplyers,directions):
        cellSymmetryFull[0].append((m+1)*d)

    for x in range(multiplyers[0]+1):
        for y in range(multiplyers[1]+1):
            for z in range(multiplyers[2]+1):
                for atom in cell:
                    position = np.copy(atom[1])
                    for a,n in zip([x,y,z],directions):
                        position += a*n
                    if atom[0] < len(atomNames):
                        flag = "%s"%atomNames[int(atom[0])]
                    else:    
                        flag = "%s"%periodicTable[int(atom[0])]
                    crystal.append([flag,position])    

    for atomName in atomNames:
        for atom in crystal:
            if atom[0]==atomName:
                cellSymmetryFull[1].append(tuple(np.dot(atom[1],invDirections)))
                cellSymmetryFull[2].append(periodicTableNumber[atom[0]])

    return crystal,cellSymmetryFull

def write_xyz(fileName,crystal,numberOfAtoms = -1):
    if numberOfAtoms < 0:
        numberOfAtoms = len(crystal)

    with open(fileName,"w+") as xyzFile:
        xyzFile.write(str(numberOfAtoms))
        xyzFile.write("\n\n")
        for atom in crystal:
            xyzFile.write("%s"%atom[0])
            for xyz in atom[1]:
                xyzFile.write(" %.10f"%xyz)
            xyzFile.write("\n")
        xyzFile.write("\n")


def write_POSCAR(fileName,crystal,multiplyers,data):
    with open(fileName,"w+") as vaspFile:
        vaspFile.write(data['comment'])
        vaspFile.write("\n1.0\n")
        for m,d in zip(multiplyers,data['directions']):
            for field in d: 
                vaspFile.write("  %.10f"%((m+1)*field))
            vaspFile.write("\n")
        for atomName in data['atomNames']:
            vaspFile.write("%s "%atomName)
        vaspFile.write("\n")    
        for atomNumber in data['cellAtoms']:
            vaspFile.write("%d "%(np.prod(np.array(multiplyers)+1)*atomNumber))
        vaspFile.write("\nCarthesian\n")
        for atomName in data['atomNames']:
            for atom in crystal:
                if atom[0]==atomName:
                    for vasp in atom[1]:
                        vaspFile.write(" %.10f "%vasp)
                    vaspFile.write(" %s\n"%atom[0])
        vaspFile.write("\n")

