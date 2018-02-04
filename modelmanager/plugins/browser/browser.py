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

from django.apps import apps as djapps


class BrowserConfig(django.apps.AppConfig):
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
        # permanently setup django (will cause error with multiple prjects)
        self.settings.setup()
        self.update_db()
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
        return

    def update_db(self, verbosity=0):
        self.manage('makemigrations', 'browser', '-v %1i' % verbosity)
        self.manage('migrate', '-v %1i' % verbosity)
        return

    def manage(self, *args):
        """
        Convenience function for django manage.py commands.
        Dango needs to be setup for this to work.
        """
        from django.core.management import execute_from_command_line
        with self.settings:
            execute_from_command_line(['manage'] + list(args))
        return

    def start(self):
        """
        Start the Django browser app. Navigate to localhost:8000/admin in your
        browser. To quit the browser server, do control-c on the console.
        """
        self.manage('runserver')
        return

    @property
    def tables(self):
        """
        Get all available tables from the plugin and the project.
        """
        with self.settings:
            models = list(djapps.get_app_config('modelmanager').get_models())
            models += list(djapps.get_app_config('browser').get_models())
        models = {m.__name__.lower(): m for m in models}
        return models

    def get_table(self, tablename, **filters):
        """
        Get all rows from table or subset if filters are given.
        """
        model = self.tables[tablename]
        with self.settings:
            # return lists to actually read the QuerySet from the DB
            if len(filters) > 0:
                rows = list(model.objects.filter(**filters))
            else:
                rows = list(model.objects.all())
        return rows

    def insert(self, tablename, **modelfields):
        Model = self.tables[tablename]
        instance = Model(**modelfields)
        with self.settings:
            instance.save()
        return instance


class BrowserSettings:
    # switch to track django setup for with block
    setup_on_with = False

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

    def setup(self):
        """
        Setup django settings.
        """
        from modelmanager.plugins.browser import defaultsettings
        # check if already configured
        if django.conf.settings.configured:
            conf_project = django.conf.settings.PROJECT
            # check if same project is configured without comparing instances
            if conf_project.resourcedir != self.project.resourcedir:
                raise django.core.exceptions.ImproperlyConfigured(
                      "Browser is already setup for project: %s\n" %
                      conf_project.projectdir + "You need to unset it first.")
                # conf_project.browser.settings.unset()
            else:
                return False
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
        return True

    def unset(self):
        django.conf.settings._wrapped = django.conf.empty
        if self.resourcedir in sys.path:
            sys.path = list(filter(lambda a: a != self.resourcedir, sys.path))
        return

    def __enter__(self):
        if self.setup():
            self.setup_on_with = True

    def __exit__(self, exc_type, exc_value, traceback):
        if self.setup_on_with:
            self.unset()

    def __del__(self):
        self.unset()
