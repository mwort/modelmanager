"""
A plugin to read and write model (parameter) files based on a template system.
"""
import os
import os.path as osp
import string

from modelmanager import utils

try:
    import parse
except ImportError:
    raise ImportError('The templates plugin requires the python parse '
                      'package to be installed. Try pip install parse')


class Templates(object):
    """
    Templates modelmanager plugin.

    Place templates with named placeholders (see below) into the modelmanager
    resourcedir templates directory with the same name (and path, i.e. add
    directories) as those in the projectdir.

    Read/write values from/to any templated file:
    value = project.templates('key')
    project.templates(key=value)

    Or from/to particular template:
    values = project.templates['partofpath'].read_values()  # dict of values
    project.templates['partofpath'].write_values(key=value)

    Compatible template placeholder field types:
    {name}   string (w/o spaces)
    {name:d} int/digits
    {name:f} float
    {name:g} general numbers, float or int
    """

    def __init__(self, project):
        self.project = project
        self.resourcedir = osp.join(project.resourcedir, 'templates')

        if not osp.exists(self.resourcedir):
            self._install()
        return

    def _install(self):
        """
        Install method for convenient overwriting by subclasses.
        """
        os.mkdir(self.resourcedir)
        return

    def get_template(self, pathorpart):
        """
        Get template with any part of the relative path.
        Returns a template instance or throws error if no or multiple found.
        """
        if osp.exists(osp.join(self.resourcedir, pathorpart)):
            return Template(osp.join(self.resourcedir, pathorpart),
                            osp.join(self.project.projectdir, pathorpart))
        else:
            tmplts = self.get_templates('*' + pathorpart + '*')
            assert len(tmplts) == 1, ("%s matches %s template paths."
                                      % (pathorpart, len(tmplts)))
            return tmplts[0]

    def get_templates(self, pattern='*'):
        """
        Get template instances by pattern.
        Returns a list of matching templates.
        """
        matches = utils.get_paths_pattern(pattern, self.resourcedir)
        tpts = [Template(osp.join(self.resourcedir, path),
                         osp.join(self.project.projectdir, path))
                for path in matches]
        return tpts

    def __call__(self, *getvalues, **setvalues):
        """
        Global value getter and setter.
        Returns value if one name was passed into getvalues, if more returns
        a dictionary, and if only setvalues returns none.
        """
        assert len(getvalues) > 0 or len(setvalues) > 0, ("No values to get "
                                                          "or set.")
        gotvalues = {}
        setvals = setvalues.copy()
        for t in self.get_templates():
            values = t.read_values()
            for gv in getvalues:
                if gv in values:
                    gotvalues[gv] = values[gv]
            valset = {k: setvals.pop(k) for k in setvalues if k in values}
            if valset:
                t.write_values(**valset)
        # ensure everything asked for was completed
        if len(setvalues) > 0 and len(setvals) > 0:
            raise KeyError('Could not set all values: %s' % setvals)
        if len(getvalues) > 0:
            result = [v for v in getvalues if v not in gotvalues]
            if len(result) > 0:
                raise KeyError('Could not find values for %s' % result)
            ret = tuple([gotvalues.pop(v) for v in getvalues])
            return ret if len(ret) > 1 else ret[0]
        return

    def __getitem__(self, pathorpart):
        return self.get_template(pathorpart)


class Template(object):
    """
    A representation of a template and file pair with associated functionality.
    """

    def __init__(self, templatepath, filepath):
        assert osp.exists(templatepath), ("Template file does not exist: %s"
                                          % templatepath)
        self.templatepath = templatepath
        assert osp.exists(filepath), ("Templated file does not exist: %s"
                                      % filepath)
        self.filepath = filepath

        self.field_not_found_error_msg = '%s not found in ' + self.templatepath
        return

    @property
    def template(self):
        """
        Read a template file into a string.
        """
        with file(self.templatepath) as f:
            tmpstr = f.read()
        return tmpstr

    @property
    def file(self):
        with file(self.filepath) as f:
            tmplted = f.read()
        return tmplted

    @property
    def fields(self):
        flds = string.Formatter().parse(self.template)
        return {name: (lit, spec, conv) for lit, name, spec, conv in flds}

    def __repr__(self):
        return '<Template %s / %s>' % (self.templatepath, self.filepath)

    def read_values(self, *templatefields):
        """
        Read the values of template into a dictionary.
        """
        # parse with cleaned whitespace
        tw, fw = self.template.split(), self.file.split()
        result = parse.parse(' '.join(tw), ' '.join(fw))
        # unsucessful parsing
        if result is None:
            nw = min(len(tw), len(fw))
            worddiff = [tw[i] + ': ' + fw[i] for i in range(nw)
                        if (tw[i] != fw[i] and not parse.parse(tw[i], fw[i]))]
            ermsg = ('Encountered problem while parsing:\n' +
                     self.templatepath + '\nThese words/fields are different '
                     'or cant be parsed:\n' + '\n'.join(worddiff) + '\nAll '
                     'non-whitespace strings and field types must stricly '
                     'match with those in the template.')
            raise ValueError(ermsg)
        # return dict subset
        if len(templatefields) > 0:
            res = {}
            for f in templatefields:
                if f not in result.named:
                    raise KeyError(self.field_not_found_error_msg % f)
                res[f] = result.named[f]
            # return value only
            if len(res) == 1:
                return res[res.keys()[0]]
        # return all
        else:
            res = result.named
        return res

    def write_values(self, **templatevalues):
        """
        Write any number of template values into a templated file.
        """
        assert len(templatevalues) > 0, "No values to write."
        values = self.read_values()
        for k, v in templatevalues.items():
            if k not in values:
                raise KeyError(self.field_not_found_error_msg % k)
            values[k] = v
        with file(self.filepath, 'w') as f:
            f.write(self.template.format(**values))
        return
