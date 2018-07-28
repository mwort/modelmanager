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
    """

    def __init__(self, project_or_gisdb, location=None, mapset=None,
                 grassbin='grass'):
        if type(project_or_gisdb) is not str:
            self.project = project_or_gisdb
            project_or_gisdb = self.project.grass_db
            location = location or self.project.grass_location
            mapset = mapset or self.project.grass_mapset
            if hasattr(self.project, "grassbin"):
                grassbin = self.project.grassbin
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
        return grass

    def __enter__(self):
        return self.setup()

    def clean(self):
        # remove .gislock and rc file if exists
        env = self.grass.gisenv()
        lf = osp.join(env['GISDBASE'], env['LOCATION_NAME'], env['MAPSET'],
                      '.gislock')
        [os.remove(f) for f in [lf, self.rcfile] if osp.exists(lf)]
        # clean envs
        sys.path = [p for p in sys.path if p is not self.python_package]
        ps = os.pathsep
        rmpaths = [self.addonpath]
        paths = os.environ['PATH'].split(ps)
        os.environ['PATH'] = ps.join([p for p in paths if p not in rmpaths])
        return

    def __exit__(self, *args):
        self.clean()
        return


class GrassAttributeTable(DataFrame):
    """A plugin to represent a grass vector attribute table.

    Specify `database` and `table`, if you dont want to rely on grass to get
    the table connection parameters.
    """
    vector = None
    #: Optional
    layer = 1
    #: Specify a different key index, default is same as grass table or 'cat'
    key = None
    #: dictionary of dictionary-like data or names project setting of those
    #: data must have the same keys as table
    add_attributes = None
    #: list, optional subset of columns to read, writing reads+writes full tbl
    subset_columns = None
    #: optional if it shouldnt call grass to find out
    database = None
    #: optional if it shouldnt call grass to find out
    table = None

    def __init__(self, project, **override):
        super(GrassAttributeTable, self).__init__()
        self.__dict__.update(override)
        self._project = project
        em = 'vector or (database and table) class attributes needed.'
        assert self.vector or (self.database and self.table), em
        if not (self.database and self.table):
            with GrassSession(self._project) as grass:
                tblcon = grass.vector_db(self.vector)[self.layer]
            self.database = tblcon['database']
            self.table = tblcon['table']
            self.key = self.key or tblcon['key']
        self.key = self.key or 'cat'
        # fill dataframe
        self.read()
        return

    def read(self):
        """Read table from db."""
        sc = self.subset_columns
        cols = ','.join(sc if self.key in sc else [self.key]+sc) if sc else '*'
        with self.dbconnection as con:
            tbl = pd.read_sql('select %s from %s;' % (cols, self.table), con)
        tbl.set_index(self.key, inplace=True, verify_integrity=True)
        # fill DataFrame
        super(GrassAttributeTable, self).__init__(tbl)
        # append dictionary-like data
        if self.add_attributes:
            assert type(self.add_attributes) == dict
            self.append_attributes(self.add_attributes)
        return

    @property
    def dbconnection(self):
        return sqlite3.connect(self.database)

    def append_attributes(self, appenddict):
        em = 'append attribute must be a dictionary. %r' % appenddict
        assert type(appenddict) == dict, em
        for k, v in appenddict.items():
            if type(v) == str:
                v = self._project._attribute_or_function_result(v)
            self.loc[:, k] = pd.Series(v)
        return

    def write(self):
        """Save table back to GRASS sqlite3 database.
        """
        dropcols = self.add_attributes.keys() if self.add_attributes else []
        cleantbl = self.drop(dropcols, axis=1)
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
    project settings or its own attributes.
    """

    module = None

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
        with GrassSession(self.project):
            from grass.pygrass.modules import Module
            module = Module(self.module, run_=False)
            for p in module.params_list:
                if p.name in moduleargs:
                    args[p.name] = moduleargs[p.name]
                elif hasattr(self, p.name):
                    args[p.name] = getattr(self, p.name)
                elif hasattr(self.project, p.name):
                    args[p.name] = getattr(self.project, p.name)
                elif p.required:
                    em = p.name + ' argument is required by ' + self.module
                    raise AttributeError(em)
            if not verbose:
                args['stderr_'] = subprocess.PIPE
                args['stdout_'] = subprocess.PIPE
            # run module
            module(**args).run()
            if not verbose:
                for l in module.outputs.stderr.split('\n'):
                    if 'ERROR' in l or 'WARNING' in l:
                        print(l)
        return

    def update(self, **modulekwargs):
        """Run create and postprocess with GRASS_OVERWRITE."""
        GO = 'GRASS_OVERWRITE'
        is_set = GO in os.environ and os.environ[GO] != '0'
        os.environ[GO] = '1'
        self.create(**modulekwargs)
        self.postprocess(**modulekwargs)
        if not is_set:
            os.environ.pop(GO)
        return

    def __call__(self, **modulekwargs):
        """Shortcut for `update`."""
        return self.update(**modulekwargs)

    def postprocess(self, **modulekwargs):
        """Overwrite to perform follow up tasks."""
        return
