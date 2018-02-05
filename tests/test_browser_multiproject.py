"""Test module for the Browser plugin."""
import unittest
import os
import shutil
import cProfile, pstats

from django.conf import settings as djsettings
import modelmanager as mm
from modelmanager.plugins import browser

import test_project

test_project.TEST_SETTINGS += """
from modelmanager.plugins.browser import Browser
"""


class MultiProject(unittest.TestCase):

    projectdirs = ['testmodel1', 'testmodel2', 'testmodel3']

    def setUp(self):

        self.projects = []
        for n in self.projectdirs:
            p = test_project.create_project(n)
            print('Django configured: %s' % djsettings.configured)
            p = mm.Project(n)
            print('Django configured: %s' % djsettings.configured)
            p.browser.settings.unset()
            print('Django configured: %s' % djsettings.configured)
            self.projects.extend([p])
        return

    def tearDown(self):
        for p in self.projects:
            shutil.rmtree(p.projectdir)
        return

    def test_multi_project(self):
        self.assertNotEqual(self.projects[0], self.projects[1])


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
