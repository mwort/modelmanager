"""
This is a modelmanager plugin for a django server app that gives you a
browser interface and a database backend for your model.

The plugin is made up of two custom Django apps, one residing in the
modelmanager package and one in the project/resourcedir/browser directory.
While the first is fully importable (i.e. is on your PYTHONPATH), the latter
is not and should thus only be accessed through the browser object.
"""
import os
import os.path as osp
import sys
import shutil

try:
    import django
except ImportError:
    raise ImportError("Please install Django: pip install django")

from django.apps import apps as djapps

from modelmanager import utils


class browser(object):

    def __init__(self, project):
        self.project = project
        self.resourcedir = osp.join(project.resourcedir, 'browser')
        # always ensure all resources are installed (not overwritten)
        self._install()
        # permanently setup django (will cause error with multiple prjects)
        self.settings = BrowserSettings(self)
        self.settings.setup()
        # only update the database if it doesnt exist yet
        if not osp.exists(self.settings.dbpath):
            self.update_db()
        for n, m in self.models.items():
            setattr(self, n+'s', m.objects)
        return

    def _install(self):
        """
        Install the browser resources in project.resourcedir.
        """
        try:
            utils.copy_resources(osp.join(osp.dirname(__file__), 'resources'),
                                 self.resourcedir)
        except OSError as e:
            print(e)
            em = ('Cant install the browser resources. Do they already '
                  'exist in %s?' % self.resourcedir)
            raise OSError(em)
        return

    def update_db(self, verbosity=0):
        self.manage('makemigrations', 'browser',  verbosity=verbosity)
        self.manage('migrate',  verbosity=verbosity)
        return

    def manage(self, *args, **kwargs):
        """
        Convenience function for django manage.py commands.
        Dango needs to be setup for this to work.
        """
        from django.core import management
        with self.settings:
            management.call_command(*args, **kwargs)
        return

    def start(self):
        """
        Start the Django browser app. Navigate to localhost:8000/admin in your
        browser. To quit the browser server, do control-c on the console.
        """
        self.manage('runserver')
        return

    @property
    def models(self):
        """
        Get all available Django models from the plugin and the project.
        """
        with self.settings:
            models = list(djapps.get_app_config('browser').get_models())
        models = {m.__name__.lower(): m for m in models}
        return models

    def get(self, tablename, **filters):
        """
        Get all rows from a browser table or a subset if filters are given.
        """
        model = self.models[tablename]
        with self.settings:
            # return lists to actually read the QuerySet from the DB
            if len(filters) > 0:
                rows = model.objects.filter(**filters)
            else:
                rows = model.objects.all()
        return list(rows)

    def insert(self, tablename, **modelfields):
        """
        Insert entries into the table including related fields.

        **modelfields : Keyword arguments of table fields with appropriate
            values. Related table field values must be dicts or list of dicts.
        """
        Model = self.models[tablename]
        # filter realted fields
        related = [(f, modelfields.pop(f.name))
                   for f in Model._meta.get_fields()
                   if any([f.one_to_many, f.one_to_one, f.many_to_many])
                   and f.name in modelfields]
        # deal with main model
        instance = Model(**modelfields)
        with self.settings:
            instance.save()
        # insert related values
        for field, value in related:
            em = 'Value of %s must be a dict or a list of dicts.' % field.name
            assert type(value) in [list, dict], em
            value = value if type(value) is list else [value]
            relm = field.related_model._meta.model_name
            for rd in value:
                assert type(rd) is dict, em
                rd[field.remote_field.name] = instance
                self.insert(relm, **rd)
        return instance


class BrowserSettings(object):
    # switch to track django setup for with block
    setup_on_with = False
    dbname = 'db.sqlite3'
    filesdirname = 'files/'
    tmpfilesdirname = 'tmp/'

    def __init__(self, browser):
        self.project = browser.project
        self.browser = browser
        self.resourcedir = self.project.resourcedir
        self.dbpath = osp.join(self.browser.resourcedir, self.dbname)
        self.filesdir = osp.join(self.browser.resourcedir, self.filesdirname)
        self.tmpfilesdir = osp.join(self.filesdir, self.tmpfilesdirname)
        if not osp.exists(self.tmpfilesdir):
            os.makedirs(self.tmpfilesdir)
        # Project-specific Django settings
        self.django_settings = {
            "BASE_DIR": self.project.resourcedir,
            "PROJECT": self.project,
            "DATABASES": {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': self.dbpath,
                    'OPTIONS': {'timeout': 60},
                    }
                },
            "MEDIA_ROOT": self.filesdir,
            "MEDIA_URL": self.filesdir}
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
            same_resources = (osp.realpath(conf_project.resourcedir) !=
                              osp.realpath(self.project.resourcedir))
            if same_resources:
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
        except Exception as e:
            print(e)
            raise Exception('Failed to activate Django :(')
        # reset database path for multiple projects (connections is
        # instantiated when django is loaded and is therfore not changed when
        # the settings are changed)
        django.db.connections.databases['default']['NAME'] = self.dbpath
        return True

    def unset(self):
        # close database so that on setup a new connection is opened
        django.db.connections['default'].close()
        # overwrite settings with empty
        django.conf.settings._wrapped = django.conf.empty

        if self.resourcedir in sys.path:
            sys.path = [a for a in sys.path if a != self.resourcedir]

        self.clear_tmp_files()
        return

    def clear_tmp_files(self):
        """Recursively remove everything *inside* the tmpfilesdir."""
        # clear files tmpdir
        if osp.exists(self.tmpfilesdir):
            for i in os.listdir(self.tmpfilesdir):
                p = osp.join(self.tmpfilesdir, i)
                # thread-safe removing
                try:
                    shutil.rmtree(p) if osp.isdir(p) else os.remove(p)
                except OSError:
                    pass
        return

    def __enter__(self):
        if self.setup():
            self.setup_on_with = True

    def __exit__(self, exc_type, exc_value, traceback):
        if self.setup_on_with:
            self.unset()
            self.setup_on_with = False
