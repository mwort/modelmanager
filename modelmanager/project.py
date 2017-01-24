"""Core project components of a modelmanager project.

The Project class is the only exposed object of the modelmanager package. If
extending modelmanager for your model, you can inherit this class.

Project setup with the provided commandline script (calls 'initialise' below):
modelmanager --projectdir=.

"""

from settings import SettingsFile
import os
from os import path as osp


class Project(object):

    def __init__(self, path='.', **settings):

        # change into project dir

        # check resource dir exists
            # glob.glob(*/PARAMETERFILE)
            # if 0, none exists
            # if > 1, take first and warn
            # if 1, just load

        # load parameter file
        return


def initialise(**settings):

    # get defaults
    settings = SettingsFile(**settings)

    # create resource dir if it does not exist
    if osp.exists(settings.resourcedir):
        errmsg = 'There seems to be already a modelmanager project here:\n'
        errmsg += settings.resourcedir
        raise IOError(errmsg)
    else:
        os.mkdir(settings.resourcedir)

    # save default settings
    settings.save()

    # copy mmbrowser app
    # run migrate to create db and populate with some defaults

    return


def execute_from_command():
    import argparse

    parser = argparse.ArgumentParser(description='A helpful tool for modellers.')
    parser.add_argument('--projectdir', type=str, default='.',
                        help='Model root directory.')

    args = parser.parse_args()
    initialise(**vars(args))
