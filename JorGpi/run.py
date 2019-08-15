# -*- coding: utf-8 -*-
from sys import path
path.insert(0,r'../../')
import numpy as np

import JorGpi.symmetry as symmetry
import argv
from aux.format import print_case
import JorGpi.loadsave as loadsave
import JorGpi.generator as generator
from JorGpi.equivalent import FindFlips

from heisenberg import EquationSolver,NaiveHeisenberg,apply_mirrors_xyz

from JorGpi.iohandlers import StreamHandler,JmolVisualization
from JorGpi.iohandlers import TemporaryFiles,Msg
from JorGpi.iohandlers import VariableFixer,Symmetry,read_flips
from JorGpi.crun import Crun
import shutil as su

class JorGpi:
    def __init__(self,*args):
        self.currentOptions  = argv.Options(*args)
        self.cutOff          = self.currentOptions('cutOff')
        self.nearestNeighbor = self.currentOptions('neighbor')
        self.reference       = self.currentOptions('reference')
        self.outDirName      = self.currentOptions('output')
        self.extraMultiplier = np.zeros(3,dtype=int)

        self.handler    = StreamHandler(self.outDirName)
        self.outDirName = self.handler()

    #   Reading POSCAR and INCAR files
        self.readData,self.oldMoments,self.incarData =\
                self.handler.load_vasp(self.currentOptions('input'),
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
        symmetry.WriteReport([self.symmetry.symmetry,symmetryStandard,symmetryRefined],
            comments=["(1) the crude input cell", "(2) the standarized cell", "(3) the refined cell"])
        exit()

    def write_input_raport(self):
        with open(self.outDirName+"/input_report.txt",'w+') as raport:
            symmetry.WriteReport([self.symmetry.symmetry],
                                 comments=["Analysis of symmetry in the input cell"],
                                 stream=raport)
        Msg.print_crystal_info(title="INPUT",crystal=self.cell,directions=self.directions,
                               reference=self.reference,moments=self.oldMoments)

    def initialize_new_cell(self):
        self.write_input_raport()
        self.nearestNeighbor,\
                self.cutOff = VariableFixer.fix_neighbor(self.nearestNeighbor,self.cutOff)
        if self.cutOff is None:
            self.prepare_cell_from_nn()
        else:
            self.prepare_cell_from_rr()
        self.search_for_flipps()
        self.write_output_raport()

    def prepare_cell_from_nn(self):
        generatorNN = generator.NearestNeighborsGenerator(self.cell,self.referenceAtom,self.directions)
        generatorNN.wyckoffs         = self.currentOptions('Wyckoffs')
        generatorNN.atomTypeMask     = self.currentOptions('mask')
        generatorNN.moments          = self.oldMoments
        generatorNN.extraMultiplier  = self.extraMultiplier

        generatorNN(self.nearestNeighbor)
        try:
            (self.cutOff, self.crystal,
             self.symmetryFull, self.newReference,
             self.copiesInEachDirection, self.wyckoffDict) = generatorNN(self.nearestNeighbor)
        except Exception:
            print("Failed to generate crystal:")
            exit(errors.failed_to_generate)
        self.extraDirections =\
                VariableFixer.fix_directions(self.copiesInEachDirection,self.directions)

    def prepare_cell_from_rr(self):
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
        flipSearch              = FindFlips()
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
            symmetry.WriteReport([self.symmetryFull],
                                 comments=["Analysis of symmetry in the generated cell"],
                                 stream=raport)
        self.readData['comment']="NewRef: %d, @ %s"%(self.newReference,self.crystal[self.newReference])
        loadsave.SavePOSCAR(self.readData, fileName=self.outDirName+"/POSCAR",
                            crystal=self.crystal, multiplyers=self.copiesInEachDirection)
        self.selected = [self.newReference]
        for caseID,(i,atom,distance,wyck) in enumerate(self.flipper):
            print_case(atom,atomID=i+1,caseID=caseID+1,wyckoffPosition=wyck,distance=distance)
            self.selected.append(i)
        self.crystal8 = apply_mirrors_xyz(self.extraDirections,self.crystal)
        loadsave.SaveXYZ(self.crystal, fileName=self.outDirName+"/crystal.xyz",
                          selectedAtoms = self.selected)
        loadsave.SaveXYZ(self.crystal8,fileName=self.outDirName+"/crystalFull.xyz",
                          selectedAtoms = self.selected)
        JmolVisualization.create_script(self.outDirName,radius=self.cutOff,
                                        center=self.crystal[self.newReference][1])

    class AdaptiveSimulatedAnnealing:
        solverDirectory = './asa/solver'
        myDirectory     = '../../'
        options = {'extra_compile_args': ['-std=c++17','-O3','-Wall','-Wextra','-pedantic','-fopenmp'],
                   'extra_link_args'   : ['-std=c++17','-lm','-lgsl','-lgslcblas','-fopenmp']}

        def __init__(self,JorGpiObject):
            self.options['define_macros'] = [('_SITESNUMBER', str(len(JorGpiObject.crystal)))]
            self.builder = Crun('asa/asa.cpp',
                                'asa/ising.cpp',
                                'asa/solver/solver.cpp',
                                'asa/solver/aux.cpp',
                                **self.options)
            self.tmpFiles = TemporaryFiles()
            self.tmpFiles.write_input(JorGpiObject.allFlippable,JorGpiObject.crystal)
            self.tmpFiles.write_supercell(JorGpiObject.crystal)
            self.tmpFiles.write_directions(JorGpiObject.extraDirections)
            Msg.print_solver_status(int(2**len(JorGpiObject.allFlippable)),self.tmpFiles)

        def __call__(self,jorgpiobject):
            self.builder('solver',*self.tmpFiles.get_files(),jorgpiobject.newReference,2*jorgpiobject.nearestNeighbor+4)

        def __del__(self):
            Msg.print_solver_status(len(np.loadtxt('best.flips',bool)),self.tmpFiles)
            del self.tmpFiles
            del self.builder

    def load_from_annealing(self):
        self.flippingConfigurations = read_flips()
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
        try:
            if not systemOfEquations:
                print("ERROR! Not enough equations! Please rerun.")
                exit(-3)
        except ValueError:
            if systemOfEquations.size == 0:
                print("ERROR! Not enough equations! Please rerun.")
                exit(-3)
        if not self.currentOptions('redundant'): # If the System of Equations is required to be consistent
            systemOfEquations,flippingConfigurations = eqs.remove_linear_combinations(flippingConfigurations)
        return systemOfEquations,flippingConfigurations

    def save_result(self):
        saver = loadsave.INCARsaver(self.incarData,self.crystal)
        saver.save(self.outDirName,self.flippingConfigurations)
        Msg.print_equations(self.systemOfEquations,self.currentOptions('redundant'))
        np.savetxt(self.outDirName+'/systemOfEquations.txt',np.array(self.systemOfEquations))

    def possible_configurations(self):
        try:
            su.copy('best.flips.rerun','best.flips')
        except (OSError,FileNotFoundError):
            solver = self.AdaptiveSimulatedAnnealing(self)
            solver(self)
            del solver
        self.load_from_annealing()
        self.systemOfEquations,self.flippingConfigurations = \
                self.build_system_of_equations(self.flippingConfigurations)
        self.save_result()