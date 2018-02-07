"""Module for everything to do with the commandline interface."""
import argparse
import inspect

import modelmanager.project


def execute_from_commandline():
    """Comandline interface.

    Build an argsparse commandline interface by trying to load a project in
    the current directory and accessing the commandline_functions settings. If
    that fails, just show init command.
    """
    # non project methods must not have positional arguments
    functions = {'setup': modelmanager.project.setup}
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
    for n, pi in plugins.items():
        pi_subparser = subparser.add_parser(n)
        methods = inspect.getmembers(pi, predicate=inspect.ismethod)
        pi_functions = {n: m for (n, m) in methods if not n.startswith('_')}
        add_subparser_functions(pi_subparser, pi_functions, dest='method')

    args = mainparser.parse_args()
    # send to function and return whatever is returned by the function
    # (pop removes call from dict)
    func = args.__dict__.pop('function')
    if func in plugins:
        method = args.__dict__.pop('method')
        result = getattr(plugins[func], method)(**args.__dict__)
    else:
        result = functions[func](**args.__dict__)
    return result


def add_subparser_functions(mainparser, functions, **kwargs):
    subparser = mainparser.add_subparsers(**kwargs)
    for l, f in functions.items():
        # get function arguments
        fspec = inspect.getargspec(f)
        # create the parser for the functions
        nargs = len(fspec.args) - len(fspec.defaults or [])
        defs = zip(fspec.args, [None]*nargs + list(fspec.defaults or []))
        # remove first argument if not an optional argument
        argsdef = [(a, d) for i, (a, d) in enumerate(defs)
                   if not (i == 0 and d is None)]
        callsig = ['%s=%r' % (a, d) if d is not None else a
                   for a, d in argsdef]
        helpstr = '(%s) ' % ', '.join(callsig) + (f.__doc__ or '')
        fparser = subparser.add_parser(l, help=helpstr)
        # function arguments
        for a, d in argsdef:
            args = a if d is None else '--'+a
            hlpstr = '(default={0!r})'.format(d) if d is not None else ''
            typ = type(d) if d else str
            fparser.add_argument(args, default=d, help=hlpstr, type=typ)
    return subparser
