

# default project parameters
DEFAULTS = {
,
}


class Project:

    PARAMETERFILE = 'mm.json'

    def __init__(self, path='.', create=False, **parameters):

        # change into project dir

        # check resource dir exists
            # glob.glob(*/PARAMETERFILE)
            # if 0, none exists
            # if > 1, take first and warn
            # if 1, just load

        # load parameter file


def create_new_project(path, **parameters):


class Parameters:

    def __init__(self, path):
        self.path = path

    def read(self):

    def write(self):
        
