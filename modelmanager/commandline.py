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
    try:
        project = modelmanager.project.Project()
        functions.update(project.settings.functions)
    except modelmanager.project.ProjectDoesNotExist:
        pass

    cli_description = "The modelmanager command line interface."

    # create the top-level parser
    mainparser = argparse.ArgumentParser(description=cli_description)
    subparsers = mainparser.add_subparsers(help='function to call',
                                           dest='call')

    for l, f in functions.items():
        # get function arguments
        fspec = inspect.getargspec(f)
        # create the parser for the functions
        nargs = len(fspec.args)-len(fspec.defaults or [])
        defs = [None]*nargs + list(fspec.defaults or [])
        argsdef = zip(fspec.args, defs)
        # remove self
        if len(argsdef) > 0 and argsdef[0][0] == 'self':
            argsdef = argsdef[1:] if len(argsdef) > 1 else []

        callsig = ['%s=%r' % (a, d) if d is not None else a
                   for a, d in argsdef]
        helpstr = '(%s) ' % ', '.join(callsig) + (f.__doc__ or '')
        fparser = subparsers.add_parser(l, help=helpstr)
        # function arguments
        for i, (a, d) in enumerate(argsdef):
            # skip the first project/self positional argument
            if (i == 0 and not d):
                continue
            args = a if d is None else '--'+a
            hlpstr = '(default={0!r})'.format(d) if d is not None else ''
            typ = type(d) if d else str
            fparser.add_argument(args, default=d, help=hlpstr, type=typ)

    args = mainparser.parse_args()
    # send to function and return whatever is returned by the function
    # (pop removes call from dict)
    func = args.__dict__.pop('call')
    return functions[func](**args.__dict__)
