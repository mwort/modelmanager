"""
A modelmanager plugin that enables project cloning.
"""
import os
import os.path as osp
import shutil
from glob import glob

from modelmanager import Project
from modelmanager.project import ProjectDoesNotExist
from modelmanager import utils


class Clone(object):
    """
    Project cloning plugin.

    Optional project variables:
    clonesdir    Directory where clones are created/found.
    clonelinks   List of relative paths for which symlinks will be created.
    cloneignore  List of relative paths to ignore for clones
    """

    def __init__(self, project):
        self.project = project
        if hasattr(project, 'clonesdir'):
            self.resourcedir = self.project.clonesdir
        else:
            self.resourcedir = osp.join(project.resourcedir, "clones")
            project.settings(clonesdir=self.resourcedir)
        # make sure it exists
        if not osp.exists(self.resourcedir):
            os.mkdir(self.resourcedir)
        return

    def _get_path_by_name(self, name):
        path = osp.join(self.project.clonesdir, name)
        if not osp.exists(path):
            raise ProjectDoesNotExist('Clone does not exist in %s.'
                                      % self.project.clonesdir)
        return path

    def names(self):
        names = glob(osp.join(self.project.clonesdir, '*'))
        namesdir = [osp.relpath(n, self.project.clonesdir)
                    for n in sorted(names) if osp.isdir(n)]
        return namesdir

    def load_clone(self, name):
        # clone settings (non-persistent)
        kwargs = {'cloned': True,
                  'cloneparent': self.project,
                  'clonename': name}
        return ClonedProject(self._get_path_by_name(name), **kwargs)

    def __getitem__(self, key):
        """
        Load an existing clone.
        """
        return self.load_clone(key)

    def create(self, name, fresh=False, linked=True, verbose=False):
        '''
        Clone the project by creating a dir in project.clonesdir.

        Arguments:
        ----------
        name: Name of clone to create. If exists, return ClonedProject.
        fresh: Remove existing clone of same name and recreate.
        linked: Create symlink to project.resourcedir.
        verbose: Print actions.

        Optional project settings:
        --------------------------
        clonesdir: Directory to create clones. (default: resourcedir/clones)
        clonelinks: List of path patterns to create links to rather than copy.
        cloneignore: List of path patterns to ignore when cloning.

        Return a Project instance
        '''
        def printverbose(args):
            if verbose:
                print(args)
            return
        pj = os.path.join
        prel = os.path.relpath
        # project variables
        prodir = self.project.projectdir
        clonesdir = self.project.clonesdir  # checked in __init__
        clonelinks = getattr(self.project, 'clonelinks', [])
        cloneignore = getattr(self.project, 'cloneignore', [])

        # link or ignore project.resourcedir
        resdir = prel(self.project.resourcedir, prodir)
        if linked:
            clonelinks.append(resdir)
        else:
            cloneignore.append(prel(self.resourcedir, prodir))
            if hasattr(self.project, 'browser'):
                cloneignore.append(prel(self.browser.settings.dbpath, prodir))
        printverbose('Ignore rules: %r' % cloneignore)
        printverbose('Link rules: %r' % clonelinks)
        # new projectdir
        cprodir = pj(clonesdir, name)
        # remove if fresh and already exists
        if os.path.exists(cprodir):
            if fresh:
                printverbose('Removing %s' % cprodir)
                shutil.rmtree(cprodir)
            else:
                print('Clone %s already exists, will try to load it.'
                      % cprodir)
                return self.load_clone(name)

        # copy
        utils.copy_resources(prodir, cprodir, ignorepatterns=cloneignore,
                             linkpatterns=clonelinks, verbose=verbose)

        # return loaded project
        return self.load_clone(name)

    def __call__(self, name, **kwargs):
        """Create clone. See clone.create()"""
        return self.create(name, **kwargs)


class ClonedProject(Project):
    pass
