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
    # create resource dir if it does not exist
    if osp.exists(settings.resourcedir):
        errmsg = 'There seems to be already a modelmanager project here:\n'
        errmsg += settings.resourcedir
        raise IOError(errmsg)
    else:
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


def execute_from_commandline(functions={'init': initialise}):
    """Comandline interface.

    Build an argsparse commandline interface by trying to load a project in
    the current directory and accessing the commandline_functions settings. If
    that fails, just show init command.
    """
    import argparse
    import inspect

    try:
        pro = Project()
        if hasattr(pro, 'commandline_functions'):
            for f in pro.commandline_functions:
                if hasattr(pro, f):
                    functions[f] = getattr(pro, f)
                else:
                    print('Function %s is listed in commandline_function ' +
                          'settings, but is not found in project.')
    except:
        pass

    cli_description = "The modelmanager command line interface."

    # create the top-level parser
    mainparser = argparse.ArgumentParser(description=cli_description)
    subparsers = mainparser.add_subparsers(help='function to call',
                                           dest='call')

    for l, f in functions.items():
        # get function arguments
        fspec = inspect.getargspec(f)
        # create the parser for the functions
        nargs = len(fspec.args)-len(fspec.defaults or [])
        defs = [None]*nargs + list(fspec.defaults or [])
        argsdef = zip(fspec.args, defs)
        callsig = ['%s=%r' % (a, d) if d is not None else a
                   for a, d in argsdef]
        helpstr = '(%s) ' % ', '.join(callsig) + (f.__doc__ or '')
        fparser = subparsers.add_parser(l, help=helpstr)
        # function arguments
        for a, d in argsdef:
            fparser.add_argument(a if d is None else '--'+a, default=d,
                                 help='(default={0!r})'.format(d)
                                      if d is not None else '')

    args = mainparser.parse_args()
    # send to function and return whatever is returned by the function
    # (pop removes call from dict)
    functions[args.__dict__.pop('call')](**args.__dict__)
    return
