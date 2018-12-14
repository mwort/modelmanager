"""Test module for the Project class."""
import unittest
import os
import shutil
import subprocess

import cProfile, pstats

import modelmanager as mm

TEST_SETTINGS = """
import os
from modelmanager import utils
from modelmanager.settings import parse_settings as _parse_settings

test_variable = 123
test_relpath = 'mm/settings.py'

@_parse_settings
def test_function(project, d=1, edit=False):
    dd = d + 1
    return dd

class testplugin:
    test_plugin_variable = 456

    def __init__(self, project):
        self.project = project
        self.test_project_variable = project.test_variable
        return

    @_parse_settings
    def test_method(self, testarg, setting=None):
        self.project.test_variable
        return testarg + (setting or 0)

@property
def test_property(project):
    return project.projectdir

@utils.propertyplugin
class result:
    plugin = ['plot', 'resultresult']

    @utils.propertyplugin
    class resultresult:
        plugin = ['plot', 'som']
        def __init__(self, project):
            pass
        def plot(self, kind='bar'):
            print(kind)
            return kind
        def som(self):
            print(1)
            return

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
        self.projectdir = self.project.projectdir
        self.settings = self.project.settings
        return

    def tearDown(self):
        shutil.rmtree(self.projectdir)
        # make sure properties are deleted between project creations
        for p in self.settings.properties:
            if hasattr(self.project.__class__,  p):
                delattr(self.project.__class__,  p)
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
        self.assertIn('result', self.settings.plugins)
        self.assertIn('result.plot', self.settings.functions)
        self.assertIn('result.resultresult', self.settings.plugins)
        self.assertIn('result.resultresult.plot', self.settings.functions)

    def test_override(self):
        self.settings.load(test_variable=321)
        self.assertEqual(self.project.test_variable, 321)
        self.assertEqual(self.project.testplugin.test_project_variable, 321)

    def test_abspath(self):
        self.assertTrue(os.path.exists(self.project.test_relpath))
        sw = self.project.test_relpath.startswith(self.project.projectdir)
        self.assertTrue(sw)

    def test_str_retrieval(self):
        dottedpath = 'testplugin.test_plugin_variable'
        self.assertEqual(self.settings['test_variable'], 123)
        self.assertEqual(self.settings[dottedpath], 456)
        with self.assertRaises(AttributeError):
            self.settings['some_crap']

    def test_undefined(self):
        with self.assertRaises(mm.settings.SettingsUndefinedError):
            self.project.someundefinedsetting
        with self.assertRaises(mm.settings.SettingsUndefinedError):
            self.project.someundefinedsetting()
        with self.assertRaises(AttributeError):
            self.project.someundefinedsetting
        # AttributeErrors from properties dont return SettingsUndefinedErrors
        self.project.settings(someproperty=property(lambda p: str.undefined))
        try:
            self.project.someproperty
        except Exception as e:
            self.assertNotEqual(type(e), mm.settings.SettingsUndefinedError)

    def test_function_introspection(self):
        def test_function(project, d=1):
            w = project.test_variable + project.test_session_variable
            return w
        self.settings(test_function)
        func = self.settings.functions['test_function']
        self.assertEqual(func.optional_arguments, ['d'])
        self.settings(test_session_variable=2)
        func = self.settings.functions['testplugin.test_method']
        self.assertEqual(func.positional_arguments, ['testarg'])

    def test_parse_settings(self):
        # simple function
        self.assertEqual(self.project.test_function(), 2)
        self.project.settings(test_function_d=0)
        self.assertEqual(self.project.test_function(), 1)
        # plugin.method
        self.assertEqual(self.project.testplugin.test_method(1, setting=1), 2)
        self.project.settings(testplugin_test_method_setting=1)
        self.assertEqual(self.project.testplugin.test_method(1), 2)


class CommandlineInterface(ProjectTestCase):

    def call(self, *argslist):
        argslist = ['modelmanager', '-p', self.projectdir]+list(argslist)
        proc = subprocess.Popen(argslist, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.wait()
        with proc.stderr as f:
            stderrlines = [l.rstrip().decode() for l in f.readlines()]
        print('\n'.join(stderrlines))
        with proc.stdout as f:
            stdoutlines = [l.rstrip().decode() for l in f.readlines()]
        return stdoutlines, stderrlines

    def test_function(self):
        out, err = self.call('test_function', '--d=2')
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], '3')
        self.assertEqual(len(err), 1)
        self.assertEqual(err[0], '>>> test_function(d=2)')

    def test_plugin_method(self):
        out, err = self.call('testplugin', 'test_method', '2')
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], '2')
        self.assertEqual(len(err), 1)
        self.assertEqual(err[0], '>>> testplugin.test_method(2)')
        out, err = self.call('result', 'resultresult', 'plot')
        self.assertEqual(out[0], "bar")
        self.assertEqual(err[0], ">>> result.resultresult.plot()")

    def test_flag(self):
        # short
        out, err1 = self.call('test_function', '-e')
        self.assertEqual(err1[0], '>>> test_function(edit=True)')
        # long
        out, err2 = self.call('test_function', '--edit')
        self.assertEqual(err1, err2)
        # False
        out, err3 = self.call('test_function', '--not-edit')
        self.assertEqual(err3[0], '>>> test_function()')  # False is default


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
