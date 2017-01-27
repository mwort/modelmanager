import unittest
import sys, os, shutil

import modelmanager as mm

class ProjectSetupTester(unittest.TestCase):
    projectdir = 'testmodel'

    def setUp(self):
        os.makedirs(self.projectdir)
        self.pro = mm.project.initialise(projectdir=self.projectdir)
        return

    def tearDown(self):
        shutil.rmtree(self.projectdir)
        return


class project(ProjectSetupTester):
    def test_setup(self):
        self.assertEqual(os.path.split(self.pro.settings.projectdir)[-1],
                         self.projectdir)
        return


if __name__ == '__main__':
    unittest.main()
