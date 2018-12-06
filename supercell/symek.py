#!/usr/bin/python3
# -*- coding: utf-8 -*-

from sys import argv
from sys import maxsize
from os import system,environ
import re
from datetime import datetime
import numpy as np
import spglib
from aux.periodic import *
from aux.symmetry import *
from aux.format import *
from aux.argv import options
from JorG.loadsave import * 
from JorG.generator import * 


def main(**args):
    pass

if __name__ == '__main__':
    
    currentOptions = options(*argv)
    POSCARfile     = currentOptions('input')
    INCARfile      = currentOptions('incar')
    cutOff         = currentOptions('cutOff')
    nearestNeighbor= currentOptions('neighbor')  
    atomTypeMask   = currentOptions('mask')  
    reference      = currentOptions('reference')
    SYMMETRYRUN    = currentOptions('symmetry')
    USEREFINED     = currentOptions('refined')
    wyckoffs       = currentOptions('Wyckoffs')
    outDirName     = currentOptions('output')
   
    if outDirName == None:
      # if output directory is not given:  
      outDirName = "output/"+datetime.now().strftime("%Y%m%d%H%M%S")
    else:
      # remove multiple '/' and possible '/' at the end  
      outDirName = re.sub('/+','/',outDirName)
      outDirName = re.sub('/$','',outDirName)

    # cr4eating output path
    temporaryName = ""
    for partOfOutput in re.split('/',outDirName):
      temporaryName += partOfOutput
      system("mkdir -p %s"%temporaryName)
      temporaryName += "/"

    # clean output path ? SHOULD WE?
#    system("rm -r "+temporaryName+"*")
    """ Reading POSCAR and INCAR files.
          TODO: bulletproofing """
#    
    readData             = load_POSCAR(POSCARfile)
    oldMoments,incarData = load_INCAR (readData['cell'],INCARfile)
#    
    cell          = readData['cell']
    cellSymmetry  = readData['cellSymmetry']
    atomNames     = readData['atomNames']
    comment       = readData['comment']
    directions    = readData['directions']
    cellVolume    = readData['cellVolume']
    cellCenter    = readData['cellCenter']
    cellAtoms     = readData['cellAtoms']

    referenceAtom = None
    if reference >= 0:
      referenceAtom = cell[reference]
    else:
      for i,atom in enumerate(cell):  
        if "$"+atomNames[atom[0]]+"$" in atomTypeMask:  
          referenceAtom = atom
          reference = i
          break
    if referenceAtom is None:
      print("Error: can not find any atoms (%s) in input file!"%re.sub('\$','',atomTypeMask))
      exit(-7)
    
    print("The reference was chosen to be atom No. %d:\n"%(reference+1)+color.BF+color.YELLOW+"%s"%(atomNames[referenceAtom[0]])+color.END+' [ '+color.DARKCYAN+"% 2.5f % 2.5f % 2.5f"%(*referenceAtom[1],)+color.END+' ]')

    if USEREFINED: 
        refinedCell = (spglib.standardize_cell(cellSymmetry,
                                               to_primitive=0,
                                               no_idealize=0,
                                               symprec=1e-1))
        directions = np.array(refinedCell[0])
        for refinedAtom in refinedCell[1]:
            newPosition = np.zeros(3)
            for x,d in zip(refinedAtom,refinedCell[0]):
                newPosition += x*np.array(d)
            for atom in cell:
                if np.linalg.norm(atom[1] - newPosition) <= 1e-1:
                    atom[1] = newPosition
                    continue
    """

        Printing input data


    """

    print_moments(oldMoments)
    print_label("INPUT")
    print_crystal(directions,cell,atomNames=atomNames)

    """ 
    
        Generating output


    """
    if nearestNeighbor is None:
        nearestNeighbor = maxsize

    if cutOff is None:
        if nearestNeighbor is None:
            nearestNeighbor = 1
        (cutOff,
         crystal,
         symmetryFull, 
         newReference, 
         copiesInEachDirection,
         wyckoffDict) = generate_from_NN(cell,
                                         referenceAtom,
                                         directions,
                                         nearestNeighbor,
                                         atomNames,
                                         wyckoffs,
                                         atomTypeMask,
                                         moments=oldMoments)
        extraDirections = [(mul+1)*d 
                           for mul,d in
                           zip(copiesInEachDirection,
                               directions)]
    else:
        copiesInEachDirection = get_number_of_pictures(directions,cutOff,referenceAtom)
        extraDirections = [(mul+1)*d 
                           for mul,d in
                           zip(copiesInEachDirection,
                               directions)]
        crystal, newReference =\
                generate_crystal(copiesInEachDirection,
                                 cell,
                                 directions,
                                 atomNames,
                                 reference=reference,
                                 moments=oldMoments)
        wyckoffDict, symmetryFull, symmetryOriginal = wyckoffs_dict(cell, 
                                                      crystal,
                                                      directions,
                                                      extraDirections,
                                                      atomNames)        
