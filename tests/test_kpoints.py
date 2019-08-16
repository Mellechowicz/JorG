from sys import path
path.insert(0,r'../')
import unittest
from utilities.KPOINTS.kpoints import KPOINTS
import numpy as np

class TestKPOINTS(unittest.TestCase):
    def test_simple_poscar(self):
        generator=KPOINTS("_INPUT/POSCAR")
        points = generator(np.sqrt(1e-3))
        for result,record in zip(points,self.dataIron):
            self.assertListEqual(result[0],record[:-1])
            self.assertAlmostEqual(result[1],record[3],places=3)
    def test_complicated_poscar(self):
        generator=KPOINTS("testData/POSCAR_exp1")
        for i,accuracy in enumerate(self.accuracies):
            points = generator(accuracy)
            for result,record in zip(points,self.dataCuprate[i]):
                self.assertListEqual(result[0],record[:-1])
                self.assertAlmostEqual(result[1],record[3],places=3)

    accuracies = [np.sqrt(1e-3),np.sqrt(1e-2),np.sqrt(1e-1),np.sqrt( 0.5),np.sqrt( 1.0)]
    dataIron = [[ 1, 1, 1,0.000], [ 2, 2, 2,0.003], [ 3, 3, 3,0.003], [ 4, 4, 4,0.003],
                [ 5, 5, 5,0.003], [ 6, 6, 6,0.003], [ 7, 7, 7,0.003], [ 8, 8, 8,0.003],
                [ 9, 9, 9,0.003], [10,10,10,0.003], [11,11,11,0.003], [12,12,12,0.003],
                [13,13,13,0.003], [14,14,14,0.003], [15,15,15,0.003], [16,16,16,0.003],
                [17,17,17,0.003], [18,18,18,0.003], [19,19,19,0.003], [20,20,20,0.003],
                [21,21,21,0.003], [22,22,22,0.003], [23,23,23,0.003], [24,24,24,0.003],
                [25,25,25,0.003], [26,26,26,0.003], [27,27,27,0.003], [28,28,28,0.003],
                [29,29,29,0.003], [30,30,30,0.003], [31,31,31,0.003], [32,32,32,0.003],
                [33,33,33,0.003], [34,34,34,0.003], [35,35,35,0.003], [36,36,36,0.003],
                [37,37,37,0.003], [38,38,38,0.003], [39,39,39,0.003], [40,40,40,0.003],
                [41,41,41,0.003], [42,42,42,0.003], [43,43,43,0.003], [44,44,44,0.003],
                [45,45,45,0.003], [46,46,46,0.003], [47,47,47,0.003], [48,48,48,0.003],
                [49,49,49,0.003], [50,50,50,0.003], [51,51,51,0.003], [52,52,52,0.003],
                [53,53,53,0.003], [54,54,54,0.003], [55,55,55,0.003], [56,56,56,0.003],
                [57,57,57,0.003], [58,58,58,0.003], [59,59,59,0.003], [60,60,60,0.003],
                [61,61,61,0.003], [62,62,62,0.003], [63,63,63,0.003], [64,64,64,0.003],
                [65,65,65,0.003], [66,66,66,0.003], [67,67,67,0.003], [68,68,68,0.003],
                [69,69,69,0.003], [70,70,70,0.003], [71,71,71,0.003], [72,72,72,0.003],
                [73,73,73,0.003], [74,74,74,0.003], [75,75,75,0.003], [76,76,76,0.003],
                [77,77,77,0.003], [78,78,78,0.003], [79,79,79,0.003], [80,80,80,0.003],
                [81,81,81,0.003], [82,82,82,0.003], [83,83,83,0.003], [84,84,84,0.003],
                [85,85,85,0.003], [86,86,86,0.003], [87,87,87,0.003], [88,88,88,0.003]]
    dataCuprate = [[[25,25, 8,0.017], [50,50,16,0.031], [78,78,25,0.007]],
                   [[19,19, 6,0.093], [22,22, 7,0.055], [47,47,15,0.069], [53,53,17,0.060],
                    [72,72,23,0.084], [75,75,24,0.046]],
                   [[ 3, 3, 1,0.240], [ 4, 4, 1,0.285], [ 7, 7, 2,0.246], [10,10, 3,0.208],
                    [13,13, 4,0.170], [16,16, 5,0.132], [28,28, 9,0.150], [29,29, 9,0.299],
                    [32,32,10,0.261], [35,35,11,0.223], [38,38,12,0.184], [41,41,13,0.146],
                    [44,44,14,0.108], [54,54,17,0.313], [56,56,18,0.298], [57,57,18,0.275],
                    [60,60,19,0.237], [63,63,20,0.199], [66,66,21,0.160], [69,69,22,0.122],
                    [81,81,26,0.208], [82,82,26,0.290], [85,85,27,0.251], [88,88,28,0.213]],
                   [[ 5, 5, 1,0.605], [ 6, 6, 2,0.478], [ 8, 8, 2,0.567], [11,11, 3,0.529],
                    [14,14, 4,0.490], [17,17, 5,0.452], [20,20, 6,0.414], [23,23, 7,0.376],
                    [24,24, 7,0.696], [26,26, 8,0.337], [27,27, 8,0.658], [30,30, 9,0.620],
                    [31,31,10,0.388], [33,33,10,0.581], [34,34,11,0.628], [36,36,11,0.543],
                    [39,39,12,0.505], [42,42,13,0.467], [45,45,14,0.428], [48,48,15,0.390],
                    [51,51,16,0.352], [52,52,16,0.672], [55,55,17,0.634], [58,58,18,0.596],
                    [59,59,19,0.538], [61,61,19,0.558], [64,64,20,0.519], [67,67,21,0.481],
                    [70,70,22,0.443], [73,73,23,0.404], [76,76,24,0.366], [77,77,24,0.687],
                    [79,79,25,0.328], [80,80,25,0.648], [83,83,26,0.610], [84,84,27,0.448],
                    [86,86,27,0.572], [87,87,28,0.686]],
                   [[ 6, 6, 1,0.926], [ 9, 9, 2,0.888], [ 9, 9, 3,0.718], [12,12, 3,0.849],
                    [12,12, 4,0.956], [15,15, 4,0.811], [18,18, 5,0.773], [21,21, 6,0.734],
                    [28,28, 8,0.978], [31,31, 9,0.940], [34,34,10,0.902], [37,37,11,0.864],
                    [37,37,12,0.866], [40,40,12,0.825], [43,43,13,0.787], [46,46,14,0.749],
                    [49,49,15,0.711], [53,53,16,0.993], [56,56,17,0.955], [59,59,18,0.916],
                    [62,62,19,0.878], [62,62,20,0.776], [65,65,20,0.840], [68,68,21,0.802],
                    [71,71,22,0.763], [74,74,23,0.725], [81,81,25,0.969], [84,84,26,0.931],
                    [87,87,27,0.893]]]
