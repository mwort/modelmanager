"""Core project components of a modelmanager project.

The Project class is the only exposed object of the modelmanager package. If
extending modelmanager for your model, you can inherit this class.

Project setup with the provided commandline script (calls 'initialise' below):
modelmanager --projectdir=.

"""

import os
from os import path as osp
import shutil
import sys

from modelmanager.settings import SettingsManager, SettingsUndefinedError


class Project(object):
    """The central project object.

    All variables and fuctions are available to operate on the current model
    state.
    """

    def __init__(self, projectdir='.', **settings):
        self.projectdir = osp.abspath(projectdir)
        # initalise settings
        self.settings = SettingsManager(self)
        # load settings with overridden settings
        self.settings.load(**settings)
        return

    def __repr__(self):
        rpd = osp.relpath(self.projectdir, os.getcwd())
        r = ('<%s instance in: %s >' % (self.__class__.__name__, rpd))
        return r

    def __getattr__(self, attr):
        """
        Fall-back if requested setting isnt defined.
        """
        # make sure AttributeErrors from properties are not misinterpreted
        if attr in self.__class__.__dict__:
            try:
                # acess property without getattr
                self.__class__.__dict__[attr].fget(self)
            except AttributeError:
                import traceback
                ex_type, ex, tb = sys.exc_info()
                raise AttributeError('While accessing the setting %s,' % attr +
                                     ' the below error occurred:\n\n' +
                                     ''.join(traceback.format_tb(tb)) +
                                     'AttributeError: '+str(ex))
        else:
            raise SettingsUndefinedError(attr)


def setup(projectdir='.', resourcedir='mm'):
    """Initialise a default modelmanager project in the current directory."""

    resourcedir = osp.join(projectdir, resourcedir)
    settings_path = osp.join(resourcedir, SettingsManager.settings_file_name)
    print('Initialising a new modelmanager project in: %s\n' % projectdir +
          'with settings file in: %s' % settings_path)
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
    pro = Project(projectdir)

    return pro


class ProjectDoesNotExist(Exception):
    pass
