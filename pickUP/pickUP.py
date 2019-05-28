#!/usr/bin/python3

import numpy as np
from os import system

def main(**args):
    pass

if __name__ == '__main__':
    systemOfEquations = np.loadtxt('systemOfEquations.txt')
#    print(systemOfEquations)

    system("touch .energies.dat")
    try:
        for i in range(len(systemOfEquations)):
            system("grep 'energy  without entropy=' flip%d/OUTCAR | awk '{print $7}'>>.energies.dat"%i)
    except TypeError:
        system("grep 'energy  without entropy=' flip0/OUTCAR | awk '{print $7}'>>.energies.dat")
    system("grep 'energy  without entropy=' noFlip/OUTCAR | awk '{print $7}'>>.energies.dat")
    energies = np.loadtxt(".energies.dat")
#    print(energies)
    system("rm -f .energies.dat")

    try:
        dE = np.zeros(len(systemOfEquations))
        for i in range(len(systemOfEquations)):
            dE[i] = energies[i] - energies[-1]
        if (systemOfEquations.shape[0] == systemOfEquations.shape[1]):
            sol = np.linalg.solve(systemOfEquations,dE)
        else:
            sol = np.linalg.lstsq(systemOfEquations,dE,rcond=None)[0]

    except TypeError:
        sol = (energies[0]-energies[1])/systemOfEquations


    print("Js:")
    try:
        for s in sol:
            print(s,end=' ')
        print("")
    except:
        print(sol)
