"""
This is a modelmanager plugin for a django server app that gives you a
browser interface and a database backend for your model.
"""

import os.path as osp
import types

from modelmanager import utils

try:
    import django
except ImportError:
    raise ImportError("Please install Django: pip install django")


class Browser:
    def __init__(self, project):
        self._project = project

    # old project function
    def _confBrowser(self):
        self.setup_django(self._loadResource('browser.settings'))
        return

    def _migrateBrowser(self, verbosity=0):
        self._confBrowser()
#        utils.manage_django('makemigrations', 'browser', '-v %1i' % verbosity)
        self.manage_django('migrate', '-v %1i' % verbosity)
        return

    def start(self):
        """Start the model browser."""
        self._confBrowser()
        self.manage_django('runserver')
        return

    def update(self):
        self._migrateBrowser()
        return

    def setup_django(self, pathormodule):
        """
        Setup django settings w either path to settings or a loaded module.
        """
        if type(pathormodule) == str and osp.exists(pathormodule):
            set_mod = utils.load_module_path('settings', pathormodule)
        elif isinstance(pathormodule, types.ModuleType):
            set_mod = pathormodule
        else:
            raise IOError('%s must be a valid path or a module instance.'
                          % pathormodule)

        # project specific django modules can not be found unless the path is added
        # to sys.path
    #    djdir = osp.dirname(osp.dirname(set_mod.__file__))
    #    if djdir in sys.path:
    #        sys.path.remove(djdir)
    #    sys.path = [djdir] + sys.path
        django.conf.settings._wrapped = django.conf.empty
        django.conf.settings.configure(set_mod)
        django.setup()
        return

    def manage_django(self, *args):
        """Convenience function for django manage.py commands.
        Dango needs to be setup for this to work.
        """
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage'] + list(args))
        return


def startbrowser(self):
    """
    Start the Django browser app. Navigate to localhost:8000/admin in your
    browser. To quit the browser server, do control-c on the console.
    """
    self.project.browser.start()
    return
