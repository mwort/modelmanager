import unittest
import sys,os

import modelmanager as mm

class ModelTester(unittest.TestCase):
    def setUp(self):
        self.testfile = 'test.tmp'
        f = file(self.testfile,'w')
        f.write('hi')
        f.close()
    def tearDown(self):
        os.remove(self.testfile)

class ModelTestCase(ModelTester):
    def test_sayhi(self):
        self.assertEqual(mm.sayhi(),'hi')

    def test_readhi(self):
        firstline = file(self.testfile).readlines()[0]
        print(firstline)
        self.assertEqual(firstline,'hi')


if __name__ == '__main__':
    unittest.main()
