"""
This is a modelmanager plugin for a django server app that gives you a
browser interface and a database backend for your model.

The plugin is made up of two custom Django apps, one residing in the
modelmanager package and one in the project/resourcedir/browser directory.
While the first is fully importable (i.e. is on your PYTHONPATH), the latter
is not and should thus only be accessed through the browser object.
"""

import os.path as osp
import sys
import shutil

try:
    import django
except ImportError:
    raise ImportError("Please install Django: pip install django")

from django.apps import AppConfig


class BrowserConfig(AppConfig):
    """
    This is the app configuration of the modelmanager.plugins.browser app.
    """
    name = 'modelmanager.plugins.browser'
    verbose_name = 'Modelmanager'
    label = 'modelmanager'


class Browser:

    def __init__(self, project):
        self.project = project
        self.resourcedir = osp.join(project.resourcedir, 'browser')
        self.settings = BrowserSettings(self)

        if not osp.exists(self.resourcedir):
            self._install()
        return

    def _install(self):
        """
        Install the browser resources in project.resourcedir.
        """
        try:
            shutil.copytree(osp.join(osp.dirname(__file__), 'resources'),
                            self.resourcedir)
        except OSError:
            em = ('Cant install the browser resources. Do they already '
                  'exist in %s?' % self.resourcedir)
            raise OSError(em)
        # install database
        self.update_db()
        return

    def update_db(self, verbosity=0):
        self.manage('makemigrations', 'browser', '-v %1i' % verbosity)
        self.manage('migrate', '-v %1i' % verbosity)
        return

    def manage(self, *args):
        """Convenience function for django manage.py commands.
        Dango needs to be setup for this to work.
        """
        from django.core.management import execute_from_command_line
        with self.settings:
            execute_from_command_line(['manage'] + list(args))
        return


class BrowserSettings:
    def __init__(self, browser):
        self.project = browser.project
        self.browser = browser
        self.resourcedir = self.project.resourcedir
        self.dbpath = osp.join(self.browser.resourcedir, 'db.sqlite3')

        # Project-specific Django settings
        self.django_settings = {
            "BASE_DIR": self.project.resourcedir,
            "PROJECT": self.project,
            "DATABASES": {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': self.dbpath}}}
        # override them from settings file
        if hasattr(self.project, 'django_settings'):
            self.django_settings.update(self.project.django_settings)

        return

    def __enter__(self):
        """
        Setup django settings.
        """
        from modelmanager.plugins.browser import defaultsettings

        # make sure the resourcedir is on sys.path
        if self.project.resourcedir not in sys.path:
            sys.path = [self.project.resourcedir] + sys.path
        # import settings
        try:
            django.conf.settings.configure(defaultsettings,
                                           **self.django_settings)
            django.setup()
        except Exception:
            raise #Exception('Failed to activate Django :(')
        return

    def __exit__(self, exc_type, exc_value, traceback):
        django.conf.settings._wrapped = django.conf.empty
        if self.resourcedir in sys.path:
            sys.path = list(filter(lambda a: a != self.resourcedir, sys.path))
        return


def startbrowser(project):
    """
    Start the Django browser app. Navigate to localhost:8000/admin in your
    browser. To quit the browser server, do control-c on the console.
    """
    project.browser.manage('runserver')
    return


def manage(project, csvcommands):
    project.browser.manage(*csvcommands.split(','))
