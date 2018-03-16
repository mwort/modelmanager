'''
The modelmanager settings module contains everything concerning the setup,
management and validation of the project settings defined in the settings
.mm/settings.json file.
'''

import sys
import json
import os.path as osp
from glob import glob
import inspect
import types
import traceback
import re

from modelmanager import utils


class SettingsManager(object):
    '''
    Object to manage everything defined in the settings file.
    '''

    settings_file_name = 'settings.py'

    def __init__(self, project):
        self._project = project
        # initial methods
        self.functions = {}
        # attributes assigned through load
        self.file = None
        self.variables = {}
        self.properties = {}
        self.classes = {}
        self.plugins = {}
        # register build-in project "settings"
        self.register(**dict(inspect.getmembers(project)))
        return

    def load(self, **override_settings):
        """
        (Re)load and override project settings.

        Reads the settings from the settings file and attaches them to the
        project. Can be used to reload the settings and override settings that
        are used when initialising plugins.
        """
        self.file = self._find_settings()
        # resourcedir cant be overriden
        override_settings["resourcedir"] = osp.dirname(self.file)
        settings = load_settings(self.file)
        settings.update(override_settings)
        self(**settings)
        return

    def _find_settings(self):
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
        return osp.abspath(sfp[0])

    def __call__(self, *objects, **settings):
        """
        Central settings assign method.

        Calling the SettingsManager with either objects or keyword arguments
        assigns the object or attribute to the project.

        Arguments:
        ----------
        *objects: Any attachable object that has a __name__ attribute.
        **settings: Keywords with name: settings-object pairs.
        """
        # sort out names of objects
        for obj in objects:
            errmsg = ("The object %s does not have a __name__ attribute.\n"
                      "You need to assign it with a keyword argument.") % obj
            assert hasattr(obj, '__name__'), errmsg
            settings[obj.__name__] = obj

        settypes = sort_settings(settings)
        # attach to project
        #  attributes
        for k, v in settypes['variables'].items():
            fv = self._filter_abs_path(v)
            setattr(self._project, k, fv)
        #  functions (name is same as defined in settings)
        for k, f in settypes['functions'].items():
            fm = types.MethodType(f, self._project)
            setattr(self._project, k, fm)
            settings[k] = fm
        # properties
        for k, p in settypes['properties'].items():
            self.properties[k] = p
            setattr(self._project.__class__, k, p)
        # classes to plugins
        for k, c in settypes['classes'].items():
            instance = self._instatiate(c)
            name = k.lower()
            setattr(self._project, name, instance)
            settings[name] = (c, instance)

        self.register(**settings)
        return

    def register(self, **settings):
        """
        Add settings to the SettingsManager register.

        **settings: Keyword settings.

        Note: To register plugins, a tuple of (class, instance) is required,
            otherwise plugins will be registered as variables. Class not part
            of a (class, instance) tuple are not registered.
        """
        settypes = sort_settings(settings)

        # check for plugins
        for n in list(settypes['variables'].keys()):
            v = settypes['variables'][n]
            tuple2 = (type(v) == tuple and len(v) == 2)
            if tuple2 and inspect.isclass(v[0]) and isinstance(v[1], v[0]):
                # remove from variables
                c, pi = settypes['variables'].pop(n)
                methods = inspect.getmembers(pi, predicate=inspect.ismethod)
                methods = {n: Function(m) for (n, m) in methods
                           if not n.startswith('_')}
                self.classes[c.__name__] = c
                self.plugins[n] = (pi, methods)
        #  attributes
        for k, v in settypes['variables'].items():
            fv = self._filter_abs_path(v)
            self.variables[k] = fv
        #  functions (name is same as defined in settings)
        for k, f in settypes['functions'].items():
            self.functions[k] = Function(f)
        # properties
        for k, p in settypes['properties'].items():
            self.properties[k] = p
            # deal with propertyplugins
            if getattr(p, 'isplugin', False):
                plnf = getattr(p, 'plugin_functions', {})
                cl = getattr(p, 'plugin_class')
                plnf = {n: Function(v) for n, v in plnf.items()}
                self.plugins[k] = (cl, plnf)
        return

    def _instatiate(self, cla):
        """Savely instatiate a settings class."""
        try:
            obj = cla(self._project)
        except Exception:
            traceback.print_exc()
            print("Failed to add %s to project." % cla.__name__)
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

    def check(self, verbose=True):
        checked = {(n, None): f.configured for n, f in self.functions.items()}
        for pin, (pi, met) in self.plugins.items():
            checked.update({(n, pin): m.configured for n, m in met.items()})
        if verbose:
            print('Function configuration state:')
            for (n, p), b in sorted(checked.items()):
                fulp = p + '.' + n if p else n
                print('[{0}] - {1}'.format('x' if b else ' ', fulp))
        return None if verbose else checked


