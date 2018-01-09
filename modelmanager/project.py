"""Core project components of a modelmanager project.

The Project class is the only exposed object of the modelmanager package. If
extending modelmanager for your model, you can inherit this class.

Project setup with the provided commandline script (calls 'initialise' below):
modelmanager --projectdir=.

"""

import os
from os import path as osp
import shutil

from modelmanager.settings import SettingsManager


class Project(object):
    """The central project object.

    All variables and fuctions are available to operate on the current model
    state.
    """
    # defaults
    projectdir = '.'
    resourcedir = 'mm'
    settings_file = 'settings.py'

    def __init__(self, projectdir='.', **settings):
        self.projectdir = projectdir
        # initalise settings
        self.settings = SettingsManager(self)
        # override settings if any are parsed
        self.settings(**settings)
        return


def setup(projectdir='.', **settings):
    """Initialise a default modelmanager project in the current directory."""

    # use defaults if not given in settings
    for s in ['resourcedir', 'settings_file']:
        if s not in settings:
            settings[s] = Project.__dict__[s]
    resourcedir = osp.join(projectdir, settings['resourcedir'])
    settings_path = osp.join(resourcedir, settings['settings_file'])
    print('Initialising a new modelmanager project in: \n%s\n' % projectdir +
          'with modelmanager files in:\n%s' % settings_path)
    # create projectdir if not existing
    if not osp.exists(projectdir):
        os.mkdir(projectdir)
    # create resource dir if it does not exist, raise error otherwise
    ermg = ('The modelmanager resource directory seems to exist already:\n' +
            resourcedir)
    assert not osp.exists(resourcedir), ermg

    default_resources = osp.join(osp.dirname(__file__), 'resources')
    shutil.copytree(default_resources, resourcedir)

    # load project and update/create database
    pro = Project(projectdir, **settings)

    return pro


class ProjectDoesNotExist(Exception):
    pass
