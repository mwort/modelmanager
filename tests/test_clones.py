"""Test module for the Browser plugin."""
import unittest
import os
import os.path as osp
import shutil
import cProfile, pstats

from modelmanager.project import ProjectDoesNotExist

from test_project import create_project

TEST_SETTINGS = """
from modelmanager.plugins import Clones
"""


class Clones(unittest.TestCase):

    projectdir = 'clonestestproject'
    verbose = False

    def setUp(self):
        self.project = create_project(self.projectdir, TEST_SETTINGS)
        self.clonesdir = self.project.clonesdir
        self.assertTrue(osp.exists(self.clonesdir))
        # create some dirs + files
        os.mkdir(self.pd('input'))
        os.mkdir(self.pd('output'))
        file(self.pd('input/params.txt'), 'w').close()
        file(self.pd('input/input.txt'), 'w').close()
        file(self.pd('output/out.txt'), 'w').close()
        os.symlink(osp.relpath(__file__, self.projectdir), self.pd('sym.link'))
        return

    def pd(self, *args):
        return osp.join(self.projectdir, *args)

    def cd(self, *args):
        return osp.join(self.clonesdir, *args)

    def tearDown(self):
        shutil.rmtree(self.projectdir)
        return

    def test_simple_cloning(self):
        clone = self.project.clones.create_clone('testclone',
                                                 verbose=self.verbose)
        self.assertTrue(osp.isdir(self.cd('testclone')))
        self.assertTrue(osp.islink(self.cd('testclone/mm')))
        mmln = os.readlink(self.cd('testclone/mm'))
        self.assertTrue(osp.exists(self.cd(mmln)))
        relp = osp.relpath(clone.projectdir, self.cd('testclone'))
        self.assertEqual(relp, '.')
        self.assertTrue(osp.exists(self.cd('testclone/input/input.txt')))

    def test_retrieval(self):
        self.project.clones.create_clone('testclone', verbose=self.verbose)
        clone = self.project.clones['testclone']
        self.assertTrue(osp.exists(clone.projectdir))
        with self.assertRaises(ProjectDoesNotExist):
            self.project.clones['someclone']

    def test_clone_of_clone(self):
        clone = self.project.clones.create_clone('testclone',
                                                 verbose=self.verbose)
        clone.clones.create_clone('testclone2', verbose=self.verbose)
        self.assertTrue(osp.exists(self.cd('testclone2')))

    def test_cloneignore(self):
        self.project.settings(cloneignore=['output/*'])
        self.project.clones.create_clone('testclone', verbose=self.verbose)
        self.assertFalse(osp.exists(self.cd('testclone/output/out.txt')))
        self.assertTrue(osp.exists(self.cd('testclone/output')))

    def test_clonelinks(self):
        lns = ['input/params.txt', 'output']
        self.project.settings(clonelinks=lns)
        self.project.clones.create_clone('testclone', verbose=self.verbose)
        for l in lns:
            self.assertTrue(osp.islink(self.cd('testclone', l)))

    def test_unlinked(self):
        clone = self.project.clones.create_clone('testclone', linked=False,
                                                 verbose=self.verbose)
        self.assertFalse(osp.islink(self.cd('testclone/mm')))
        self.assertEqual(file(self.pd('mm/settings.py')).read(),
                         file(self.cd('testclone/mm/settings.py')).read())
        # clone of clone
        clone.clones.create_clone('testclone', verbose=self.verbose)
        self.assertTrue(osp.exists(self.cd('testclone/mm/clones/testclone')))


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
