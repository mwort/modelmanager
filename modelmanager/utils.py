"""All handy, general utility functionality used throughout the package."""

import os
import os.path as osp
import fnmatch
import shutil
import inspect


def load_module_path(path, name=None):
    """Load a python module source file python version aware."""
    name = name if name else osp.splitext(osp.basename(path))[0]
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
    # pass on plugin functions to property.fget.plugin_functions
    if hasattr(cls, 'plugin_functions'):
        mthds = {n: getattr(cls, n, None) for n in cls.plugin_functions}
        plugin_instatiator.plugin_functions = {k: v for k, v in mthds.items()
                                               if inspect.ismethod(v)}
    return property(plugin_instatiator)
