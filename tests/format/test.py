#!/usr/bin/python3
# -*- coding: utf-8 -*-

from sys import path
path.insert(0,r'../../')
import time
import numpy as np

from JorG.format import standard,color
from JorG.format import print_vector
from JorG.format import print_atom
from JorG.format import print_case

def main(**args):
    pass

def line():
    print(92*'+')

if __name__ == '__main__':
    tracker  = -(time.time())

    print("Test of kwargs fixing:")
    testkwargs = {'linewidth' : 99, 'nonexistent' : 'yetIexist'}
    print(testkwargs)
    testkwargs = standard.fix(**testkwargs)
    print(testkwargs)
    line()

    print("Test of print_vector(",end="")
    vector = [0.1, 0.11, 0.111]
    print(vector,end=")\n")
    print("\tplain:")
    print_vector(vector)
    print("\twith vectorStyle=color.BF:")
    print_vector(vector,vectorStyle=color.BF)
    print("\twith linewidth=23:")
    print_vector(vector,linewidth=23)
    print("\twith end=\'\\nSTOP\\n\':")
    print_vector(vector,end='\nSTOP\n')
    line()

    print("Test of print_atom(",end="")
    atom = ["Cu",np.zeros(3)]
    print(atom,end=")\n")
    print("\tplain:")
    print_atom(atom)
    print("\twith vectorStyle=color.BF:")
    print_atom(atom,vectorStyle=color.BF)
    print("\twith elementStyle=color.DARKRED")
    print_atom(atom,elementStyle=color.DARKRED)
    print("\twith end=\'\\nSTOP\\n\':")
    print_atom(atom,end='\nSTOP\n')
    line()

    print("Test of print_case(",end="")
    case = [1, ["Cu",np.zeros(3)], 12]
    print(*case,end=")\n")
    print("\tplain:")
    print_case(*case)
    print("\twith caseStyle=color.BF:")
    print_case(*case,caseStyle=color.BF)
    print("\twith numberStyle=color.BF:")
    print_case(*case,numberStyle=color.BF)
    print("\twith distanceStyle=color.BF:")
    print_case(*case,distanceStyle=color.BF)
    print("\twith wyckoffPostion=\'a\':")
    print_case(*case,wyckoffPostion='a')
    print("\twith distance=1.23")
    print_case(*case,distance=1.23)
    print("\twith end=\'\\nSTOP\\n\':")
    print_case(*case,end='\nSTOP\n')
    line()
    

    tracker += time.time()
    print("Runtime of %02d:%02d:%02d.%09d"%(int(tracker/3600),int(tracker/60),int(tracker),int(1e9*tracker)))
    exit(0)