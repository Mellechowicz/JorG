# -*- coding: utf-8 -*-

from sys import path
path.insert(0,r'../../')
import numpy as np
np.seterr(all='raise')
from itertools import product

class EquationSolver:
    def __init__(self,equations,vector):
        self.equations = np.array(equations)
        self.vector    = np.array(vector)
        self.solution  = None

    def solve(self,**kwargs):
        if self.solution is not None:
            return self.solution
        self.solve_system_of_equations(**kwargs)
        return self.solution

    def solve_system_of_equations(self, **kwargs):
        if len(self.equations) == 1:
            self.solution = self.vector[0]/self.equations[0]
        elif self.equations.shape[0] == self.equations.shape[1]:
            print("detB = ",np.linalg.det(self.equations))
            self.solution = np.linalg.solve(self.equations,self.vector,**kwargs)
        else:
            try:
                self.solution = np.linalg.lstsq(self.equations,self.vector,rcond=None,**kwargs)[0]
            except np.linalg.LinAlgError as err:
                print("%s: see:"%str(err))
                print(self.equations.shape,self.vector.shape)
                print(self.equations)
                print(self.vector)

    def remove_tautologies(self):
        # removing 0 = 0 equations !
        scale       = np.average(np.abs(self.equations))
        tautologies = np.argwhere(
                        np.apply_along_axis(
                          np.linalg.norm,1,self.equations)/scale<1e-3).flatten()
        self.equations = np.delete(self.equations,tuple(tautologies),axis=0)
        self.vector    = np.delete(self.vector   ,tuple(tautologies))
        return self.equations,self.vector

    @staticmethod
    def is_to_be_removed(i,j,equations):
        if i == j:
            return False
        scale = np.sum(np.abs(equations))
        inner_product = np.inner(equations[i],equations[j])
        norm_i = np.linalg.norm(equations[i])
        norm_j = np.linalg.norm(equations[j])
        if np.abs(inner_product - norm_j * norm_i)/scale < 1E-8:
            return True
        return False

    def remove_linears(self):
        # Based on https://stackoverflow.com/questions/
        #                  28816627/how-to-find-linearly-independent-rows-from-a-matrix
        # We remove lineary dependent rows
        remover=set([])
        for i,j in product(range(self.equations.shape[0]),repeat=2):
            if i in remover:
                continue
            if self.is_to_be_removed(i,j,self.equations):
                remover.add(j)
        if remover:
            self.equations = np.delete(self.equations,tuple(remover),axis=0)
            self.vector    = np.delete(self.vector   ,tuple(remover))
            return remover

    def remove_linear_combinations(self, secondSystem):
        scale            = np.sum(np.abs(self.equations))
        resultantSystem  = np.array([self.equations[0]])
        gram_schmidt     = np.array([self.equations[0]])
        self.equations   = np.delete(self.equations, (0), axis=0)
        resultantSystem2 = np.array([secondSystem[0]])
        secondSystem     = np.delete(secondSystem, (0), axis=0)
        while len(resultantSystem) < self.equations.shape[1]:
            if self.equations.size == 0:
                print("ERROR! Not enough equations! Please rerun.")
                exit(-3)
            tmpVector = np.copy(self.equations[0])
            for vector in gram_schmidt:
                tmpVector -= np.inner(tmpVector,vector)*vector/np.inner(vector,vector)
            if np.linalg.norm(tmpVector)/scale > 1e-4:
                gram_schmidt     = np.vstack((gram_schmidt,tmpVector))
                resultantSystem  = np.vstack((resultantSystem,self.equations[0]))
                self.equations   = np.delete(self.equations, (0), axis=0)
                resultantSystem2 = np.vstack((resultantSystem2,secondSystem[0]))
                secondSystem     = np.delete(secondSystem, (0), axis=0)
        self.equations = resultantSystem
        return resultantSystem,resultantSystem2

class DefaultMoments:
    def __init__(self,crystal):
        self.moments = [ atom[2] for atom in crystal ]
        self.moments.insert(0,0.0)
    def __call__(self,idx=0):
        return {'energy': 0.0, 'moments': self.moments}

