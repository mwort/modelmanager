"""Module for everything to do with the commandline interface."""
import argparse

import modelmanager.project
from .settings import Function


def execute_from_commandline():
    """Comandline interface.

    Build an argsparse commandline interface by trying to load a project in
    the current directory and accessing the commandline_functions settings. If
    that fails, just show init command.
    """
    # non project methods must not have positional arguments
    functions = {'setup': Function(modelmanager.project.setup)}
    plugins = {}
    try:
        project = modelmanager.project.Project()
        functions.update(project.settings.functions)
        plugins.update(project.settings.plugins)
    except modelmanager.project.ProjectDoesNotExist:
        pass

    cli_description = "Your modelmanager command line interface."

    # create the top-level parser
    mainparser = argparse.ArgumentParser(description=cli_description)
    # add functions
    subparser = add_subparser_functions(mainparser, functions, dest='function',
                                        help='project function')
    # add plugin functions
    for n, (instance, methods) in plugins.items():
        pi_subparser = subparser.add_parser(n)
        add_subparser_functions(pi_subparser, methods, dest='method')

    args = mainparser.parse_args()
    # send to function and return whatever is returned by the function
    # (pop removes call from dict)
    func = args.__dict__.pop('function')
    if func in plugins:
        method = args.__dict__.pop('method')
        instance, inmethods = plugins[func]
        result = inmethods[method](**args.__dict__)
    else:
        result = functions[func](**args.__dict__)
    return result


def add_subparser_functions(mainparser, functions, **kwargs):
    subparser = mainparser.add_subparsers(**kwargs)
    for l, f in functions.items():
        helpstr = '(%s) ' % f.signiture + f.doc
        fparser = subparser.add_parser(l, help=helpstr)
        # function arguments
        for a in f.positional_arguments:
            fparser.add_argument(a, type=str)
        for a, d in zip(f.optional_arguments, f.defaults):
            args = '--'+a
            hlpstr = '(default={0!r})'.format(d)
            typ = type(d) if d else str
            fparser.add_argument(args, default=d, help=hlpstr, type=typ)
    return subparser
