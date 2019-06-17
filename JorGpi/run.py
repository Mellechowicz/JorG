# -*- coding: utf-8 -*-
from sys import path
path.insert(0,r'../../')
from os import makedirs
from subprocess import call
import errno
import re
from datetime import datetime
import numpy as np
import spglib
import time
import shutil
from itertools import product

import JorG.symmetry
from JorG.argv import options
from JorG.format import print_case
import JorG.loadsave as loadsave
import JorG.generator as generator
from JorG.equivalent import findFlips

from JorG.pickup import EquationSolver,NaiveHeisenberg

from WiP.WiP import StreamHandler,JmolVisualization
from WiP.WiP import TemporaryFiles,errors,Msg
from WiP.WiP import VariableFixer,Symmetry

class JorGpi:
    def __init__(self,*args):
        self.currentOptions  = options(*args)
        self.cutOff          = self.currentOptions('cutOff')
        self.nearestNeighbor = self.currentOptions('neighbor')
        self.reference       = self.currentOptions('reference')
        self.outDirName      = self.currentOptions('output')
        self.extraMultiplier = np.zeros(3,dtype=int)
    
        self.handler    = StreamHandler(self.outDirName)
        self.outDirName = self.handler()
    
    #   Reading POSCAR and INCAR files
        self.readData,self.oldMoments,self.incarData =\
                self.handler.load_VASP(self.currentOptions('input'),
                                       self.currentOptions('incar'))
        self.cell          = self.readData['cell']
        self.atomNames     = self.readData['atomNames']
        self.comment       = self.readData['comment']
        self.directions    = self.readData['directions']
        self.referenceAtom,self.reference =\
                VariableFixer.fix_reference(self.reference,self.cell,
                                            self.currentOptions('mask'))
        self.symmetry      = Symmetry(self.readData['cellSymmetry'])
        self.logAccuracy   = 2  # accuracy of e.g. 2 digits

    #   Setting options
        if self.currentOptions('symmetry'):
            self.symmetry_run()
            exit(0)
        if self.currentOptions('refined'):
            refinedCell               = self.symmetry.standarize()
            self.cell,self.directions = VariableFixer.from_refined(refinedCell) 

    def symmetry_run(self):
#   Checking the symmetry of the input
        symmetryStandard,symmetryRefined = self.symmetry.get_standarized()
        JorG.symmetry.write_report(["(1) the crude input cell",
                                    "(2) the standarized cell",
                                    "(3) the refined cell"],
                [self.symmetry.symmetry,symmetryStandard,symmetryRefined],self.cell)

    def write_input_raport(self):
        with open(self.outDirName+"/input_report.txt",'w+') as raport:
            JorG.symmetry.write_report(["Analysis of symmetry in the input cell"],
                                       [self.symmetry.symmetry], self.cell, stream=raport)
        Msg.print_crystal_info(title="INPUT",crystal=self.cell,directions=self.directions,
                               reference=self.reference,moments=self.oldMoments)
                 
    def initialize_new_cell(self):
        self.nearestNeighbor,\
                self.cutOff = VariableFixer.fix_neighbor(self.nearestNeighbor,self.cutOff)
        if self.cutOff is None:
            self.prepare_cell_from_NN()
        else:
            self.prepare_cell_from_RR()
        self.search_for_flipps()
        self.write_output_raport()

    def prepare_cell_from_NN(self):
        generatorNN = generator.NearestNeighborsGenerator(self.cell,self.referenceAtom,self.directions)
        generatorNN.wyckoffs         = self.currentOptions('Wyckoffs')
        generatorNN.atomTypeMask     = self.currentOptions('mask')
        generatorNN.moments          = self.oldMoments
        generatorNN.extraMultiplier  = self.extraMultiplier

        try:
            (self.cutOff, self.crystal,
             self.symmetryFull, self.newReference,
             self.copiesInEachDirection, self.wyckoffDict) = generatorNN(self.nearestNeighbor)
        except Exception:
            print("Failed to generate crystal")
            exit(errors.failed_to_generate)
        self.extraDirections =\
                VariableFixer.fix_directions(self.copiesInEachDirection,self.directions)

    def prepare_cell_from_RR(self):
        self.copiesInEachDirection =\
                generator.get_number_of_pictures(self.directions,
                                                 self.cutOff,
                                                 self.referenceAtom)
        localGenerator =\
                generator.CrystalGenerator(self.cell, self.directions,
                                           self.atomNames,reference=self.reference)
        localGenerator.moments          = self.oldMoments
        self.crystal, self.newReference = \
                localGenerator(self.copiesInEachDirection)
        self.extraDirections            = \
                VariableFixer.fix_directions(self.copiesInEachDirection,self.directions)
        self.wyckoffDict, self.symmetryFull, self.symmetryOriginal =\
           generator.wyckoffs_dict(
                   generator.NearestNeighborsGenerator.get_symmetry(self.cell,
                                                                    self.directions), 
                   generator.NearestNeighborsGenerator.get_symmetry(self.crystal,
                                                                    self.extraDirections))

    def search_for_flipps(self):
