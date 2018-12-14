"""
A modelmanager plugin that enables project cloning.
"""
import os
import os.path as osp
import shutil
from glob import glob

from modelmanager.project import ProjectDoesNotExist
from modelmanager import utils
from modelmanager.settings import parse_settings


class clone(object):
    """
    Project cloning plugin.
    """
    plugin = ['__call__']
    default_resourcedir = 'clones'

    def __init__(self, project):
        self.project = project
        if hasattr(project, 'clone_dir'):
            self.resourcedir = self.project.clone_dir
        else:
            self.resourcedir = osp.join(project.resourcedir,
                                        self.default_resourcedir)
            project.settings(clone_dir=self.resourcedir)
        # make sure it exists
        if not osp.exists(self.resourcedir):
            os.mkdir(self.resourcedir)
        return

    def _get_path_by_name(self, name):
        path = osp.join(self.project.clone_dir, name)
        if not osp.exists(path):
            raise ProjectDoesNotExist('Clone does not exist in %s.'
                                      % self.project.clone_dir)
        return path

    def names(self, pattern='*'):
        names = glob(osp.join(self.project.clone_dir, pattern))
        namesdir = [osp.relpath(n, self.project.clone_dir)
                    for n in sorted(names) if osp.isdir(n)]
        return namesdir

    def load_clone(self, name, **settings):
        # clone settings (non-persistent)
        kwargs = {'cloned': True,
                  'cloneparent': self.project,
                  'clonename': name}
        settings.update(kwargs)

        # dynamically inheriting project class
        class ClonedProject(self.project.__class__, ClonedProjectMixin):
            pass
        if 'projectdir' not in settings:
            settings['projectdir'] = self._get_path_by_name(name)
        return ClonedProject(**settings)

    def __getitem__(self, key):
        """
        Load an existing clone.
        """
        return self.load_clone(key)

    @parse_settings
    def __call__(self, name, fresh=False, linked=True, verbose=False,
                 dir=None, links=[], ignore=[], **settings):
        '''
        Clone the project by creating a dir in project.clone_dir.

        Arguments:
        ----------
        name : str
            Name of clone to create. If exists, return ClonedProject.
        fresh : bool
            Remove existing clone of same name and recreate.
        linked : bool
            Create symlink to project.resourcedir.
        verbose : bool
            Print actions.
        dir : str path
            Directory relative to projectdir to create clones in.
        links : iterable
            List of path patterns to create links to rather than copy.
        ignore : iterable
            List of path patterns to ignore when cloning.
        settings : <any keyword>
            Settings passed on to the clone project instance.

        Returns
        -------
        <clones.ClonedProject> instance
        '''
        def printverbose(args):
            if verbose:
                print(args)
            return
        pj = os.path.join
        prel = os.path.relpath
        # project variables
        prodir = self.project.projectdir
        clonesdir = dir or self.resourcedir  # checked in __init__

        # link or ignore project.resourcedir
        resdir = prel(self.project.resourcedir, prodir)
        if linked:
            links = links + [resdir]  # copy and append!
        else:
            # ignore clones_dir
            ignore = ignore + [prel(self.resourcedir, prodir)]
            if hasattr(self.project, 'browser'):
                bdbpath = prel(self.project.browser.settings.dbpath, prodir)
                ignore.append(bdbpath)
        printverbose('Ignore rules: %r' % ignore)
        printverbose('Link rules: %r' % links)
        # new projectdir
        cprodir = pj(clonesdir, name)
        settings['projectdir'] = cprodir
        # remove if fresh and already exists
        if os.path.exists(cprodir):
            if fresh:
                printverbose('Removing %s' % cprodir)
                shutil.rmtree(cprodir)
            else:
                print('Clone %s already exists, will try to load it.'
                      % cprodir)
                return self.load_clone(name, **settings)

        # copy
        utils.copy_resources(prodir, cprodir, ignorepatterns=ignore,
                             linkpatterns=links, verbose=verbose)

        # return loaded project
        return self.load_clone(name, **settings)


class ClonedProjectMixin(object):
    """Mix-in for ClonedProject dynamically inheriting in Clone.load_clone.
    """
    def remove(self):
        """Remove the clone directory."""
        shutil.rmtree(self.projectdir)
        return
