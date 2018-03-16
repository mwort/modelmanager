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
from modelmanager import utils

test_variable = 123
test_relpath = 'mm/settings.py'

def test_function(project, d=1):
    dd = d + 1
    return dd

class TestPlugin:
    test_plugin_variable = 456

    def __init__(self, project):
        self._project = project
        self.test_project_variable = project.test_variable
        return

    def test_method(self, testarg):
        self._project.test_variable
        return testarg

@property
def test_property(project):
    return project.projectdir

@utils.propertyplugin
class result:
    plugin_functions = ['plot']
    def __init__(self, project):
        pass
    def plot(self):
        return 'a-plot'
"""


def create_project(projectdir, settingsstr):
    os.makedirs(projectdir)
    project = mm.project.setup(projectdir=projectdir)
    with open(project.settings.file, 'w') as f:
        f.write(settingsstr)
    project.settings.load()
    return project


class ProjectTestCase(unittest.TestCase):
    """Abstract class to initialise and clean a default project."""

    projectdir = 'testmodel'

    def setUp(self):
        self.project = create_project(self.projectdir, TEST_SETTINGS)
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

    def test_plugin(self):
        self.assertEqual(self.project.testplugin.test_plugin_variable, 456)
        self.assertEqual(self.project.testplugin.test_project_variable, 123)

    def test_property(self):
        self.assertEqual(self.project.test_property, self.project.projectdir)
        self.assertIn('settings.result', str(self.project.result.__class__))
        self.assertIn('plot', self.project.settings.plugins['result'][1])

    def test_override(self):
        self.project.settings.load(test_variable=321)
        self.assertEqual(self.project.test_variable, 321)
        self.assertEqual(self.project.testplugin.test_project_variable, 321)

    def test_abspath(self):
        self.assertTrue(os.path.exists(self.project.test_relpath))
        sw = self.project.test_relpath.startswith(self.project.projectdir)
        self.assertTrue(sw)

    def test_str_retrieval(self):
        dottedpath = 'testplugin.test_plugin_variable'
        self.assertTrue(self.project.settings.is_valid('test_variable'))
        self.assertEqual(self.project.settings['test_variable'], 123)
        self.assertTrue(self.project.settings.is_valid(dottedpath))
        self.assertEqual(self.project.settings[dottedpath], 456)

    def test_undefined(self):
        with self.assertRaises(mm.settings.SettingsUndefinedError):
            self.project.someundefinedsetting
        with self.assertRaises(mm.settings.SettingsUndefinedError):
            self.project.someundefinedsetting()
        with self.assertRaises(AttributeError):
            self.project.someundefinedsetting

    def test_function_introspection(self):
        def test_function(project, d=1):
            w = project.test_variable + project.test_session_variable
            return w
        self.project.settings(test_function)
        func = self.project.settings.functions['test_function']
        self.assertEqual(func.optional_arguments, ['d'])
        self.assertEqual(func.project_instance_name, 'project')
        usedvars = ['test_session_variable', 'test_variable']
        self.assertEqual(func.attributes_used, usedvars)
        self.assertEqual(func.project, self.project)
        self.assertIsNone(func.plugin)
        self.assertFalse(func.configured)
        self.project.settings(test_session_variable=2)
        self.assertTrue(func.configured)
        pi, pimethods = self.project.settings.plugins['testplugin']
        func = pimethods['test_method']
        self.assertEqual(func.positional_arguments, ['testarg'])
        self.assertEqual(func.project_instance_name, 'self._project')
        self.assertEqual(func.attributes_used, ['test_variable'])
        self.assertEqual(func.project, self.project)
        self.assertEqual(func.plugin, pi)
        self.assertTrue(func.configured)
        # lazy testing the settings.check output
        self.project.settings.check()


class CommandlineInterface(ProjectTestCase):
    def test_function(self):
        os.chdir(self.projectdir)
        proc = subprocess.Popen(['modelmanager', 'test_function', '--d=2'],
                                stdout=subprocess.PIPE)
        lns = [l.rstrip() for l in proc.stdout.readlines()]
        self.assertEqual(len(lns), 1)
        self.assertEqual(lns, [b'3'])
        os.chdir('..')

    def test_plugin_method(self):
        os.chdir(self.projectdir)
        args = ['modelmanager', 'testplugin', 'test_method', '2']
        proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        lns = [l.rstrip() for l in proc.stdout.readlines()]
        self.assertEqual(len(lns), 1)
        self.assertEqual(lns, [b'2'])
        os.chdir('..')


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
