"""All handy, general utility functionality used throughout the package."""
import sys
import types
import django
import os.path as osp


def load_module_path(name, path):
    """Load a python module source file python version aware."""
    if True:  # PY==27
        import imp
        m = imp.load_source(name, path)
    elif False:  # PY==33/34
        from importlib.machinery import SourceFileLoader
        srcloader = SourceFileLoader(name, path)
        m = srcloader.load_module()
    else:  # PY 35
        import importlib.util as iu
        spec = iu.spec_from_file_location(name, path)
        m = iu.module_from_spec(spec)
        spec.loader.exec_module(m)

    return m


def inherit(obj, functions):
    """Attach all functions to the object."""
    obj.__dict__.update({f.__name__: types.MethodType(f, obj)
                         for f in functions})
    return


def manage_django(*args):
    """Convenience function for django manage.py commands.
    Dango needs to be setup for this to work.
    """
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage'] + list(args))
    return


def setup_django(pathormodule):
    """Setup django settings w either path to settings or a loaded module."""
    if type(pathormodule) == str and osp.exists(pathormodule):
        set_mod = load_module_path('settings', pathormodule)
    elif isinstance(pathormodule, types.ModuleType):
        set_mod = pathormodule
    else:
        raise IOError('%s must be a valid path or a module instance.'
                      % pathormodule)

    # project specific django modules can not be found unless the path is added
    # to sys.path
#    djdir = osp.dirname(osp.dirname(set_mod.__file__))
#    if djdir in sys.path:
#        sys.path.remove(djdir)
#    sys.path = [djdir] + sys.path
    django.conf.settings._wrapped = django.conf.empty
    django.conf.settings.configure(set_mod)
    django.setup()
    return
