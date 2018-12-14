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
import functools

from modelmanager import utils


class SettingsManager(object):
    '''
    Object to manage everything defined in the settings file.
    '''

    settings_file_name = 'settings.py'

    def __init__(self, project):
        self._project = project
        # attributes assigned through load
        self.file = None
        self.module = None
        self.variables = {}
        self.functions = {}
        self.properties = {}
        self.plugins = {}
        self.register_plugin(project.__class__, '')
        return

    def load(self, defaults={}, **override_settings):
        """
        (Re)load and override project settings.

        Reads the settings from the settings file and attaches them to the
        project. Can be used to reload the settings and override settings that
        are used when initialising plugins.
        """
        self.file = self._find_settings()
        self.module = utils.load_module_path(self.file,
                                             remove_byte_version=True)
        # resourcedir cant be overriden
        override_settings["resourcedir"] = osp.dirname(self.file)
        settings = load_settings(self.file)
        settings.update(override_settings)
        # set defaults
        for k, v in defaults.items():
            settings.setdefault(k, v)
        # assign settings to project
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
            self.variables[k] = v
        #  functions (name is same as defined in settings)
        for k, f in settypes['functions'].items():
            fm = types.MethodType(f, self._project)
            setattr(self._project, k, fm)
            self.register_function(fm, k)
        # properties
        for k, p in settypes['properties'].items():
            setattr(self._project.__class__, k, p)
            self.properties[k] = p
            if hasattr(p, 'plugin'):
                self.register_plugin(p.plugin, k)
        # classes to plugins
        for k, c in settypes['classes'].items():
            instance = self._instatiate(c)
            setattr(self._project, k, instance)
            self.register_plugin(c, k)
        return

    def register_function(self, f, name):
        assert callable(f)
        self.functions[name] = FunctionInfo(f)
        return

    def register_plugin(self, cls, name):
        assert inspect.isclass(cls)
        assert type(name) is str, name
        # get functions from instances only if declared
        if hasattr(cls, 'plugin'):
            pif = [(n, getattr(cls, n)) for n in cls.plugin]
        else:
            pif = [(i, o) for i, o in inspect.getmembers(cls)
                   if not i.startswith('_')]
        # filter callables and crawl on
        for i, o in pif:
            fname = name + '.' + i if name else i
            if inspect.isclass(o):
                self.register_plugin(o, fname)
            elif hasattr(o, 'plugin'):
                c = o.plugin if inspect.isclass(o.plugin) else o.__class__
                self.register_plugin(c, fname)
            # special case when plugin is only used as function
            elif i == '__call__':
                self.register_function(o, name)
                self.functions[name].name = name
                return
            elif callable(o):
                self.register_function(o, fname)
        if name:
            self.plugins[name] = cls
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
        Return absolute path if variable is a relative path from project
        directory and includes a /, else return variable.
        """
        if type(variable) == str:
            path = osp.join(self._project.projectdir, variable)
            if osp.exists(path) and osp.sep in variable:
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
            try:
                mod = getattr(mod, comp)
            except AttributeError:
                raise AttributeError('Project doesnt have attribute %s' % key)
        return mod

    def serialise(self):
        '''Default serialisation happens here via json.dumps'''
        return json.dumps(self.variables, indent=1, sort_keys=True)

    def __unicode__(self):
        return unicode(self.__str__())

    def __repr__(self):
        rep = '<SettingsManager for %s>' % self._project
        return rep

    # needs to be revised, maybe remove completely
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


class FunctionInfo(object):
    """
    Representation of a project function.
    """
    def __init__(self, function):
        if isinstance(function, FunctionInfo):
            function = function.function
        if hasattr(function, 'decorated_function'):
            function = function.decorated_function
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

        self.doc = inspect.cleandoc(function.__doc__ or '')
        self.__doc__ = self.doc
        self.name = function.__name__
        self.varargs = fspec.varargs
        self.function = function
        code, self.firstcodeline = inspect.getsourcelines(function)
        self.code = "".join(code)
        nposargs = len(args) - len(self.defaults)
        self.positional_arguments = list(args)[:nposargs]
        self.optional_arguments = list(args)[nposargs:]

        try:
            self.cls = function.im_class
        except AttributeError:
            # in PY3 unbound methods are just functions
            self.cls = None
        if len(self.positional_arguments) > 0:
            self.instance_name = self.positional_arguments[0]
            self.positional_arguments = self.positional_arguments[1:]
        else:
            # best guess
            self.instance_name = 'self'
        opsign = ['%s=%r' % (a, d) for a, d in zip(self.optional_arguments,
                                                   self.defaults)]
        self.signiture = ', '.join(self.positional_arguments + opsign)
        return

    def __call__(self, *args, **kwargs):
        print('Call %s via its project.' % self.name)
        return

    def __repr__(self):
        return '<Modelmanager function: %s >' % self.name

    # these introspection methods need to be called with a project instance somehow
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

    def configured(self):
        return all([hasattr(self.project, a) for a in self.attributes_used])


class SettingsUndefinedError(AttributeError):
    def __init__(self, setting, additionalmessage=None):
        addmessage = additionalmessage + '\n' if additionalmessage else ''
        msg = ('{0}\n\nThe requested project setting is not defined.\n\n{1}'
               'If you want to set it for this session only do: \n'
               'project.settings({0}=<your-value>) \n\n'
               'Or if you want to permanently add it to the project,\n define '
               'it in your settings.py file.').format(setting, addmessage)
        AttributeError.__init__(self, msg)
        return


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


def parse_settings(function):
    """A decorator to parse project settings to a project or plugin method.

    ```
    @parse_settings
    def method(self, arg=None):
        return
    ```
    If the method is called without the `arg=` argument and the `self.project`
    has a `method_arg` setting, the value will be parsed.
    """
    finfo = FunctionInfo(function)
    iscall = finfo.name == '__call__'

    @functools.wraps(function)
    def f(*args, **kwargs):
        # get project instance
        from .project import Project
        inst = args[0]  # assumes method
        if isinstance(inst, Project) or Project in inst.__class__.__bases__:
            prefix = ''
            project = inst
        elif hasattr(inst, 'project'):
            project = inst.project
            prefix = inst.__class__.__name__.lower() + '_'
        else:
            em = ('%s is not a Project instance or doesnt have a project '
                  'attribute.')
            raise AttributeError(em % inst)
        # get settings
        for a in finfo.optional_arguments:
            setname = prefix + ('' if iscall else finfo.name+'_') + a
            if a not in kwargs and hasattr(project, setname):
                kwargs[a] = getattr(project, setname)
        # call function
        return function(*args, **kwargs)
    # add signiture to beginning of docstrign if PY2
    if sys.version_info < (3, 0):
        sig = '%s(%s)\n' % (finfo.name, finfo.signiture)
        f.__doc__ = sig + finfo.doc
    # add generic docs
    add_docs = """

Settings
--------
All keyword arguements: `%s_<kwarg> = value`
"""
    add_docs = add_docs % ('<plugin>' if iscall else '[<plugin>_]<method>')
    function.__doc__ = (finfo.doc or '') + add_docs
    # attach original function (finfo has also decorated function)
    f.decorated_function = finfo.function
    return f
