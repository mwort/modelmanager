"""Test module for the Browser plugin."""
import unittest
import os
import shutil
import cProfile, pstats

from django.apps import apps
from django.test import Client as TestClient

from modelmanager.plugins import Browser

import test_project

test_project.TEST_SETTINGS += """
from modelmanager.plugins.browser import Browser
"""

TEST_MODELS = """
from django.db import models

class TestModel(models.Model):
    type = models.FloatField('xyzmetric')
"""


class BrowserProjectTestCase(test_project.ProjectTestCase):
    def tearDown(self):
        shutil.rmtree(self.project.projectdir)
        self.project.browser.settings.unset()


class BrowserSetup(BrowserProjectTestCase):

    def test_init(self):
        self.assertTrue(isinstance(self.project.browser, Browser))

        with self.project.browser.settings:
            from modelmanager.plugins.browser.models import Run
            self.assertEqual(apps.get_model('modelmanager.run'), Run)


class Tables(BrowserProjectTestCase):
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


class Admin(BrowserProjectTestCase):
    urls = ['/modelmanager/',
            '/modelmanager/run/',
            '/modelmanager/run/1/change/',
            '/modelmanager/parameter/',
            '/modelmanager/parameter/1/change/']

    def test_urls(self):
        run = self.project.browser.insert('run', tags='test t1')
        self.project.browser.insert('parameter', name='t1', value=2.1, run=run)
        client = TestClient()
        for u in self.urls:
            self.assertEqual(client.get(u).status_code, 200)


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
