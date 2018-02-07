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
        fi = Function(f)
        helpstr = '(%s) ' % fi.signiture + fi.doc
        fparser = subparser.add_parser(l, help=helpstr)
        # function arguments
        for a, d in fi.arguments:
            args = a if d is None else '--'+a
            hlpstr = '(default={0!r})'.format(d) if d is not None else ''
            typ = type(d) if d else str
            fparser.add_argument(args, default=d, help=hlpstr, type=typ)
    return subparser


class Function(object):
    """
    Representation of a project function with all of attributes.
    """
    def __init__(self, function):
        # get function arguments
        fspec = inspect.getargspec(function)
        # create the parser for the functions
        self.defaults = list(fspec.defaults or [])
        self.noptionalargs = len(fspec.args) - len(self.defaults)
        self.arguments = zip(fspec.args,
                             [None]*self.noptionalargs + self.defaults)
        self.ismethod = inspect.ismethod(function)
        if self.ismethod:
            # remove first argument if not an optional argument
            self.arguments = [(a, d) for i, (a, d) in enumerate(self.arguments)
                              if not (i == 0 and d is None)]
            self.instance = (function.im_self if hasattr(function, 'im_self')
                             else None)
        self.signiture = ', '.join(['%s=%r' % (a, d) if d is not None else a
                                    for a, d in self.arguments])
        self.doc = (function.__doc__ or '')
        self.name = function.__name__
        self.kwargs = (fspec.keywords is not None)
        return