#        Searching for unique atoms for calculations
        flipSearch              = findFlips()
        flipSearch.symmetry     = self.symmetryFull
        flipSearch.crystal      = self.crystal
        flipSearch.atomTypeMask = self.currentOptions('mask')
        flipSearch.Wyckoffs     = self.currentOptions('Wyckoffs')
        flipSearch.wyckoffDict  = self.wyckoffDict
        flipSearch.logAccuracy  = self.logAccuracy
        self.flipper            = flipSearch.unique(self.crystal[self.newReference],self.cutOff)
        self.allFlippable       = flipSearch.all(self.crystal[self.newReference],self.cutOff)

        Msg.print_crystal_info(title="OUTPUT",crystal=self.crystal,directions=self.extraDirections,
                               copies=(*VariableFixer.add_to_all(self.copiesInEachDirection),),
                               reference=self.newReference)

    def write_output_raport(self):
    #   Checking the symmetry of the output
        with open(self.outDirName+"/output.txt",'w+') as raport:
            JorG.symmetry.write_report(["Analysis of symmetry in the generated cell"],
                         [self.symmetryFull], self.crystal, stream=raport)
        loadsave.save_POSCAR(self.readData, fileName=self.outDirName+"/POSCAR",
                             crystal=self.crystal, multiplyers=self.copiesInEachDirection)
    
        self.selected = [self.newReference]
        for caseID,(i,atom,distance,wyck) in enumerate(self.flipper):
            print_case(atom,atomID=i+1,caseID=caseID+1,wyckoffPosition=wyck,distance=distance)
            self.selected.append(i)
        self.crystal8 =\
                generator.apply_mirrorsXYZ(self.extraDirections,self.crystal,
                                           cutOff=self.cutOff, reference=self.newReference)
        loadsave.save_xyz(self.crystal, fileName=self.outDirName+"/crystal.xyz",
                          selectedAtoms = self.selected)
        loadsave.save_xyz(self.crystal8,fileName=self.outDirName+"/crystalFull.xyz",
                          selectedAtoms = self.selected)
        JmolVisualization.create_script(self.outDirName,radius=self.cutOff,
                                        center=self.crystal[self.newReference][1])

    class AdaptiveSimulatedAnnealing:
        solverDirectory = './asa/solver'
        myDirectory     = '../../'
        def __init__(self,JorGpiObject):
            self.tmpFiles = TemporaryFiles()
            self.tmpFiles.write_input(JorGpiObject.allFlippable,JorGpiObject.crystal)
            self.tmpFiles.write_supercell(JorGpiObject.crystal)
            self.tmpFiles.write_directions(JorGpiObject.extraDirections)
            Msg.print_solver_status(int(2**len(JorGpiObject.allFlippable)),self.tmpFiles)
            call('cd %s; make clean; make SITES=-D_SITESNUMBER=%d; cd %s'%(self.solverDirectory,len(JorGpiObject.crystal),self.myDirectory), shell=True)

        def __call__(self,JorGpiObject):
            call('%s/start %s %d %d'%(self.solverDirectory,str(self.tmpFiles),JorGpiObject.newReference,4*JorGpiObject.nearestNeighbor+8), shell=True)
            call('cd %s; make clean; cd %s'%(self.solverDirectory,self.myDirectory), shell=True)

        def __del__(self):
            Msg.print_solver_status(len(np.loadtxt('best.flips',bool)),self.tmpFiles)
            del self.tmpFiles

    def load_from_annealing(self):
        self.flippingConfigurations = np.loadtxt('best.flips',bool)
        try:
            np.shape(self.flippingConfigurations)[1]
        except IndexError:
            self.flippingConfigurations=[self.flippingConfigurations]

    def build_system_of_equations(self,flippingConfigurations):
        gen = NaiveHeisenberg(flippingConfigurations,self.crystal,self.crystal8)
        systemOfEquations = gen.generate(self.currentOptions('mask'),[flip[2] for flip in self.flipper])

        eqs = EquationSolver(systemOfEquations,np.zeros(len(systemOfEquations)))
        systemOfEquations = eqs.remove_tautologies()
        remover = eqs.remove_linears()
        if remover:
            flippingConfigurations = np.delete(flippingConfigurations, tuple(remover), axis=0)
            systemOfEquations = eqs.equations
        if systemOfEquations.size == 0:
            print("ERROR! Not enough equations! Please rerun.")
            exit(-3)
        if not self.currentOptions('redundant'): # If the System of Equations is required to be consistent
            systemOfEquations,flippingConfigurations = eqs.remove_linear_combinations(flippingConfigurations)
        return systemOfEquations,flippingConfigurations

    def save_result(self):
        Msg.print_equations(self.systemOfEquations,self.currentOptions('redundant'))
        np.savetxt(self.outDirName+'/systemOfEquations.txt',self.systemOfEquations)
        saver = loadsave.INCARsaver(self.incarData,self.crystal)
        saver.save(self.outDirName,self.flippingConfigurations)

    def generate_possible_configurations(self):
        solver = self.AdaptiveSimulatedAnnealing(self)
        solver(self)
        del solver
        self.load_from_annealing()
        self.systemOfEquations,self.flippingConfigurations = \
                self.build_system_of_equations(self.flippingConfigurations)
        self.save_result()


