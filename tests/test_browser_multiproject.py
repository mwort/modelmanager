"""Test module for the Browser plugin."""
import unittest
import os
import shutil
import cProfile, pstats

import modelmanager as mm

from test_project import create_project

TEST_SETTINGS = """
from modelmanager.plugins.browser import Browser
"""


class MultiProject(unittest.TestCase):

    projectdirs = ['testmodel1', 'testmodel2', 'testmodel3']

    def setUp(self):

        self.projects = []
        for n in self.projectdirs:
            p = create_project(n, TEST_SETTINGS)
            # needs to be imported after django setup
            from django.conf import settings as djsettings
            print('Django configured: %s' % djsettings.configured)
            self.assertTrue(djsettings.configured)
            p = mm.Project(n)
            print('Django configured: %s' % djsettings.configured)
            self.assertTrue(djsettings.configured)
            p.browser.settings.unset()
            print('Django configured: %s' % djsettings.configured)
            self.assertFalse(djsettings.configured)
            self.projects.extend([p])
            self.assertTrue(os.path.exists(p.browser.settings.dbpath))
        return

    def tearDown(self):
        for p in self.projects:
            shutil.rmtree(p.projectdir)
        return

    def test_multi_project(self):
        self.assertNotEqual(self.projects[0], self.projects[1])


if __name__ == '__main__':
    unittest.main()
    #cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    #pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
