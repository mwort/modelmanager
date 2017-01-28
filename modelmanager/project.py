"""Core project components of a modelmanager project.

The Project class is the only exposed object of the modelmanager package. If
extending modelmanager for your model, you can inherit this class.

Project setup with the provided commandline script (calls 'initialise' below):
modelmanager --projectdir=.

"""

import os
from os import path as osp
from glob import glob
import shutil
import sys

import django

from settings import SettingsFile
import browser


class Project(object):

    def __init__(self, projectdir='.', **settings):

        # load parameter file
        self.settings = self._getSettingsFile(projectdir)

        # load environment (resourcedir and Django)
        self.env = ProjectEnv(self.settings.resourcedir)

        return

    def _getSettingsFile(self, projectdir):
        # search settings file in any directory in this directory
        settings_dotglob = osp.join(projectdir, '.*',
                                    SettingsFile.settings_file)  # w dotted dir
        settings_glob = osp.join(projectdir, '*', SettingsFile.settings_file)

        sfp = glob(settings_glob) + glob(settings_dotglob)
        # warn if other than 1
        if len(sfp) == 0:
            errmsg = 'Cant find a modulemanager settings file under:\n'
            errmsg += settings_glob + '\n'
            errmsg += 'You can initialise a new project here using: \n'
            errmsg += 'modelmanager init \n'
            raise IOError(errmsg)
        elif len(sfp) > 1:
            msg = 'Found multiple modulemanager settings files (using *):\n'
            msg += '*'+'\n'.join(sfp)
            print(msg)

        sf = SettingsFile(sfp[0])
        return sf


class ProjectEnv:
    '''Class to handle the environment variables needed for the project.'''
    def __init__(self, resourcedir):
        self.resourcedir = resourcedir
        # add resourcedir to python path
        sys.path = [self.resourcedir] + sys.path
        # django setup
        os.environ["DJANGO_SETTINGS_MODULE"] = "browser.settings"
        django.setup()
        return


def initialise(projectdir='.', **settingskwargs):
    """Initialise a default modelmanager project in the current directory."""
    from django.core.management import execute_from_command_line

    # use defaults for the settings file if not given in settings
    if 'settings_path' not in settingskwargs:
        sfpc = [settingskwargs.pop(s)
                if s in settingskwargs
                else SettingsFile.__dict__[s]
                for s in ['resourcedir', 'settings_file']]
        settingskwargs['settings_path'] = osp.join(projectdir, *sfpc)
    # load settings
    settings = SettingsFile(**settingskwargs)

    print('Initialising a new modelmanager project in: \n%s\n'
          % settings.projectdir +
          'with modelmanager files in:\n%s' % settings.resourcedir)
    # create projectdir if not existing
    if not osp.exists(projectdir):
        os.mkdir(settings.projectdir)
    # create resource dir if it does not exist, raise error otherwise
    ermg = 'There seems to be a modelmanager project here already:\n'
    assert not osp.exists(settings.resourcedir), ermg + settings.resourcedir
    os.mkdir(settings.resourcedir)

    # copy mmbrowser app
    settings.browser_path = osp.join(settings.resourcedir, 'browser')
    shutil.copytree(osp.join(browser.__path__[0], 'browser'),
                    settings.browser_path)

    # setup django
    env = ProjectEnv(settings.resourcedir)

    # run migrate to create db and populate with some defaults
    execute_from_command_line(['manage', 'migrate', '-v 0'])

    # save default settings
    settings.save()

    # load and return project
    return Project(settings.projectdir)
