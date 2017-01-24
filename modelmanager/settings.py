'''
The modelmanager settings module contains everything concerning the setup,
management and validation of the project settings defined in the settings
.mm/settings.json file.
'''

import json
import os.path as osp
import inspect


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
    resourcedir = '.mm'
    settings_file = 'settings.json'
    neversave = ['settings_file', 'resourcedir', 'settings_file']

    def __init__(self, **override):

        # make defaults instance variables
        self.__dict__.update(self._getDefaults())

        # define absolute path to file
        spath = [self.projectdir, self.resourcedir, self.settings_file]
        self.settings_path = osp.abspath(osp.join(*spath))

        # load settings from file
        try:
            self.load()
        except IOError:
            pass

        # override with instance initialised variables
        self.__dict__.update(override)

        return

    def _getDefaults(self):
        att = {k: v
               for k, v in inspect.getmembers(self.__class__)
               if not (k.startswith('_') or hasattr(v, '__call__'))}
        return att

    def _openFile(self, mode='r'):
        if mode == 'r' and not self._fileExists:
            raise(IOError, 'Settings file does not exist: %s')
        return file(self.settings_path, mode)

    @property
    def _fileExists(self):
        return osp.exists(self.settings_path)

    def relPath(self, path):
        '''Convert paths relative to projectdir'''
        return osp.relpath(path, self.projectdir)

    def absPath(self, path):
        '''Convert paths to absolute from project dir.'''
        return osp.abspath(osp.join(self.projectdir, path))

    def checkPaths(self, dictionary=None, warn=True):
        '''Checks all settings for possible paths and return that are existing
        as a dictionary.'''
        dictionary = dictionary or self.__dict__
        # needs to have a slash \ or /
        slashed = {k: v
                   for k, v in dictionary.items()
                   if osp.sep in v}
        existing = {k: v
                    for k, v in slashed.items()
                    if osp.exists(v)}
        notexisting = {k: v
                       for k, v in slashed.items()
                       if osp.exists(v)}

        if warn:
            print('These variables look like paths but doesnt exist:')
            for k, v in notexisting.items():
                print('%s: %s' % (k, v))
        return existing

    def save(self):
        json_str = self.serialise()
        with self._open_file('w') as f:
            f.write(json_str)
        return

    def load(self):
        with self._open_file() as f:
            sd = json.load(f)
        # make absolute
        paths = self.checkPaths()
        sd.update({k: self.absPath(v) for k, v in paths.items()})
        self.__dict__.update(sd)
        return

    def __str__(self):
        return self.serialise()

    def serialise(self):
        '''Default serialisation happens here via json.dumps'''
        var = self.__dict__.copy()
        # make paths relative
        paths = self.checkPaths()
        var.update({k: self.relPath(v) for k, v in paths.items()})
        # remove those that should never be saved
        for k in self.neversave:
            var.pop(k)
        return json.dumps(var, indent=1, sort_keys=True)

    def __unicode__(self):
        return self.__str__()

    def __repr__(self):
        ppath = osp.abs(self.projectdir)
        rep = '<modelmanager.settings.SettingsFile for %s' % ppath
        return rep
