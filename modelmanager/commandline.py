"""Module for everything to do with the commandline interface."""
import project
import argparse
import inspect


def execute_from_commandline(functions={'init': project.initialise}):
    """Comandline interface.

    Build an argsparse commandline interface by trying to load a project in
    the current directory and accessing the commandline_functions settings. If
    that fails, just show init command.
    """
    try:
        pro = project.Project()
        if hasattr(pro, 'commandline_functions'):
            for f in pro.commandline_functions:
                if hasattr(pro, f):
                    functions[f] = getattr(pro, f)
                else:
                    print('Function %s is listed in commandline_function ' +
                          'settings, but is not found in project.')
    except:
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
        callsig = ['%s=%r' % (a, d) if d is not None else a
                   for a, d in argsdef]
        helpstr = '(%s) ' % ', '.join(callsig) + (f.__doc__ or '')
        fparser = subparsers.add_parser(l, help=helpstr)
        # function arguments
        for a, d in argsdef:
            fparser.add_argument(a if d is None else '--'+a, default=d,
                                 help='(default={0!r})'.format(d)
                                      if d is not None else '')

    args = mainparser.parse_args()
    # send to function and return whatever is returned by the function
    # (pop removes call from dict)
    functions[args.__dict__.pop('call')](**args.__dict__)
    return
