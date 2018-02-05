"""Test module for the Browser plugin."""
import unittest
import os
import shutil
import cProfile, pstats

from django.conf import settings as djsettings
from django.apps import apps
import modelmanager as mm
from modelmanager.plugins import browser

import test_project

test_project.TEST_SETTINGS += """
from modelmanager.plugins.browser import Browser
"""

TEST_MODELS = """
from django.db import models

class TestModel(models.Model):
    type = models.FloatField('xyzmetric')
"""


class BrowserSetup(test_project.ProjectTestCase):

    def test_init(self):
        self.assertTrue(isinstance(self.project.browser, browser.Browser))

        with self.project.browser.settings:
            from modelmanager.plugins.browser.models import Run
            self.assertEqual(apps.get_model('modelmanager.run'), Run)

    def tearDown(self):
        shutil.rmtree(self.project.projectdir)
        self.project.browser.settings.unset()


class Tables(test_project.ProjectTestCase):
    def test_project_model(self):
        with file(self.project.browser.resourcedir+'/models.py', 'w') as f:
            f.write(TEST_MODELS)
        self.project.browser.update_db()
        from browser import models
        reload(models)
        self.assertEqual(apps.get_model('browser.testmodel'),
                         models.TestModel)

    def test_table_read_write(self):
        b = self.project.browser
        model = b.models['run']
        run = model(notes='testing notes')
        run.save()
        run_read = model.objects.filter(notes__contains='testing').last()
        self.assertEqual(run, run_read)
        # with internal functions
        run = b.insert('run', notes='tests notes')   # returns a run instance
        run_read = b.get_table('run', notes__contains='tests')  # list of dicts
        self.assertEqual(run.notes, run_read[0]['notes'])

    def tearDown(self):
        shutil.rmtree(self.project.projectdir)
        self.project.browser.settings.unset()


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
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(10)
