'''
The modelmanager settings module contains everything concerning the setup,
management and validation of the project settings defined in the settings
.mm/settings.json file.
'''

import json
from os import path as ospath


class SettingsFile(object):
    '''
    The settings file representation. All class variables are default values
    which will be overridden in the following order:
    - by values define in file
    - by values define when creating this class

    The only variable not saved to the file is the file path itself
    (settings_path) to avoid reloading issues.
    '''
    # define defaults here
    store_input_functions = []
    projectdir = '.'

    def __init__(self, path='.mm/settings.json', **override):

        # define absolute to file
        self.settings_path = ospath.abspath(ospath.join(self.projectdir, path))

        # load settings from file
        try:
            self.load()
        except IOError:
            pass

        # override with instance initialised variables
        self.__dict__.update(override)

        return

    def _open_file(self, mode='r'):
        if mode == 'r' and not self.exists:
            raise(IOError, 'Settings file does not exist: %s')
        return file(self.settings_path, mode)

    @property
    def exists(self):
        return ospath.exists(self.settings_path)

    def save(self):
        json_str = str(self)
        with self._open_file('w') as f:
            f.write(json_str)
        return

    def load(self):
        with self._open_file() as f:
            sd = json.load(f)
        self.__dict__.update(sd)
        return

    def __str__(self):
        '''Default serialisation happens here via json.dumps'''
        dump = self.__dict__.copy()
        dump.pop('settings_path')
        return json.dumps(dump, indent=1, sort_keys=True)

    def __unicode__(self):
        return self.__str__()

    def __repr__(self):
        rep = 'Settings:\n'
        order = sorted(self.__dict__.keys())
        rep += '\n'.join(['%s: %s' % (k, self.__dict__[k]) for k in order])
        return rep
