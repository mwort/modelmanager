"""This is a collection of grass-related plugins."""

from __future__ import absolute_import
import os
import os.path as osp
import sys
import subprocess
import sqlite3

try:
    import pandas as pd
    from pandas import DataFrame
except ImportError:
    raise ImportError('The grass plugin requires the pandas package '
                      'for the GrassAttributeTable plugin. '
                      'Try pip install pandas')


class GrassSession(object):
    """Open a GRASS session in a mapset without launching GRASS.

    To be used as a context. The context variable is the grass.script module:
    with GrassSession('path/to/mapset') as grass:
        grass.run_command()

    Arguments
    ---------
    project_or_gisdb : project | str path
        Project instance with the settings (below) or the path to a GRASS
        database or straight to the mapset if location and mapset are None.
    location, mapset : str, optional
    grassbin : str
        Name or path of GRASS executable.

    Settings
    --------
    grass_db : str path
        Path to grass database.
    grass_location : str
        Grass location name.
    grass_mapset : str
        Grass mapset where to write to.
    grassbin : str, optional (default=grass)
        Name or path of the grass executable.
    grass_overwrite : bool, optional
        Always overwrite maps.
    """

    def __init__(self, project_or_gisdb, location=None, mapset=None,
                 overwrite=None, verbose=None, grassbin='grass'):
        if type(project_or_gisdb) is not str:
            self.project = project_or_gisdb
            project_or_gisdb = self.project.grass_db
            location = location or self.project.grass_location
            mapset = mapset or self.project.grass_mapset
            if hasattr(self.project, "grassbin"):
                grassbin = self.project.grassbin
            if hasattr(self.project, "grass_overwrite") and overwrite is None:
                overwrite = self.project.grass_overwrite
        gisdb = project_or_gisdb
        # if gisdb is path to mapset
        assert osp.exists(gisdb), 'gisdb doesnt exist: %s' % gisdb
        if not location and not mapset:
            gisdb = gisdb[:-1] if gisdb.endswith('/') else gisdb
            mapset = os.path.basename(gisdb)
            dblo = os.path.dirname(gisdb)
            location = os.path.basename(dblo)
            gisdb = os.path.dirname(dblo)
        errmsg = 'location %s doesnt exist.' % location
        assert osp.exists(osp.join(gisdb, location)), errmsg
        self.gisdb, self.location, self.mapset = gisdb, location, mapset
        # query GRASS 7 itself for its GISBASE
        errmsg = "%s not found or not executable." % grassbin
        assert self._which(grassbin), errmsg
        startcmd = [grassbin, '--config', 'path']
        p = subprocess.Popen(startcmd, shell=False, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            raise ImportError("ERROR: Cannot find GRASS GIS 7 start script "
                              "using %s. Try passing correct grassbin."
                              % (' '.join(startcmd)))
        self.gisbase = out.decode().strip().split('\n')[-1]
        userdir = osp.expanduser("~")
        self.addonpath = osp.join(userdir, '.grass7', 'addons', 'scripts')
        self.python_package = os.path.join(self.gisbase, "etc", "python")

        self.overwrite = GrassOverwrite(overwrite, verbose=verbose)
        return

    def _which(self, program):
        fpath, fname = os.path.split(program)
        if fpath:
            if os.path.isfile(program) and os.access(program, os.X_OK):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
                    return exe_file
        return None

    def setup(self):
        # Set environment variables
        os.environ['GISBASE'] = self.gisbase
        os.environ['GISDBASE'] = self.gisdb
        # add path to GRASS addons depends on build/platform
        os.environ['PATH'] += os.pathsep + self.addonpath
        sys.path.insert(0, self.python_package)

        import grass.script as grass
        from grass.script import setup

        self.grass = grass
        self.rcfile = setup.init(self.gisbase, self.gisdb,
                                 self.location, 'PERMANENT')
        # always create mapset if it doesnt exist
        if self.mapset != 'PERMANENT':
            grass.run_command('g.mapset', mapset=self.mapset, flags='c',
                              quiet=True)
        self.overwrite.__enter__()
        return grass

    def __enter__(self):
        return self.setup()

    def clean(self):
        # remove .gislock and rc file if exists
        env = self.grass.gisenv()
        lf = osp.join(env['GISDBASE'], env['LOCATION_NAME'], env['MAPSET'],
                      '.gislock')
        for f in [lf, self.rcfile]:
            try:
                os.remove(f)
            except OSError:
                pass
        # clean envs
        sys.path = [p for p in sys.path if p is not self.python_package]
        ps = os.pathsep
        rmpaths = [self.addonpath]
        paths = os.environ['PATH'].split(ps)
        os.environ['PATH'] = ps.join([p for p in paths if p not in rmpaths])
        self.overwrite.__exit__()
        return

    def __exit__(self, *args):
        self.clean()
        return


class GrassOverwrite(object):
    """Context processor to overwrite GRASS mapsself."""
    OVERWRITE = 'GRASS_OVERWRITE'
    VERBOSE = "GRASS_VERBOSE"

    def __init__(self, overwrite=True, verbose=None):
        """
        Arguments
        ---------
        overwrite : bool
            Convenience argument to avoid putting the context in if block.
        verbose : bool | int(-1 ... 3), optional
            Optional verbosity setting in the context.
        """
        self.overwrite = bool(overwrite)
        self.verbose = int(verbose) if verbose is not None else None
        return

    def __enter__(self):
        GO = self.OVERWRITE
        self.is_set = GO in os.environ and os.environ[GO] != '0'
        self.verbose_is_set = self.VERBOSE in os.environ
        if self.overwrite:
            os.environ[GO] = '1'
        if self.verbose is not None and not self.verbose_is_set:
                os.environ[self.VERBOSE] = str(self.verbose)
        return

    def __exit__(self, *args):
        if not self.is_set and self.overwrite:
            os.environ.pop(self.OVERWRITE)
        if not self.verbose_is_set and self.verbose is not None:
            os.environ.pop(self.VERBOSE)
        return

    def __bool__(self):
        return self.overwrite

    def __nonzero__(self):
        return self.overwrite


class GrassAttributeTable(DataFrame):
    """A plugin to represent a grass vector attribute table.

    Specify `database` and `table`, if you dont want to rely on grass to get
    the table connection parameters.
    """
    vector = None
    #: Optional
    layer = 1
    #: Specify a different key index, default is the first column
    key = None
    #: list, optional subset of columns to read, writing reads+writes full tbl
    subset_columns = None
    #: optional if it shouldnt call grass to find out
    database = None
    #: optional if it shouldnt call grass to find out
    table = None
    #: needed to stop exposing all pd.DataFrame methods
    plugin = []

    def __init__(self, project, **override):
        super(GrassAttributeTable, self).__init__()
        self.__dict__.update(override)
        self.project = project
        em = 'vector class attribute (str) needed (others are optional).'
        assert type(self.vector) == str, em
        nms = self.vector.split('@')
        self.mapset = nms[1] if len(nms) > 1 else project.grass_mapset
        self.table = self.table or nms[0]
        dfdb = osp.join(project.grass_db, project.grass_location, self.mapset,
                        'sqlite', 'sqlite.db')
        self.database = self.database or dfdb
        self.key = self.key or 0
        # fill dataframe
        self.read()
        return

    def read(self):
        """Read table from db."""
        sc = self.subset_columns
        cols = ','.join(sc) if sc else '*'
        with self.dbconnection as con:
            tbl = pd.read_sql('select %s from %s;' % (cols, self.table), con)
        self.key = tbl.columns[self.key] if type(self.key) == int else self.key
        tbl.set_index(self.key, inplace=True, verify_integrity=True)
        # fill DataFrame
        super(GrassAttributeTable, self).__init__(tbl)
        return

    @property
    def dbconnection(self):
        return sqlite3.connect(self.database)

    def write(self):
        """Save table back to GRASS sqlite3 database.
        """
        cleantbl = self
        with self.dbconnection as con:
            if self.subset_columns:  # read other columns
                tbl = pd.read_sql('select * from %s;' % self.table, con)
                tbl.set_index(self.key, inplace=True, verify_integrity=True)
                tbl[cleantbl.columns] = cleantbl
                cleantbl = tbl
            cleantbl.to_sql(self.table, con, if_exists='replace')
        return


class GrassModulePlugin(object):
    """A representation of a grass module that takes arguments from either
    project settings specified by ``argument_setting`` or its own attributes.
    """
    #: Name of module
    module = None
    #: name of dictionary project setting to look for default arguments
    argument_setting = None

    def __init__(self, project):
        self.project = project
        errmsg = '%s.module has to be set.' % self.__class__.__name__
        assert self.module, errmsg
        return

    def create(self, verbose=True, **moduleargs):
        """Run the related grass module.

        Arguments
        ---------
        verbose : bool
            Print all module output. If False, only WARNINGS and ERRORS are
            printed at the end.
        **moduleargs :
            Override any arguments of the module alredy set in settings.
        """
        args = {}
        aset = self.argument_setting
        if aset and hasattr(self.project, aset):
            arg_setting = getattr(self.project, aset)
            arg_setting = arg_setting if type(arg_setting) == dict else {}
        else:
            arg_setting = {}

        with GrassSession(self.project):
            from grass.pygrass.modules import Module
            module = Module(self.module, run_=False)
            for p in module.params_list:
                if p.name in moduleargs:
                    args[p.name] = moduleargs[p.name]
                elif p.name in arg_setting:
                    args[p.name] = arg_setting[p.name]
                elif hasattr(self, p.name):
                    args[p.name] = getattr(self, p.name)
                elif p.required:
                    em = p.name + ' argument is required by ' + self.module
                    raise AttributeError(em)
            # run module
            module(quiet=not verbose, **args).run()
        return

    def update(self, **modulekwargs):
        """Run create and postprocess with GRASS_OVERWRITE."""
        with GrassOverwrite():
            self.create(**modulekwargs)
            self.postprocess(**modulekwargs)
        return

    def __call__(self, **modulekwargs):
        """Shortcut for `update`."""
        return self.update(**modulekwargs)

    def postprocess(self, **modulekwargs):
        """Overwrite to perform follow up tasks."""
        return
