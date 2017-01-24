from settings import SettingsFile


class Project(object):

    def __init__(self, path='.', create=False, **parameters):

        # change into project dir

        # check resource dir exists
            # glob.glob(*/PARAMETERFILE)
            # if 0, none exists
            # if > 1, take first and warn
            # if 1, just load

        # load parameter file


def create_new_project(path, **parameters):
    # create .mm directory
    # make some defaults
    settings = SettingsFile()
    settings.save()

    # copy mmbrowser app
    # run migrate to create db and populate with some defaults
