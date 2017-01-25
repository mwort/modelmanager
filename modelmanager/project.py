"""Core project components of a modelmanager project.

The Project class is the only exposed object of the modelmanager package. If
extending modelmanager for your model, you can inherit this class.

Project setup with the provided commandline script (calls 'initialise' below):
modelmanager --projectdir=.

"""

from settings import SettingsFile
import os
from os import path as osp
from glob import glob


class Project(object):

    def __init__(self, projectdir='.', **settings):

        # load parameter file
        self.settings = self._getSettingsFile(projectdir)

        return

    def _getSettingsFile(self, projectdir):
        # check resource dir exists
            # glob.glob(*/PARAMETERFILE)
        settings_glob = osp.join(projectdir, '*', SettingsFile.settings_file)
        sfp = glob(settings_glob)
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

        return sfp[0]

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
