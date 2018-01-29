"""Test module for the Browser plugin."""
import unittest
import cProfile, pstats

from django.apps import apps
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

    def test_project_model(self):
        with file(self.project.browser.resourcedir+'/models.py', 'w') as f:
            f.write(TEST_MODELS)
        self.project.browser.update_db()
        with self.project.browser.settings:
            from browser import models
            reload(models)
            self.assertEqual(apps.get_model('browser.testmodel'),
                             models.TestModel)


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(10)
