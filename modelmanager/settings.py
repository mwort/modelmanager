'''
The modelmanager settings module contains everything concerning the setup,
management and validation of the project settings defined in the settings
.mm/settings.json file.
'''

import json
import os.path as osp
from glob import glob
import inspect
import types
import traceback

from modelmanager import utils


class SettingsManager(object):
    '''
    Object to manage everything defined in the settings file.
    '''

    def __init__(self, project):
        self._project = project
        # attributes assigned through load
        self.module = None
        self.file = None
        self.variables = {}
        self.functions = {}
        self.classes = {}

        self.load()
        return

    def load(self):
        """
        Reads the settings from the settings file and attaches them to the
        project. Can be used to reload the settings.
        """
        # import module
        self.module = self._load_module()
        # filter settings that should be ignored
        settings = {n: self.module.__dict__[n]
                    for n in dir(self.module)
                    if not (inspect.ismodule(self.module.__dict__[n]) or
                            n.startswith('_'))}
        # assign them to project
        self(**settings)
        return

    def _load_module(self):
        from modelmanager.project import ProjectDoesNotExist

        # search settings file in any directory in this directory
        settings_dotglob = osp.join(self._project.projectdir, '.*',
                                    self._project.settings_file)
        settings_glob = osp.join(self._project.projectdir, '*',
                                 self._project.settings_file)

        sfp = glob(settings_glob) + glob(settings_dotglob)
        # warn if other than 1
        if len(sfp) == 0:
            errmsg = 'Cant find a modelmanager settings file under:\n'
            errmsg += settings_glob + '\n'
            errmsg += 'You can initialise a new project here using: \n'
            errmsg += 'modelmanager init \n'
            raise ProjectDoesNotExist(errmsg)
        elif len(sfp) > 1:
            msg = 'Found multiple modelmanager settings files (using *):\n'
            msg += '*'+'\n'.join(sfp)
            print(msg)
        self.file = osp.abspath(sfp[0])
        # save resourcedir to project
        self(resourcedir=osp.dirname(self.file))
        return utils.load_module_path('settings', self.file)

    def __call__(self, *objects, **settings):
        """
        Central settings assign method.

        Calling the SettingsManager with either objects or keyword arguments
        assigns the object or attribute to the project. Keyword arguments
        allow custom naming (i.e. best for variables), while positional
        arguments get assigned to the obj.__name__ in the project instance.
        """
        # sort out names of objects
        for obj in objects:
            errmsg = ("The object %s does not have a __name__ attribute.\n"
                      "You need to assign it with a keyword argument.")
            assert hasattr(obj, __name__), errmsg
            settings[obj.__name__] = obj
        # filter settings
        for name, obj in settings.items():
            if inspect.isfunction(obj):
                self.functions[name] = types.MethodType(obj, self._project)
            elif inspect.isclass(obj):
                # will be instatiated later when all variables and
                # functions are available
                self.classes[name] = obj
            else:
                self.variables[name] = obj
        # attach to project
        #  attributes
        for k, v in self.variables.items():
            setattr(self._project, k, v)
        #  functions (name is same as defined in settings)
        for k, f in self.functions.items():
            setattr(self._project, k, f)
        # classes
        self.plugins = {c.lower(): self._instatiate(self.classes[c])
                     for c in self.classes}
        for k, c in self.plugins.items():
            setattr(self._project, k, c)
        return

    def _instatiate(self, cla):
        """Savely instatiate a settings class."""
        try:
            obj = cla(self._project)
        except Exception:
            print("Failed to add %s to project." % cla.__name__)
            traceback.print_exc()
            obj = None
        return obj

    def __setitem__(self, key, value):
        """
        Settings assignment via:
        project.settings['name'] = value
        """
        self(**{key: value})
        return

    def __getitem__(self, key):
        """
        Make settings available through the project.settings['name'] interface.
        """
        return self._project.__dict__[key]

    def check_paths(self, dictionary=None, warn=True):
        '''Checks all settings for possible paths and return that are existing
        as a dictionary.'''
        dictionary = dictionary or self.variables
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

    def serialise(self):
        '''Default serialisation happens here via json.dumps'''
        return json.dumps(self.variables, indent=1, sort_keys=True)

    def __unicode__(self):
        return self.__str__()

    def __repr__(self):
        ppath = osp.abs(self.projectdir)
        rep = '<modelmanager.settings.SettingsManager for %s>' % ppath
        return rep