#    
    """ Checking the symmetry 
                    of the output """
    write_report(["Analysis of symmetry in the generated cell"],
                 [symmetryFull],
                 crystal,
                 outDirName+"/output_report.txt");
    save_POSCAR(outDirName+"/POSCAR",
                crystal,
                copiesInEachDirection,
                readData)

    print_label("OUTPUT")
    print_crystal(extraDirections,crystal)

    
    """
        Searching for unique atoms for calculations
                                                    """
    logAccuracy  = 2     #  accuracy of distance is 10^(-logAccuracy)
    
    from JorG.equivalent import find_unique_flips
    flipper = find_unique_flips(crystal[newReference],crystal,
                                symmetryFull,cutOff,
                                atomTypeMask,Wyckoffs=wyckoffs,
                                wyckoffDict=wyckoffDict,
                                logAccuracy=logAccuracy)
    
    caseID = 1
    selected = [newReference]
    print("Reference atom in the new system is No. %d:"%newReference)
    print_atom(crystal[newReference],vector=color.DARKCYAN)
    for (i,atom,distance,wyck) in flipper:
        if caseID <= nearestNeighbor:
            print_case(caseID,atom,i+1,wyck,distance)
            selected.append(i)
            caseID += 1
                
    if nearestNeighbor < len(flipper) :
        save_INCAR(outDirName,incarData,crystal,flipper[:nearestNeighbor])    
    else:
        save_INCAR(outDirName,incarData,crystal,flipper)    

    crystal8 = apply_mirrorsXYZ(extraDirections,crystal,
                                cutOff=cutOff,
                                reference=newReference)
    save_xyz   (outDirName+"/crystal.xyz",crystal,selectedAtoms = selected)
    save_xyz   (outDirName+"/crystalFull.xyz",crystal8,selectedAtoms = selected)
    system ("sed  -e 's/XXXXX/%f/g' -e 's/YYYYY/%f/g' -e 's/ZZZZZ/%f/g' -e 's/RRRRR/%f/g' script.template> %s"%(*crystal[newReference][1],cutOff,outDirName+"/script.jmol"))

    from JorG.equivalent import find_all_flips
    allFlippable = find_all_flips(crystal[newReference],crystal,
                                symmetryFull,cutOff,
                                atomTypeMask,Wyckoffs=wyckoffs,
                                wyckoffDict=wyckoffDict,
                                logAccuracy=logAccuracy)
 
    size = len(flipper['distance'])
    print(cutOff,flipper['distance'])
    from itertools import product
    for option in product([1,-1],repeat=len(allFlippable)):
        print(option)
        penalty = {distance: 0 for distance in flipper['distance']} 
        for i,flip1 in enumerate(option):
            if flip1 < 0:
                for (a,b) in product(range(0,8),repeat=2):
                    d = np.round(
                          np.linalg.norm(
                            crystal8[newReference+len(crystal)*a][1]
                           -crystal8[allFlippable[i]+len(crystal)*b][1]
                          ),
                        logAccuracy)
                    if d <= cutOff:
                        if d not in penalty.keys():
                            penalty[d] = 1
                        else:    
                            penalty[d] += 1
            for j,flip2 in enumerate(option):
                if(j < i):
                    if flip1*flip2 < 0:
                        for (a,b) in product(range(0,8),repeat=2):
                            d = np.round(
                                  np.linalg.norm(
                                    crystal8[allFlippable[i]+len(crystal)*a][1]
                                   -crystal8[allFlippable[j]+len(crystal)*b][1]
                                  ),
                                logAccuracy)
                            if d <= cutOff:
                                if d not in penalty.keys():
                                    penalty[d] = 1
                                else:    
                                    penalty[d] += 1
        print(penalty)