class HeisenbergKernel:
    def __init__(self, number_of_variables, magnetic_moments):
        self.interactionNames   = [ None ]*number_of_variables
        self.avgMomentSq        = [  0.0 ]*number_of_variables
        self._occMoments        = [  0   ]*number_of_variables
        self.avgCorrection      = [  0.0 ]*number_of_variables
        self._occCorrection     = [  0   ]*number_of_variables
        self.magneticMoments    = magnetic_moments

    def set_moments(self, magnetic_moments):
        self.magneticMoments = magnetic_moments

    def add_correction(self,field,indices):
        correction = (self.magneticMoments(field[0]+1)['moments'][indices[1]+1]
                     -self.magneticMoments(          )['moments'][indices[1]+1])\
                     /self.magneticMoments(field[0]+1)['moments'][indices[1]+1]
        moment     =  self.magneticMoments(          )['moments'][indices[0]+1]\
                     *self.magneticMoments(field[0]+1)['moments'][indices[1]+1]
        self.avgCorrection[ field[1]]  += correction
        self._occCorrection[field[1]]  += 1
        return correction*moment

    def add_interaction(self,field,indices):
        moment = self.magneticMoments(          )['moments'][indices[0]+1]\
                *self.magneticMoments(field[0]+1)['moments'][indices[1]+1]
        self.avgMomentSq[field[1]]  += np.abs(moment)
        self._occMoments[field[1]]  += 1
        return moment

    def add_name(self,index,name):
        if self.interactionNames [index] is None:
            self.interactionNames[index] = name

    @staticmethod
    def name_interaction(first,second,distance):
        return "%s-%s @%.2f"%(first,second,distance)

    def clean(self,max_size):
        remover =               [ i for  i,name in enumerate(self.interactionNames) if name is None ]
        self.interactionNames = [ name for name in self.interactionNames        if name is not None ]
        self.clear(remover)
        self.avgMomentSq      = np.array(self.avgMomentSq)  /np.array(self._occMoments)
        try:
            self.avgCorrection= np.array(self.avgCorrection)/np.array(self._occCorrection)
        except FloatingPointError:
            self.avgCorrection= np.array(self.avgCorrection)
        self.clip(max_size)
        return remover

    def clear(self,remover):
        self.avgMomentSq       = np.delete(np.array(self.avgMomentSq),   remover)
        self._occMoments       = np.delete(np.array(self._occMoments),   remover)
        self.avgCorrection     = np.delete(np.array(self.avgCorrection), remover)
        self._occCorrection    = np.delete(np.array(self._occCorrection),remover)

    def clip(self,max_size):
        self.interactionNames  = self.interactionNames[:max_size]
        self.avgMomentSq       = self.avgMomentSq     [:max_size]
        self.avgCorrection     = self.avgCorrection   [:max_size]

class MetaData:
    def __init__(self,heisenberg_kernel):
        self.names       = heisenberg_kernel.interactionNames
        self.moments     = np.sqrt(heisenberg_kernel.avgMomentSq)
        self.corrections = heisenberg_kernel.avgCorrection

class NaiveHeisenberg:
    def __init__(self,flippings,
                 crystal,crystal8):
        self.flippings       = flippings
        self.crystal         = crystal
        self.crystal8        = crystal8

    def initialize(self,mask,flipper):
        self.flipper           = np.array(flipper)
        self.mask              = mask
        self.numberOfElements  = self.mask.count('$')
        mul                    = self.numberOfElements*(self.numberOfElements + 1)//2
        self.systemOfEquations = np.zeros((len(self.flippings),len(flipper)*mul))
        self.kernel            = HeisenbergKernel(len(flipper)*mul,DefaultMoments(self.crystal))
        return mul

    def generate(self,mask,flipper):
        mul = self.initialize(mask,flipper)
        for (row,config),(I,atomI),atomJ in product(enumerate(self.flippings),
                                                    enumerate(self.crystal  ),
                                                              self.crystal8 ):
            distance,offset = self.check_if_contributes(atomI,atomJ)
            if not distance:
                continue
            j = np.argwhere(np.abs(self.flipper - distance)<1e-2)
            if not j.size:
                continue
            column = mul*j[0][0]+offset
            if config[I] == config[atomJ[3]]:
                print("aaaaaaaaa")
                self.systemOfEquations[row][column] -= self.kernel.add_correction((row,column),(atomJ[3],I))
            else:
                self.systemOfEquations[row][column] += self.kernel.add_interaction((row,column),(atomJ[3],I))
                self.kernel.add_name(column,HeisenbergKernel.name_interaction(atomI[0],atomJ[0],distance))
        self.clean_SoE()
        return self.systemOfEquations

    def set_moments(self,magnetic_moments):
        self.kernel.set_moments(magnetic_moments)

    def get_moments(self,idx=0):
        return self.kernel.magneticMoments(idx)

    def get_average_moments(self):
        return self.kernel.avgMomentSq

    def clean_SoE(self):
        remover = self.kernel.clean(len(self.flipper))
        self.systemOfEquations = np.delete(self.systemOfEquations,remover,axis=1)
        self.systemOfEquations = self.systemOfEquations[:,0:len(self.flipper)]

    def offset_from_mask(self,symbol):
        element = self.mask.find(symbol+'$')
        return self.mask.count('$',0,element)

    def combine_offsets(self,offsetA,offsetB):
        return self.numberOfElements         *(self.numberOfElements         -1)//2 \
            - (self.numberOfElements-offsetA)*(self.numberOfElements-offsetA -1)//2 + offsetB

    def check_if_contributes(self,atomI,atomJ):
        if (atomI[0] not in self.mask
        or  atomJ[0] not in self.mask):
            return False,None
        offsetI = self.offset_from_mask(atomI[0])
        offsetJ = self.offset_from_mask(atomJ[0])
        if offsetI <= offsetJ:
            offset = self.combine_offsets(offsetI,offsetJ)
        else:
            offset = self.combine_offsets(offsetJ,offsetI)
        return np.round(np.linalg.norm(atomI[1]-atomJ[1]),2),offset

    def get_metadata(self):
        return MetaData(self.kernel)

    def __str__(self):
        output = ""
        for I,i in product(range(len(self.get_moments()['moments'])),
                           range(len(self.get_moments))):
            if i == 0:
                output+="\n"
            output+="% .2f  "%self.get_moments(i)['moments'][I+1]
        output+="\n"
        return output

def apply_mirrors_xyz(dimensions,cell):
    outputCell = []
    for proj in product([-1,0,1],repeat=3):
        projection = np.array([proj])
        translation = np.dot(projection,dimensions)[0]
        for i,atom in enumerate(cell):
            outputCell.append([atom[0],atom[1]+translation,atom[2],i])
    return outputCell
