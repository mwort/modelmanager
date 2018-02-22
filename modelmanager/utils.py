"""All handy, general utility functionality used throughout the package."""

import os
import fnmatch


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
