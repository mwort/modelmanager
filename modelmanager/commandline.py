"""Module for everything to do with the commandline interface."""
from __future__ import print_function
import argparse
from argparse import RawTextHelpFormatter
import traceback
import pprint
import sys
import os.path as osp

# optional argcomplete support
try:
    import argcomplete
except ImportError:
    argcomplete = False

from modelmanager.settings import FunctionInfo
from modelmanager.project import ProjectDoesNotExist


class CommandlineInterface(object):
    """The command line interface plugin.

    Arguments
    ---------
    project : <project class>, optional
        Project to read and execute functions and plugins for. If None,
        functions must be given.
    functions : dict
        Functions for cases when no project exists or to override project
        functions. Defaults to ``project.settings.functions``.
    description : str
        Main program description. Default project.__doc__
    """

    def __init__(self, project=None, description=None, **functions):
        """Build the comandline interface."""
        em = 'Either a project or functions must be given.'
        assert project or functions, em

        dscpt = description or (project.__doc__ if project else '')
        mpargs = dict(description=dscpt, formatter_class=RawTextHelpFormatter)
        self.mainparser = argparse.ArgumentParser(**mpargs)
        self.mainparser.add_argument('-p', '--projectdir', metavar='<path>',
                                     help='The project directory')
        # extract project dir without firing parser
        potpd = sys.argv[1] if len(sys.argv) > 1 else ''
        if potpd.startswith('-p') or potpd.startswith('--projectdir'):
            projectdir = potpd.split('=')[1] if '=' in potpd else sys.argv[2]
            msg = 'projectdir %s does not exist.' % projectdir
            assert osp.exists(projectdir), msg
        else:
            projectdir = '.'
        try:
            self.project = project(projectdir=projectdir)
        except ProjectDoesNotExist:
            self.project = None

        if self.project:
            self.functions = {}
            self.function_info = self.project.settings.functions
            self.plugins = self.project.settings.plugins
        else:
            self.plugins = {}
            self.function_info = {n: FunctionInfo(f)
                                  for n, f in functions.items()}
            self.functions = functions

        self.mainsubparser = self.mainparser.add_subparsers(
                                                        metavar='<command>')
        self.mainsubparser.required = True
        # create plugin subparsers
        pisubparsers = {}
        for pi, picls in sorted(self.plugins.items()):
            piname = pi.split('.')[-1]
            pipi = '.'.join(pi.split('.')[:-1])
            subp = pisubparsers[pipi] if pipi else self.mainsubparser
            pisubparsers[pi] = self._add_plugin_subparser(piname, picls, subp)
        # add functions
        for l, f in sorted(self.function_info.items()):
            pipi = '.'.join(l.split('.')[:-1])
            subparser = pisubparsers[pipi] if pipi else self.mainsubparser
            fparser = self._add_function_parser(subparser, l)
            fparser.set_defaults(_function_address=l)
        # attributes filled with parse_args
        self.parsed_namespace = None
        self.varargs = []
        self.kwargs = {}
        if argcomplete:
            argcomplete.autocomplete(self.mainparser)
        return

    def parse_args(self, argslist=None):
        """Parse arguments and convert vargs and kwargs.

        Arguments
        ---------
        argslist : list
            List of commandline arguments for ``argparse.parser.parse_args``.
        """
        args = self.mainparser.parse_args(argslist)
        finfo = self.function_info[args._function_address]
        # build vargs
        varargs = [getattr(args, k) for k in finfo.positional_arguments]
        if finfo.varargs:
            for a in getattr(args, finfo.varargs):
                varargs.append(self.to_python(a))
        # build kwargs
        kwargs = {}
        for n, d in zip(finfo.optional_arguments, finfo.defaults):
            short = n[:1]
            val = getattr(args, (short if hasattr(args, short) else n))
            if val != d:
                kwargs[n] = val
        if finfo.kwargs and getattr(args, finfo.kwargs):
            kw = [a.split('=') for a in getattr(args, finfo.kwargs)]
            errmsg = 'Optional keywords must be "(--)name=value" pairs.'
            assert all([len(a) == 2 for a in kw]), errmsg
            for n, v in kw:
                kwargs[n.replace('-', '')] = self.to_python(v)
        self.function_address = args._function_address
        self.varargs = varargs
        self.kwargs = kwargs
        return varargs, kwargs

    def run(self, function_address=None, varargs=None, kwargs=None):
        """Run any project function from the commandline.

        Arguments
        ---------
        function_address : str, optional
            Dotted function path from project.
            Default: ``self.function_address``
        varargs : list, optional
            Positional arguments parsed to function. Default: ``self.varargs``
        kwargs : dict, optional
            Keyword arguments parsed to function. Default: ``self.kwargs``
        """
        if not ((varargs and kwargs) or (self.varargs and self.kwargs)):
            self.parse_args()
        function_address = function_address or self.function_address
        varargs = varargs or self.varargs
        kwargs = kwargs or self.kwargs
        # excecution message
        vas = ', '.join(['%r' % a for a in varargs])
        kws = ', '.join(['%s=%r' % (k, v) for k, v in sorted(kwargs.items())])
        sig = vas + (', ' if kws and vas else '') + kws
        print('>>> %s(%s)' % (function_address, sig),
              file=sys.stderr)
        function = self._get_function(function_address)
        try:
            res = function(*varargs, **kwargs)
        except Exception:
            traceback.print_exc()
            return
        pprint.pprint(res)
        return res

    def _get_function(self, address):
        if address in self.functions:
            return self.functions[address]
        else:
            return self.project.settings[address]

    def _add_plugin_subparser(self, name, piclass, mainparser):
        help = self._subparser_help(piclass.__doc__)
        helpstr = help if help else name + ' plugin'
        piparser = mainparser.add_parser(name, help=helpstr,
                                         description=piclass.__doc__,
                                         formatter_class=RawTextHelpFormatter)
        pisubparser = piparser.add_subparsers(metavar='<command>')
        # this only works and is needed in PY3
        pisubparser.required = True
        return pisubparser

    def _subparser_help(self, doc):
        doc = doc if doc else ''
        helpstr = doc.strip().split('\n')[0]
        helpstr = helpstr[:43]+'...' if len(helpstr) > 45 else helpstr
        return helpstr

    def _add_function_parser(self, subparser, functionpath):
        f = self.function_info[functionpath]
        helpstr = self._subparser_help(f.doc)
        parser = subparser.add_parser(f.name, help=helpstr, description=f.doc,
                                      formatter_class=RawTextHelpFormatter)
        for a in f.positional_arguments:
            parser.add_argument(a, type=self.to_python)
        if f.varargs:
            parser.add_argument(f.varargs, nargs='*', type=self.to_python,
                                help='parse any additional positional '
                                'arguments (key value)')
        # short version possible?
        shortkw = set([i[:1] for i in f.optional_arguments])
        appendshort = (len(shortkw) == len(f.optional_arguments) and
                       not any([i in f.positional_arguments for i in shortkw]))
        for a, d in zip(f.optional_arguments, f.defaults):
            self._add_optional_argument(parser, f, a, d, short=appendshort)
        if f.kwargs:
            parser.add_argument('--' + f.kwargs, nargs=argparse.REMAINDER,
                                help='parse any additional keyword arguments')
        return parser

    def _add_optional_argument(self, parser, function, argname, default,
                               short=False):
        f, a, d = function, argname, default
        typ = type(d) if d is not None else self.to_python
        hasanno = hasattr(f, 'annotations') and a in f.annotations
        help = (f.annotations[a]+' ' if hasanno else '')
        kw = dict(help=help, default=d)
        args = ['--'+a]
        if typ == bool:
            kw.update(action='store_true', dest=a)
            notkw = dict(action='store_false', dest=a, default=d)
            de = {False: 'disable', True: 'enable'}
            bhs = argparse.SUPPRESS, kw['help']+'(%s %s)' % (de[not d], a)
            kw['help'], notkw['help'] = bhs if d else bhs[::-1]
            parser.add_argument('--not-'+a, **notkw)
        else:
            addhelp = '(default={0!r})'.format(d)
            kw.update(type=typ, help=kw['help']+addhelp)
        # make short version if not already used (h = universal help)
        if short and a[:1] != 'h':
            args.append('-'+a[:1])
        parser.add_argument(*args, **kw)
        return

    @staticmethod
    def to_python(v):
        """Try to convert v to a python type.

        If no conversion is succesful, v is returned as parsed.
        """
        value = v
        try:
            value = eval(v)
        except Exception:
            pass
        return value
