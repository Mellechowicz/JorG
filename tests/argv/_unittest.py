import unittest
from argv import options

class TestArgv(unittest.TestCase):
    def set_up(self,input):
        self.currentOptions = options(*input.split())
        self.MASK     = str(self.currentOptions('mask'))
        self.OUTPUT   = self.currentOptions('output')
        self.INCAR    = self.currentOptions('incar')
        self.POSCAR   = self.currentOptions('input')
        self.NEIGHBOR = self.currentOptions('neighbor')

    def check_type(self,*args,isType):
        for arg in args:
            self.assertIsInstance(arg,isType)

    def check_bools(self):
        self.check_type(self.currentOptions('symmetry'),
                        self.currentOptions('redundant'),
                        self.currentOptions('refined'),isType=bool)

    def check_in(self,where,*args):
        for arg in args:
            self.assertIn(arg,where)

    def test_input_001(self):
        input="foo --incar INCAR --input POSCAR -N 3 -E Fe"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,3)
        self.assertEqual(self.POSCAR,'POSCAR')
        self.assertEqual(self.INCAR,'INCAR')
        self.check_in(self.MASK,"Fe")

    def test_input_002(self):
        input="foo --incar INCAR --input POSCAR -N 13 -E Ni"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,13)
        self.assertEqual(self.POSCAR,'POSCAR')
        self.assertEqual(self.INCAR,'INCAR')
        self.check_in(self.MASK,"Ni")

    def test_input_003(self):
        input="foo --incar INCAR --input POSCAR -N 3 -E Ni"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,3)
        self.assertEqual(self.POSCAR,'POSCAR')
        self.assertEqual(self.INCAR,'INCAR')
        self.check_in(self.MASK,"Ni")
        self.assertGreater(self.NEIGHBOR,0)

    def test_input_004(self):
        input="foo --incar INCAR_tst1 --input POSCAR_tst1 -N 3 -E Fe"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,3)
        self.assertEqual(self.POSCAR,'POSCAR_tst1')
        self.assertEqual(self.INCAR,'INCAR_tst1')
        self.check_in(self.MASK,"Fe")
        self.assertGreater(self.NEIGHBOR,0)

    def test_input_005(self):
        input="foo --symmetry -i POSCAR_Cs2F6Ni2 "
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.currentOptions('reference'),isType=int)
        self.assertIsNone(self.NEIGHBOR)
        self.assertEqual(self.POSCAR,'POSCAR_Cs2F6Ni2')
        self.assertEqual(self.currentOptions('symmetry'),True)

    def test_input_006(self):
        input="foo -i POSCAR_tst1 "
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.currentOptions('reference'),isType=int)
        self.assertIsNone(self.NEIGHBOR)
        self.assertEqual(self.POSCAR,'POSCAR_tst1')
        self.assertEqual(self.INCAR,'_INPUT/INCAR')
        self.check_in(self.MASK,"Mn")

    def test_input_007(self):
        input="foo --incar INCAR_tst1 --input POSCAR_tst1 -N 2 -E Fe1"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,2)
        self.assertEqual(self.POSCAR,'POSCAR_tst1')
        self.assertEqual(self.INCAR,'INCAR_tst1')
        self.check_in(self.MASK,"Fe")

    def test_input_008(self):
        input="foo --incar _INCARs/INCAR_tst1 --input _POSCARs/POSCAR_tst1 -N 1 -E Fe1"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,1)
        self.assertEqual(self.POSCAR,'_POSCARs/POSCAR_tst1')
        self.assertEqual(self.INCAR,'_INCARs/INCAR_tst1')
        self.check_in(self.MASK,"Fe")

    def test_input_009(self):
        input="foo --incar _INCARs/INCAR_CsNiF --input _POSCARs/POSCAR_CsNiF -N 1 -E Ni -o output/J1"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.OUTPUT,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,1)
        self.assertEqual(self.POSCAR,'_POSCARs/POSCAR_CsNiF')
        self.assertEqual(self.INCAR,'_INCARs/INCAR_CsNiF')
        self.assertEqual(self.OUTPUT,'output/J1')
        self.check_in(self.MASK,"Ni")

    def test_input_010(self):
        input="foo --symmetry -i _POSCARs/POSCAR_CsNiF -I _INCARs/INCAR_CsNiF "
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.currentOptions('reference'),isType=int)
        self.assertIsNone(self.NEIGHBOR)
        self.assertEqual(self.POSCAR,'_POSCARs/POSCAR_CsNiF')
        self.assertEqual(self.INCAR,'_INCARs/INCAR_CsNiF')
        self.check_in(self.MASK,"Fe")
        self.assertEqual(self.currentOptions('symmetry'),True)

    def test_input_011(self):
        input="foo -i _POSCARs/POSCAR_CsNiF -I _INCARs/INCAR_CsNiF -N 6 -E Ni -o output/ASD --redundant"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.OUTPUT,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,6)
        self.assertEqual(self.POSCAR,'_POSCARs/POSCAR_CsNiF')
        self.assertEqual(self.INCAR,'_INCARs/INCAR_CsNiF')
        self.assertEqual(self.OUTPUT,'output/ASD')
        self.check_in(self.MASK,"Ni")
        self.assertEqual(self.currentOptions('redundant'),True)

    def test_input_012(self):
        input="foo -i _POSCARs/POSCAR_CsNiF -I _INCARs/INCAR_CsNiF -E Ni -o output/ASD --reference 21 -R 123.0"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.OUTPUT,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.currentOptions('reference'),isType=int)
        self.assertEqual(self.POSCAR,'_POSCARs/POSCAR_CsNiF')
        self.assertEqual(self.INCAR,'_INCARs/INCAR_CsNiF')
        self.assertEqual(self.OUTPUT,'output/ASD')
        self.check_in(self.MASK,"Ni")
        self.assertEqual(self.currentOptions('reference'),21-1)
        self.check_type(self.currentOptions('cutOff'),isType=float)
        self.assertAlmostEqual(self.currentOptions('cutOff'),123.0)

    def test_input_013(self):
        input="foo -i _POSCARs/POSCAR_CsNiF -I _INCARs/INCAR_CsNiF -N 2 -E Ni -o output/ASD --refined"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.OUTPUT,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,2)
        self.assertEqual(self.POSCAR,'_POSCARs/POSCAR_CsNiF')
        self.assertEqual(self.INCAR,'_INCARs/INCAR_CsNiF')
        self.assertEqual(self.OUTPUT,'output/ASD')
        self.check_in(self.MASK,"Ni")
        self.assertEqual(self.currentOptions('refined'),True)

    def test_input_014(self):
        input="foo -i _POSCARs/POSCAR_CsNiF -I _INCARs/INCAR_CsNiF -N 2 -E Ni -o output/ASD  --period 3d 5p"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.OUTPUT,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,2)
        self.assertEqual(self.POSCAR,'_POSCARs/POSCAR_CsNiF')
        self.assertEqual(self.INCAR,'_INCARs/INCAR_CsNiF')
        self.assertEqual(self.OUTPUT,'output/ASD')
        self.check_in(self.MASK,"Ni","Ti","Mn","Te","In")

    def test_input_015(self):
        input="foo -i _POSCARs/POSCAR_CsNiF -I _INCARs/INCAR_CsNiF -N 2 -E Ni -o output/ASD  --block D"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.OUTPUT,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,2)
        self.assertEqual(self.POSCAR,'_POSCARs/POSCAR_CsNiF')
        self.assertEqual(self.INCAR,'_INCARs/INCAR_CsNiF')
        self.assertEqual(self.OUTPUT,'output/ASD')
        self.check_in(self.MASK,"Ni","Fe","Au","Hg","Cr","Hf")

    def test_input_016(self):
        input="foo -i _POSCARs/POSCAR_CsNiF -I _INCARs/INCAR_CsNiF -N 2 -E Ni -o output/ASD  --group 2 5"
        self.set_up(input)
        self.check_type(self.POSCAR,self.INCAR,self.OUTPUT,self.MASK,isType=str)
        self.check_bools()
        self.check_type(self.NEIGHBOR,self.currentOptions('reference'),isType=int)
        self.assertGreater(self.NEIGHBOR,0)
        self.assertEqual(self.NEIGHBOR,2)
        self.assertEqual(self.POSCAR,'_POSCARs/POSCAR_CsNiF')
        self.assertEqual(self.INCAR,'_INCARs/INCAR_CsNiF')
        self.assertEqual(self.OUTPUT,'output/ASD')
        self.check_in(self.MASK,"Ni","Be","Mg","Ca","Nb","Ta")

if __name__ == '__main__':
    unittest.main()
