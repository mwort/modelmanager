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

    settings_file_name = 'settings.py'

    def __init__(self, project):
        self._project = project
        # attributes assigned through load
        self.module = None
        self.file = None
        self.variables = {}
        self.functions = {}
        self.properties = {}
        self.classes = {}
        self.plugins = {}
        return

    def load(self, **override_settings):
        """
        (Re)load and override project settings.

        Reads the settings from the settings file and attaches them to the
        project. Can be used to reload the settings and override settings that
        are used when initialising plugins.
        """
        # import module
        self.module = self._load_module()
        # filter settings that should be ignored
        settings = {n: self.module.__dict__[n]
                    for n in dir(self.module)
                    if not (inspect.ismodule(self.module.__dict__[n]) or
                            n.startswith('_'))}
        # override
        settings.update(override_settings)
        # assign them to project
        self(**settings)
        return

    def _load_module(self):
        from modelmanager.project import ProjectDoesNotExist

        # search settings file in any directory in this directory
        settings_dotglob = osp.join(self._project.projectdir, '.*',
                                    self.settings_file_name)
        settings_glob = osp.join(self._project.projectdir, '*',
                                 self.settings_file_name)

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
        return utils.load_module_path(self.file)

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
            elif isinstance(obj, property):
                self.properties[name] = obj
            else:
                # variable, append projectdir
                self.variables[name] = self._filter_abs_path(obj)
        # attach to project
        #  attributes
        for k, v in self.variables.items():
            setattr(self._project, k, v)
        #  functions (name is same as defined in settings)
        for k, f in self.functions.items():
            setattr(self._project, k, f)
            # store as Function
            self.functions[k] = Function(f)
        # properties
        for k, p in self.properties.items():
            setattr(self._project.__class__, k, p)
            # deal with propertyplugins
            if getattr(p.fget, 'isplugin', False):
                plnf = getattr(p.fget, 'plugin_functions', {})
                plnf = {n: Function(v) for n, v in plnf.items()}
                self.plugins[k] = (v, plnf)

        # classes to plugins
        for k, c in self.classes.items():
            instance = self._instatiate(c)
            name = k.lower()
            methods = inspect.getmembers(instance, predicate=inspect.ismethod)
            methods = {n: Function(m) for (n, m) in methods
                       if not n.startswith('_')}
            setattr(self._project, name, instance)
            self.plugins[name] = (instance, methods)
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

    def _filter_abs_path(self, variable):
        """
        Check if variable is a string and an existing path relative path from
        the projectdir. If so, make it absolute.
        """
        if type(variable) == str:
            path = osp.join(self._project.projectdir, variable)
            if osp.exists(path):
                variable = path
        return variable

    def __setitem__(self, key, value):
        """
        Settings assignment via:
        project.settings['name'] = value
        """
        self(**{key: value})
        return

    def __getitem__(self, key):
        """
        Get project method and attributes by string or dotted path for plugins.

        key: attribute/method string or dotted path.
        Returns: attribute/method.
        """
        mod = self._project
        for comp in key.split('.'):
            if not hasattr(mod, comp):
                raise KeyError('Project does not have attribute %s' % key)
            mod = getattr(mod, comp)
        return mod

    def is_valid(self, key):
        """
        Check if key is a valid setting incl. dotted path to plugin attributes.
        """
        mod = self._project
        components = key.split('.')
        for i, comp in enumerate(components):
            if not hasattr(mod, comp):
                return False
            if i < len(components)-1:
                mod = getattr(mod, comp)
        return True

    def serialise(self):
        '''Default serialisation happens here via json.dumps'''
        return json.dumps(self.variables, indent=1, sort_keys=True)

    def __unicode__(self):
        return unicode(self.__str__())

    def __repr__(self):
        rep = '<SettingsManager for %s>' % self._project
        return rep


class Function(object):
    """
    Representation of a project function.
    """
    def __init__(self, function):
        if isinstance(function, Function):
            function = function.function
        # get function arguments
        fspec = inspect.getargspec(function)
        # create the parser for the functions
        self.defaults = list(fspec.defaults or [])
        nposargs = len(fspec.args) - len(self.defaults)
        self.positional_arguments = list(fspec.args)[:nposargs]
        self.optional_arguments = list(fspec.args)[nposargs:]
        self.ismethod = inspect.ismethod(function)
        if self.ismethod:
            # remove first argument if not an optional argument
            self.positional_arguments = self.positional_arguments[1:]
            self.instance = (function.im_self if hasattr(function, 'im_self')
                             else None)
        opsign = ['%s=%r' % (a, d) for a, d in zip(self.optional_arguments,
                                                   self.defaults)]
        self.signiture = ', '.join(self.positional_arguments + opsign)
        self.doc = (function.__doc__ or '')
        self.__doc__ = self.doc
        self.name = function.__name__
        self.kwargs = fspec.keywords
        self.varargs = fspec.varargs
        self.function = function
        self.code = "".join(inspect.getsourcelines(function)[0])
        return

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def __repr__(self):
        return '<Modelmanager function: %s >' % self.name
