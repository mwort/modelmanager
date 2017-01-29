"""Test module for the Project class."""
import unittest
import sys
import os
import shutil

import modelmanager as mm


class ProjectTester(unittest.TestCase):
    """Abstract class to initialise and clean a default project."""

    projectdir = 'testmodel'

    def setUp(self):
        os.makedirs(self.projectdir)
        self.pro = mm.project.initialise(projectdir=self.projectdir)
        return

    def tearDown(self):
        shutil.rmtree(self.projectdir)
        return


class ProjectSetup(unittest.TestCase):
    """Test multiple ways to setup a project."""

    projectdir = 'testmodel'

    def _mkprodir(self):
        os.makedirs(self.projectdir)

    def _tidy(self):
        shutil.rmtree(self.projectdir)

    def test_initialise_with_resourcedir(self):
        self._mkprodir()
        crdir = 'custom_resourcedir'
        self.pro = mm.project.initialise(projectdir=self.projectdir,
                                         resourcedir=crdir)
        parsed_resourcedir = os.path.split(self.pro.settings.resourcedir)[-1]
        self.assertEqual(parsed_resourcedir, crdir)
        self._tidy()
        return

    # def calling second initialise doesnt work yet
    def _initialise_with_projectdir(self):
        self._mkprodir()
        self.pro = mm.project.initialise(projectdir=self.projectdir)
        parsed_projectdir = os.path.split(self.pro.settings.projectdir)[-1]
        self.assertEqual(parsed_projectdir, self.projectdir)
        self._tidy()
        return


if __name__ == '__main__':
    unittest.main()
