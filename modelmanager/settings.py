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
    neversave = ['settings_path', 'resourcedir', 'settings_file']
    commandline_functions = {'browser': 'start_browser', 'update': 'update'}

    # these settings will be overwritten by the __init__ function from the
    # settings_path (required arguement) and are just defined here as defaults
    projectdir = '.'
    resourcedir = 'mm'
    # settings_file is a module constant, ie. can not be changed for a project
    settings_file = 'settings.json'

    def __init__(self, settings_path, **override):

        # make defaults instance variables
        self.__dict__.update(self._getDefaults())

        # save settings paths and reassign settings variables
        self.settings_path = osp.abspath(settings_path)
        resdir, setfile = osp.split(self.settings_path)
        varoverr = {'projectdir': osp.dirname(resdir),
                    'resourcedir': resdir,
                    'settings_file': setfile}
        for l, p in varoverr.items():
            if l in override:
                # remove from override to prevent it from being set later
                prem = override.pop(l)
                print('%s (%s) will be overridden by settings_path %s'
                      % (l, prem, settings_path))
            self.__dict__[l] = p

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
                       if not osp.exists(v)}

        if warn and len(notexisting) > 1:
            print('These variables look like paths but dont exist:')
            for k, v in notexisting.items():
                print('%s: %s' % (k, v))
        return existing

    def save(self):
        json_str = self.serialise()
        with self._openFile('w') as f:
            f.write(json_str)
        return

    def load(self):
        with self._openFile() as f:
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
