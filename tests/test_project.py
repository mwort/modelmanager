"""Test module for the Project class."""
import unittest
import os
import shutil
import subprocess

import cProfile, pstats

import modelmanager as mm

TEST_SETTINGS = """
import os
from inspect import cleandoc as _cleandoc

test_variable = 123

def test_function(project, d=1):
    dd = d + 1
    return dd

class TestPlugin:
    test_plugin_variable = 456

    def __init__(self, project):
        self.project = project
        return

    def test_method(self, testarg):
        return testarg
"""


class ProjectTestCase(unittest.TestCase):
    """Abstract class to initialise and clean a default project."""

    projectdir = 'testmodel'

    def setUp(self):
        os.makedirs(self.projectdir)
        self.project = mm.project.setup(projectdir=self.projectdir)
        self.write_settings()
        self.project.settings.load()
        return

    def write_settings(self):
        with file(self.project.settings.file, 'w') as f:
            f.write(TEST_SETTINGS)
        return

    def tearDown(self):
        shutil.rmtree(self.projectdir)
        return


class ProjectSetup(unittest.TestCase):
    """Test multiple ways to setup a project."""

    projectdir = ProjectTestCase.projectdir

    def tearDown(self):
        shutil.rmtree(self.projectdir)
        return

    def test_initialise_with_resourcedir(self):
        crdir = 'custom_resourcedir'
        self.project = mm.project.setup(projectdir=self.projectdir,
                                        resourcedir=crdir)
        parsed_resourcedir = os.path.split(self.project.resourcedir)[-1]
        self.assertEqual(parsed_resourcedir, crdir)
        return

    def test_setup_commandline(self):
        subprocess.call(['modelmanager', 'setup',
                         '--projectdir=%s' % self.projectdir])
        return


class Settings(ProjectTestCase):
    def test_variable(self):
        self.assertEqual(self.project.test_variable, 123)

    def test_function(self):
        self.assertEqual(self.project.test_function(), 2)

    def test_class(self):
        self.assertEqual(self.project.testplugin.test_plugin_variable, 456)


class CommandlineInterface(ProjectTestCase):
    def test_function(self):
        os.chdir(self.projectdir)
        proc = subprocess.Popen(['modelmanager', 'test_function', '--d=2'],
                                stdout=subprocess.PIPE)
        lns = [l.rstrip() for l in iter(proc.stdout.readline, '')]
        self.assertEqual(len(lns), 1)
        self.assertEqual(lns, ['3'])
        os.chdir('..')

    def test_plugin_method(self):
        os.chdir(self.projectdir)
        args = ['modelmanager', 'testplugin', 'test_method', '2']
        proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        lns = [l.rstrip() for l in iter(proc.stdout.readline, '')]
        self.assertEqual(len(lns), 1)
        self.assertEqual(lns, ['2'])
        os.chdir('..')


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(10)
