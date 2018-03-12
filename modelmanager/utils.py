"""All handy, general utility functionality used throughout the package."""

import os
import os.path as osp
import sys
import fnmatch
import shutil
import inspect


def load_module_path(path, name=None):
    """Load a python module source file python version aware."""
    name = name if name else osp.splitext(osp.basename(path))[0]
    if sys.version_info < (3,):
        import imp
        m = imp.load_source(name, path)
    elif sys.version_info >= (3, 5):
        import importlib.util as iu
        spec = iu.spec_from_file_location(name, path)
        m = iu.module_from_spec(spec)
        spec.loader.exec_module(m)
    else:
        raise ImportError('This python version is not supported: %s'
                          % sys.version_info)
    return m


def load_settings(pathormodule):
    """
    Load settings from a module or a module file.
    """
    module = (pathormodule if inspect.ismodule(pathormodule)
              else load_module_path(pathormodule))
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
        elif inspect.isfunction(obj):
            r["functions"][name] = obj
        elif inspect.isclass(obj):
            r["classes"][name] = obj
        elif isinstance(obj, property):
            r["properties"][name] = obj
        else:
            r["variables"][name] = obj
    return r


def get_paths_pattern(pattern, startdir):
    """
    Get all paths (including in subdirectories) matching pattern.

    Returns list of relative paths from startdir.
    """
    matches = []
    for root, dirnames, filenames in os.walk(startdir):
        fpaths = [os.path.relpath(os.path.join(root, fn), startdir)
                  for fn in filenames]
        matches += fnmatch.filter(fpaths, pattern)
    return matches


def copy_resources(sourcedir, destinationdir, overwrite=False,
                   ignorepatterns=[], linkpatterns=[], verbose=False):
    """
    Copy/sync resource file tree from sourcedir to destinationdir.

    overwrite: Overwrite existing files.
    """
    def printverbose(args):
        if verbose:
            print(args)
        return
    pj = osp.join
    if not osp.exists(destinationdir):
        printverbose('mkdir %s' % destinationdir)
        os.mkdir(destinationdir)

    walker = os.walk(sourcedir, topdown=True)
    for path, dirs, files in walker:
        rpath = osp.relpath(path, sourcedir).replace('.', '')
        # dirs
        subsetdirs = []
        for d in dirs:
            rdir = pj(rpath, d)
            dest = pj(destinationdir, rpath, d)
            if any(fnmatch.fnmatch(rdir, p) for p in ignorepatterns):
                printverbose('Ignoring %s' % rdir)
            # dir to symlink with relative path
            elif any(fnmatch.fnmatch(rdir, p) for p in linkpatterns):
                rsrc = osp.relpath(pj(path, d), osp.dirname(dest))
                printverbose('Linking %s to %s' % (dest, rsrc))
                os.symlink(rsrc, dest)
            # create new dir
            else:
                if not osp.exists(dest):
                    printverbose('mkdir %s' % dest)
                    os.mkdir(dest)
                subsetdirs.append(d)
        # update dirs (change in place will prevent walking into them)
        dirs[:] = subsetdirs
        # files
        for f in files:
            rfil = osp.join(rpath, f)
            dest = pj(destinationdir, rpath, f)
            src = pj(path, f)
            # ignored files
            if any(fnmatch.fnmatch(rfil, p) for p in ignorepatterns):
                printverbose('Ignoring %s' % rfil)
                continue
            # file to symlink with relative path
            elif any(fnmatch.fnmatch(rfil, p) for p in linkpatterns):
                rsrc = osp.relpath(pj(path, f), osp.dirname(dest))
                printverbose('Linking %s to %s' % (dest, rsrc))
                os.symlink(rsrc, dest)
            # copy/relink existing symlinks
            elif osp.islink(src):
                linkto = os.readlink(src)
                lnabs = osp.abspath(pj(path, linkto))
                rsrc = osp.relpath(lnabs, osp.dirname(dest))
                printverbose('Linking %s to %s' % (dest, rsrc))
                os.symlink(rsrc, dest)
            # copy file
            elif not osp.exists(dest) or overwrite:
                printverbose('cp %s to %s' % (src, dest))
                shutil.copy(src, dest)
    return


def propertyplugin(cls):
    """
    Class decorator to create a plugin that is instantiated and returned when
    the project attribute is used to conveniently combine class + constructor.

    Like all plugins, the propertyplugin __init__ method must only accept one
    positional argument, i.e. the project.

    Usage:
    ------
    @propertyplugin
    class result:
        def __init__(self, project):
            pass

    project = swim.Project()
    project.result -> result instance
    """

    def plugin_instatiator(project):
        return cls(project)
    plugin_instatiator.isplugin = True
    plugin_instatiator.plugin_class = cls
    # pass on plugin functions to property.fget.plugin_functions
    if hasattr(cls, 'plugin_functions'):
        mthds = {n: getattr(cls, n, None) for n in cls.plugin_functions}
        plugin_instatiator.plugin_functions = {k: v for k, v in mthds.items()
                                               if callable(v)}
    return property(plugin_instatiator)
