"""
A modelmanager plugin that enables project cloning.
"""
import os
import os.path as osp
from fnmatch import fnmatch
import shutil
from glob import glob

from modelmanager import Project
from modelmanager.project import ProjectDoesNotExist


class Clones:
    """
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
        return Clone(self._get_path_by_name(name), **kwargs)

    def __getitem__(self, key):
        """
        Load an existing clone.
        """
        return self.load_clone(key)

    def create_clone(self, name, fresh=False, linked=True, verbose=False):
        '''
        Clone the project by creating a dir in project.clonesdir.
        If linked: a symlink to project.resourcedir is created rather than a
        clean resourcedir.
        If fresh: an existing clone with the same name will be overwritten.

        Return a Project instance
        '''
        def printverbose(args):
            if verbose:
                print(args)
            return
        pj = os.path.join
        # project variables
        prodir = self.project.projectdir
        clonesdir = self.project.clonesdir  # checked in __init__
        clonelinks = (getattr(self.project, 'clonelinks')
                      if hasattr(self.project, 'clonelinks') else [])
        cloneignore = (getattr(self.project, 'cloneignore')
                       if hasattr(self.project, 'cloneignore') else [])

        # link or ignore project.resourcedir
        presdir = osp.relpath(self.project.resourcedir, prodir)
        if linked:
            clonelinks.append(presdir)
        else:
            cloneignore.append(presdir)
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

        printverbose('mkdir %s' % cprodir)
        os.mkdir(cprodir)

        # walk over all projectdir paths
        walker = os.walk(self.project.projectdir, topdown=True)
        for path, dirs, files in walker:
            rpath = osp.relpath(path, prodir).replace('.', '')
            # dirs
            subsetdirs = []
            for d in dirs:
                rdir = pj(rpath, d)
                dest = pj(cprodir, rpath, d)
                if any(fnmatch(rdir, p) for p in cloneignore):
                    printverbose('Ignoring %s' % rdir)
                # dir to symlink with relative path
                elif any(fnmatch(rdir, p) for p in clonelinks):
                    rsrc = osp.relpath(pj(path, d), osp.dirname(dest))
                    printverbose('Linking %s to %s' % (dest, rsrc))
                    os.symlink(rsrc, dest)
                # create new dir
                else:
                    printverbose('mkdir %s' % dest)
                    os.mkdir(dest)
                    subsetdirs.append(d)
            # update dirs (change in place will prevent walking into them)
            dirs[:] = subsetdirs
            # files
            for f in files:
                rfil = osp.join(rpath, f)
                dest = pj(cprodir, rpath, f)
                src = pj(path, f)
                # ignored files
                if any(fnmatch(rfil, p) for p in cloneignore):
                    printverbose('Ignoring %s' % rfil)
                    continue
                # file to symlink with relative path
                elif any(fnmatch(rfil, p) for p in clonelinks):
                    rsrc = osp.relpath(pj(path, f), osp.dirname(dest))
                    printverbose('Linking %s to %s' % (dest, rsrc))
                    os.symlink(rsrc, dest)
                # copy/relink existing symlinks
                elif osp.islink(src):
                    linkto = os.readlink(src)
                    lnabs = osp.abspath(pj(path, linkto))
                    rsrc = osp.relpath(lnabs, osp.dirname(dest))
                    printverbose('Linking %s to %s' % (dest, rsrc))
                    os.symlink(rsrc, dest)
                # copy file
                else:
                    printverbose('cp %s to %s' % (src, dest))
                    shutil.copy(src, dest)
        # deal with new resourcedir if not linked
        if not linked:
            from modelmanager import resources
            dest = pj(cprodir, osp.basename(presdir))
            printverbose('Creating defaults in %s' % dest)
            shutil.copytree(osp.dirname(resources.__file__), dest)
            dest = pj(dest, osp.basename(self.project.settings.file))
            printverbose('cp %s to %s' % (self.project.settings.file, dest))
            shutil.copy(self.project.settings.file, dest)

        # return loaded project
        return self.load_clone(name)


class Clone(Project):
    pass


# project.clone function
def clone(project, name, *args, **kwargs):
    return project.clones.create_clone(name, *args, **kwargs)


clone.__doc__ = Clones.create_clone.__doc__
