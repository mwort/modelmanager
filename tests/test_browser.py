"""Test module for the Browser plugin."""
import unittest
import os
import shutil
import cProfile, pstats

from django.apps import apps
from django.test import Client as TestClient

from modelmanager.plugins import Browser

from test_project import create_project

TEST_SETTINGS = """
from modelmanager.plugins.browser import Browser
"""

TEST_MODELS = """
from django.db import models

class TestModel(models.Model):
    type = models.CharField(max_length=32)
"""


class BrowserProjectTestCase(unittest.TestCase):

    projectdir = 'browsertestproject'

    def setUp(self):
        self.project = create_project(self.projectdir, TEST_SETTINGS)
        self.browser = self.project.browser
        self.models = self.browser.models
        # write custom model.py
        with file(self.browser.resourcedir+'/models.py', 'w') as f:
            f.write(TEST_MODELS)
        # populate standard models/tables
        run = self.models['run'](notes='testing notes')
        run.save()
        param = self.models['parameter'](name='xyz', value=1.33, run=run)
        param.save()
        result = self.models['resultindicator'](name='x', value=0.8, run=run)
        result.save()

    def tearDown(self):
        shutil.rmtree(self.project.projectdir)
        self.browser.settings.unset()


class BrowserSetup(BrowserProjectTestCase):

    def test_init(self):
        self.assertTrue(isinstance(self.project.browser, Browser))

        with self.project.browser.settings:
            from modelmanager.plugins.browser.models import Run
            self.assertEqual(apps.get_model('modelmanager.run'), Run)


class Tables(BrowserProjectTestCase):
    def test_project_model(self):
        from browser import models
        reload(models)
        self.browser.update_db()
        self.assertEqual(apps.get_model('browser.testmodel'),
                         models.TestModel)
        # write/read something to custom table
        v = self.browser.insert('testmodel', type="testing")
        self.assertEqual(v, self.browser.models['testmodel'].objects.first())
        vdict = self.browser.get_table('testmodel')[0]
        self.assertEqual(vdict['type'], 'testing')

    def test_table_read_write(self):
        # with django
        run_read = self.models['run'].objects.filter(notes__contains='testing')
        self.assertEqual(run_read.last().notes, "testing notes")
        # with internal functions
        run = self.browser.insert('run', notes='tests notes')   # run instance
        run_read = self.browser.get_table('run', notes__contains='tests')  # d
        self.assertEqual(run.notes, run_read[0]['notes'])


class Admin(BrowserProjectTestCase):
    urls = ['/modelmanager/',
            '/modelmanager/run/',
            '/modelmanager/run/1/change/',
            '/modelmanager/parameter/',
            '/modelmanager/parameter/1/change/']

    def test_urls(self):
        client = TestClient()
        for u in self.urls:
            self.assertEqual(client.get(u).status_code, 200)


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
