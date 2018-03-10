"""Module for everything to do with the commandline interface."""
import argparse
from argparse import RawTextHelpFormatter
import inspect
from settings import Function


DESCRIPTION = "Your modelmanager command line interface."


def execute_from_commandline(project=None, functions={},
                             description=DESCRIPTION):
    """Build and execute the comandline interface.

    project: project to read and execute functions and plugins for. If None,
        functions must be given.
    functions: a dictionary of functions for cases when no project exists or to
        override project functions.
    description: a program description.
    """
    assert project or functions, 'Either a project or functions must be given.'
    if project:
        pfunc = {n: f for n, f in project.settings.functions.items()
                 if n not in functions}
        functions.update(pfunc)
        plugins = project.settings.plugins
    else:
        plugins = {}
    # create the top-level parser
    mainparser = argparse.ArgumentParser(description=description)
    # add functions
    subparser = add_subparser_functions(mainparser, functions, dest='function',
                                        help='Functions and plugins')
    # add plugin functions
    for n, (pi, methods) in sorted(plugins.items()):
        doc = (pi if inspect.isclass(pi) else pi.__class__).__doc__
        helpstr = doc.strip().split('\n')[0] if doc else n + ' plugin'
        pi_subparser = subparser.add_parser(n, help=helpstr)
        add_subparser_functions(pi_subparser, methods, dest='method')

    args = mainparser.parse_args()
    # send to function and return whatever is returned by the function
    # (pop removes call from dict)
    argsd = args.__dict__
    func = argsd.pop('function')
    method = argsd.pop('method', None)
    # decide what function to call
    if method:
        # get from project to also get propertyplugins
        plugin = getattr(project, func)
        function = Function(getattr(plugin, method))
    else:
        function = functions[func]
    # build vargs
    varargs = [argsd.pop(k) for k in function.positional_arguments]
    if function.varargs:
        varargs += [to_python(a) for a in argsd.pop(function.varargs)]
    # build kwargs
    kwargs = {n: argsd.pop(n) for n in function.optional_arguments}
    if function.kwargs and argsd[function.kwargs]:
        kw = argsd.pop(function.kwargs)
        errmsg = 'Optional keywords must be "--name value" pairs.'
        assert len(kw) % 2 == 0, errmsg
        for n, v in zip(kw[::2], kw[1::2]):
            kwargs[n.replace('-', '')] = to_python(v)

    return function(*varargs, **kwargs)


def add_subparser_functions(mainparser, functions, **kwargs):
    subparser = mainparser.add_subparsers(**kwargs)
    for l, f in sorted(functions.items()):
        helpstr = f.doc.strip().split('\n')[0]
        fparser = subparser.add_parser(l, help=helpstr, description=f.doc,
                                       formatter_class=RawTextHelpFormatter)
        # function arguments
        for a in f.positional_arguments:
            fparser.add_argument(a, type=to_python)
        if f.varargs:
            fparser.add_argument(f.varargs, nargs='*', type=to_python, help=''
                                 'parse any additional positional arguments')
        for a, d in zip(f.optional_arguments, f.defaults):
            args = '--'+a
            hlpstr = '(default={0!r})'.format(d)
            typ = type(d) if d else str
            fparser.add_argument(args, default=d, help=hlpstr, type=typ)
        if f.kwargs:
            fparser.add_argument('--' + f.kwargs, nargs=argparse.REMAINDER,
                                 help='parse any additional keyword arguments')
    return subparser


def to_python(v):
    """
    Try to convert v to a python type.

    If no conversion is succesful, v is returned as parsed.
    """
    value = v
    try:
        value = eval(v)
    except Exception:
        pass
    return value
