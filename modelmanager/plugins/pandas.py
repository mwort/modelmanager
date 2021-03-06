"""A collection of pandas data interfaces to a project instance."""
from __future__ import absolute_import
import os.path as osp
from glob import glob
import warnings

try:
    import pandas as pd
except ImportError:
    raise ImportError('The pandas package is required for this plugin. '
                      'Try pip install pandas')


class ProjectOrRunData(pd.DataFrame):
    """
    A representation of data read from either the project, a Run or path.
    """
    path = None
    plugin = []

    def __init__(self, projectrunorpath):
        from modelmanager.project import Project
        # init DataFrame
        pd.DataFrame.__init__(self)
        self.name = self.__class__.__name__
        # instantiated with project
        if Project in projectrunorpath.__class__.__mro__:
            self.project = projectrunorpath
            self.read = self.from_project
            if self.path:
                self.path = osp.join(self.project.projectdir, self.path)
        # instantiated with run
        elif hasattr(projectrunorpath, 'files'):
            from django.conf import settings
            self.project = settings.PROJECT
            self.run = projectrunorpath
            self.path = self.find_file()
            self.read = self.from_run
        elif type(projectrunorpath) == str:
            self.path = projectrunorpath
            self.read = self.from_project
            self.project = None
        else:
            raise IOError('Run includes no saved files.')
        # read file
        if self.path:
            self.from_path(self.path)
        return

    def find_file(self):
        # find file
        fileqs = (self.run.files.filter(tags__contains=self.name) or
                  self.run.files.filter(file__contains=self.name))
        if fileqs.count() > 1:
            print('Found two files for %s, using last!' % self.name)
        elif fileqs.count() == 0:
            raise IOError('No file found for %s!' % self.name)
        fileobj = fileqs.last()
        return fileobj.file.path

    def from_path(self, path, **readkwargs):
        pd.DataFrame.__init__(self, self.read(path, **readkwargs))
        self.path = path
        return self

    def from_run(self, path, **readkwargs):
        """
        Read data from a run instance with files.
        """
        reader = self.reader_by_ext(path)
        return reader(path, **readkwargs)

    def from_project(self, path, **kw):
        """!Overwrite me!"""
        raise NotImplementedError('Cant read this ProjectOrRunData from '
                                  'project, define a from_project method!')

    def from_gzip(self, path, **readkwargs):
        readkwargs['compression'] = 'gzip'
        return self.reader_by_ext(osp.splitext(path)[0])(path, **readkwargs)

    def reader_by_ext(self, path):
        """
        Return the read method from_* using the self.path extension.
        Raises a NotImplementedError if none found.
        """
        ext = osp.splitext(path)[1][1:]  # no dot
        readmethodname = 'from_' + ext
        if not hasattr(self, readmethodname):
            raise NotImplementedError('No method %s to read file %s defined!' %
                                      (readmethodname, path))
        return getattr(self, readmethodname)


class ReadWriteDataFrame(pd.DataFrame):
    """
    A representation of data read and written to file.

    The ``read`` method has to reinitialise the dataframe. An example use as a
    plugin (instantiated on project instantiation)::

        class ProjectData(ReadWriteData):
            path = 'some/relative/path.csv'

            def read(self, **kw):
                data = pd.read_table(self.path)
                pd.DataFrame.__init__(self, data)
                return
            def write(self, **kw):
                # possible error/consistency checking
                assert len(self.columns) == 2, 'must have only 2 columns'
                self.to_csv(self.path)
        # add to project
        p = swimpy.Project('project/')
        p.settings(ProjectData)
        # access the DataFrame
        p.projectdata
        # or modify and write out again
        p.projectdata.write()

    To defer reading of the dataframe until it is actually accessed, decorate
    the class with a ``@modelmanager.utils.propertyplugin``.
    """
    path = None
    plugin = []

    def __init__(self, projectorpath, read=True, **kwargs):
        # init DataFrame
        pd.DataFrame.__init__(self)
        self.name = self.__class__.__name__
        if type(projectorpath) == str:
            self.path, self.project = projectorpath, None
        else:
            self.project = projectorpath
            self.path = osp.join(self.project.projectdir, self.path)
        if read:
            errmsg = self.name + ' file does not exist: ' + self.path
            assert osp.exists(self.path), errmsg
            pd.DataFrame.__init__(self, self.read(**kwargs))
        return

    def __call__(self, data=None, **set):
        """
        Assign read data from file and optionally set and write new values.

        data: <2D-array-like>
            Set entire dataframe.
        **set: <array-like> | <dict>
            Set columns or rows by key. Subset of values can be set by parsing
            a dict. Creates new row if key is neither in columns or index.
        """
        if data is not None:
            pd.DataFrame.__init__(self, data)
            self.write()
        elif set:
            self.read()
            for k, v in set.items():
                ix = slice(None)
                if type(v) == dict:
                    ix, v = zip(*v.items())
                if k in self.columns:
                    self.loc[ix, k] = v
                else:
                    self.loc[k, ix] = v
            self.write()
        else:
            self.read()
        return self

    def __repr__(self):
        rpr = '<%s: %s >\n' % (self.name, osp.relpath(self.path))
        return rpr + pd.DataFrame.__repr__(self)

    def read(self, **kwargs):
        """
        Override me and return pd.DataFrame.
        """
        raise NotImplementedError('Reading of %s not implemented.' % self.name)

    def write(self, **kwargs):
        """
        Override me. Error checking and writing to file should be done here.
        """
        raise NotImplementedError('Writing of %s not implemented.' % self.name)


class R(object):
    """
    Interface plugin to R using rpy2 geared towards pandas interoperability.

    The plugin makes the R object available as a project instance and sources
    all R source files in the project resourcedir.
    """

    def __init__(self, project=None):
        self.project = project
        self._initialize()
        if project:
            self.source_resources()
        return

    def _initialize(self):
        try:
            from rpy2.robjects import r, pandas2ri
        except ImportError:
            raise('Cant import rpy2 needed for the R plugin.')
        # activate automatic pandas dataframe conversion
        pandas2ri.activate()
        self._r = r
        self._pandas2ri = pandas2ri
        return

    def _source_resources(self):
        prd = self.project.resourcedir
        rsrc = sorted(glob(osp.join(prd, '*.r')) + glob(osp.join(prd, '*.R')))
        if len(rsrc) == 0:
            warnings.warn('No R source file found in %s' % prd)
        else:
            for s in rsrc:
                self._r.source(s)
        return

    def to_python(self, obj):
        """Convert a rpy2 object to pandas and python equivalents."""
        return self._pandas2ri.ri2py(obj)

    def __getattr__(self, a):
        return getattr(self._r, a)

    def __call__(self, *args, **kwargs):
        """Call any R string/code."""
        return self._r(*args, **kwargs)