class Function(object):
    """
    Representation of a project function.
    """
    def __init__(self, function):
        from modelmanager import Project
        if isinstance(function, Function):
            function = function.function
        # get function arguments
        if sys.version_info < (3, 5):
            fspec = inspect.getargspec(function)
            self.kwargs = fspec.keywords
            args = fspec.args
            self.defaults = list(fspec.defaults or [])
        else:
            fspec = inspect.getfullargspec(function)
            self.kwargs = fspec.varkw
            args = fspec.args + fspec.kwonlyargs
            kwodef = [fspec.kwonlydefaults[k] for k in fspec.kwonlyargs]
            self.defaults = list(fspec.defaults or []) + kwodef
            self.annotations = fspec.annotations

        self.doc = (function.__doc__ or '')
        self.__doc__ = self.doc
        self.name = function.__name__
        self.varargs = fspec.varargs
        self.function = function
        self.code = "".join(inspect.getsourcelines(function)[0])
        nposargs = len(args) - len(self.defaults)
        self.positional_arguments = list(args)[:nposargs]
        self.optional_arguments = list(args)[nposargs:]
        self.ismethod = inspect.ismethod(function)
        if self.ismethod or self.name is '__init__':
            try:
                self.instance = function.im_self
                self.cls = function.im_class
            except AttributeError:
                self.instance = getattr(function, '__self__', None)
                self.cls = self.instance.__class__
            self.instance_name = self.positional_arguments[0]
            self.positional_arguments = self.positional_arguments[1:]
            # project method (and __init__ methods of plugins)
            if (self.name is '__init__' or
                isinstance(self.instance, Project) or
                Project in self.cls.__bases__):
                self.project = self.instance
                self.plugin = None
                self.project_instance_name = self.instance_name
            else:
                self.plugin = self.instance
                # try to infer the project and project_instance_name
                # this does not work for plugins that dont save the project
                # instance in the __init__ method
                try:
                    pinname = self._project_name_from_plugin()
                    pian = pinname.split('.')[1]
                    self.project = getattr(self.instance, pian)
                except Exception:
                    pinname = 'None'
                    self.project = None
                self.project_instance_name = pinname

            self.attributes_set = self._attributes_set()
            self.attributes_used = self._attributes_used()
        opsign = ['%s=%r' % (a, d) for a, d in zip(self.optional_arguments,
                                                   self.defaults)]
        self.signiture = ', '.join(self.positional_arguments + opsign)
        return

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def __repr__(self):
        return '<Modelmanager function: %s >' % self.name

    def _attributes_set(self, variableset=''):
        pin = self.project_instance_name.replace('.', '\.')
        reexp = pin + r'.(\w+) *= *' + variableset
        attrs = re.findall(reexp, self.code)
        reexp = (r'setattr\( *' + pin +
                 ' *, *[\'"](.*?)[\'"] *,')
        attrs += re.findall(reexp, self.code)
        return sorted(set(attrs))

    def _attributes_used(self):
        aset = self.attributes_set
        reexp = self.project_instance_name.replace('.', '\.') + r'.(\w+)'
        attrs = sorted(set(re.findall(reexp, self.code)) - set(aset))
        return attrs

    def _project_name_from_plugin(self):
        """
        Get the dotted name of the project instance for plugin methods.
        This is a risky and guessing operation, therefore best to 'try' this.
        """
        init = Function(self.cls.__init__)
        parsedprojectname = init.positional_arguments[0]
        aname = init._attributes_set(parsedprojectname)
        name = self.instance_name + '.' + aname[0] if aname else None
        return name

    @property
    def configured(self):
        return self.ismethod and all([hasattr(self.project, a)
                                      for a in self.attributes_used])


class SettingsUndefinedError(AttributeError):
    def __init__(self, setting, additionalmessage=None):
        addmessage = additionalmessage + '\n' if additionalmessage else ''
        msg = ('{0}\n\nThe requested project setting is not defined.\n\n{1}'
               'If you want to set it for this session only do: \n'
               'project.settings({0}=<your-value>) \n\n'
               'Or if you want to permanently add it to the project,\n define '
               'it in your settings.py file.').format(setting, addmessage)
        super(SettingsUndefinedError, self).__init__(msg)


def load_settings(pathormodule):
    """
    Load settings from a module or a module file.
    """
    module = (pathormodule if inspect.ismodule(pathormodule)
              else utils.load_module_path(pathormodule))
    # filter settings that should be ignored
    settings = {n: obj for n, obj in inspect.getmembers(module)
                if not (inspect.ismodule(obj) or n.startswith('_'))}
    return settings


def sort_settings(settings):
    """
    Separate a dictionary of python objects into setting types.

    Returns a dictionary of dictionaries with type keys.
    """
    r = {n: {} for n in ("functions", "classes", "properties", "variables")}
    for name, obj in settings.items():
        if name.startswith('_'):
            continue
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            r["functions"][name] = obj
        elif inspect.isclass(obj):
            r["classes"][name] = obj
        elif isinstance(obj, property):
            r["properties"][name] = obj
        else:
            r["variables"][name] = obj
    return r
