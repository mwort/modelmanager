"""Test module for the Browser plugin."""
import unittest
import os
import shutil
import cProfile, pstats

from django.apps import apps
from django.test import Client as TestClient

from modelmanager.plugins.browser import browser

from test_project import create_project
import imp

TEST_SETTINGS = """
from modelmanager.plugins.browser import browser
from modelmanager import utils

def test_function(project, s='hello', **kwargs):
    return ','.join(kwargs.values()) if len(kwargs)>0 else s

@utils.propertyplugin
class result:
    plugin_functions = ['plot_test']

    def __init__(self, project):
        pass
    def plot_test(self):
        return 0
"""

TEST_MODELS = """
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
        modelpath = os.path.join(self.browser.resourcedir, 'models.py')
        with open(modelpath, 'a') as f:
            f.write(TEST_MODELS)
        # populate standard models/tables
        run = self.models['run'](notes='testing notes')
        run.save()
        self.test_run = run
        param = self.models['parameter'](name='xyz', value=1.33, run=run)
        param.save()
        result = self.models['indicator'](name='x', value=0.8, run=run)
        result.save()
        # test browser interaction
        self.client = TestClient()

    def tearDown(self):
        self.browser.settings.unset()
        shutil.rmtree(self.project.projectdir)


class BrowserSetup(BrowserProjectTestCase):

    def test_init(self):
        self.assertTrue(isinstance(self.browser, browser))
        self.assertTrue(os.path.exists(self.browser.settings.tmpfilesdir))
        with self.project.browser.settings:
            from browser.models import Run
            self.assertEqual(apps.get_model('browser.run'), Run)


class Tables(BrowserProjectTestCase):
    def test_project_models(self):
        from browser import models
        imp.reload(models)
        self.browser.update_db()
        self.assertEqual(apps.get_model('browser.testmodel'), models.TestModel)
        # write/read something to custom table
        v = self.browser.insert('testmodel', type="testing")
        self.assertEqual(v, self.browser.models['testmodel'].objects.first())
        vdict = self.browser.get('testmodel')[0]
        self.assertEqual(vdict.type, 'testing')

    def test_table_read_write(self):
        # with django
        run_read = self.browser.runs.filter(notes__contains='testing')
        self.assertEqual(run_read.last().notes, "testing notes")
        # with internal functions
        run = self.browser.insert('run', notes='tests notes')   # run instance
        run_read = self.browser.get('run', notes__contains='tests')  # list
        self.assertEqual(run.notes, run_read[0].notes)
        # with related fields
        run = self.browser.insert('run', notes='has related', tags='crazy',
                                  parameters=dict(name='px', value=0.77),
                                  indicators=[dict(name='x', value=1.6),
                                              dict(name='n', value=0.1)])
        # read again
        run_read = self.browser.runs.filter(tags='crazy').last()
        for related in ['parameters', 'indicators', 'files']:
            self.assertTrue(hasattr(run, related))
            self.assertTrue(hasattr(run_read, related))
        # related field values are managers
        self.assertEqual(len(run_read.indicators.all()), 2)
        indicator = self.browser.models['indicator']
        self.assertIs(type(run_read.indicators.first()), indicator)


class DatabaseAdmin(BrowserProjectTestCase):
    urls = ['/browser/',
            '/browser/run/',
            '/browser/run/1/change/',
            '/browser/parameter/',
            '/browser/parameter/1/change/']

    def test_urls(self):
        for u in self.urls:
            self.assertEqual(self.client.get(u).status_code, 200)

    def test_file_upload(self):
        with open(__file__) as f:
            data = {'run': 1, 'name': "something", 'file': f}
            response = self.client.post('/browser/file/add/', data)
        self.assertEqual(response.status_code, 302)  # redirected on success
        resfile = self.browser.models['file'].objects.last()
        with open(__file__, 'rb') as selfile:
            with resfile.file as rf:
                resfilecontents = rf.read()
            self.assertEqual(resfilecontents, selfile.read())


class ApiAdmin(BrowserProjectTestCase):
    urls = ['/api/',
            '/api/function/',
            '/api/setting/',
            '/api/function/test_function/change/',
            '/browser/run/1/function/test_function/call/']  # returns errmsg

    def check_url(self, url):
        print('Checking %s' % url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response

    def test_urls(self):
        for u in self.urls:
            self.check_url(u)

    def test_call(self):
        from modelmanager.plugins.browser.api import models
        callurl = '/api/function/%s/call/'
        # make sure function table is populated
        self.check_url('/api/function/')
        fobj = models.Function.objects.get(name='test_function')
        response = self.check_url(callurl % fobj.pk)
        self.assertEqual(response.content, b'hello')
        models.Argument(name='world', value='"hello"', function=fobj).save()
        response = self.check_url(callurl % fobj.pk)
        self.assertEqual(response.content, b'hello')
        models.Argument(name='world', value='project.resourcedir',
                        function=fobj).save()
        response = self.check_url(callurl % fobj.pk)
        self.assertEqual(response.content.decode(), self.project.resourcedir)


class Files(BrowserProjectTestCase):

    def test_file_save_types(self):
        from django.core.files import File as DjFile
        for f in [DjFile(open(__file__)), open(__file__), __file__]:
            resfile = self.browser.insert('file',
                                          file=f, run=self.test_run)
            newpath = resfile.file.path
            self.assertTrue(os.path.exists(newpath))
            fdir = os.path.join(self.project.browser.settings.filesdir, 'runs')
            self.assertTrue(newpath.startswith(fdir))
            resfile = self.browser.models['file'].objects.first()
            self.assertEqual(newpath, resfile.file.path)
            resfile.delete()
            self.assertFalse(os.path.exists(newpath))

        with self.assertRaises(IOError):
            resfile = self.browser.insert('file',
                                          file=123, run=self.test_run)

        return


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
