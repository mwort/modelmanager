"""Test module for the Browser plugin."""
import unittest
import os
import os.path as osp
import shutil
import cProfile, pstats

from modelmanager.project import ProjectDoesNotExist

from test_project import create_project

TEST_SETTINGS = """
from modelmanager.plugins import clone
"""


class Clones(unittest.TestCase):

    projectdir = 'clonetestproject'
    verbose = False

    def setUp(self):
        self.project = create_project(self.projectdir, TEST_SETTINGS)
        self.clone_dir = self.project.clone_dir
        self.assertTrue(osp.exists(self.clone_dir))
        # create some dirs + files
        os.mkdir(self.pd('input'))
        os.mkdir(self.pd('output'))
        open(self.pd('input/params.txt'), 'w').close()
        open(self.pd('input/input.txt'), 'w').close()
        open(self.pd('output/out.txt'), 'w').close()
        os.symlink(osp.relpath(__file__, self.projectdir), self.pd('sym.link'))
        return

    def pd(self, *args):
        return osp.join(self.projectdir, *args)

    def cd(self, *args):
        return osp.join(self.clone_dir, *args)

    def tearDown(self):
        shutil.rmtree(self.projectdir)
        return

    def test_simple_cloning(self):
        clone = self.project.clone('testclone', verbose=self.verbose)
        self.assertTrue(osp.isdir(self.cd('testclone')))
        self.assertTrue(osp.islink(self.cd('testclone/mm')))
        mmln = os.readlink(self.cd('testclone/mm'))
        self.assertTrue(osp.exists(self.cd(mmln)))
        relp = osp.relpath(clone.projectdir, self.cd('testclone'))
        self.assertEqual(relp, '.')
        self.assertTrue(osp.exists(self.cd('testclone/input/input.txt')))

    def test_retrieval(self):
        self.project.clone('testclone', verbose=self.verbose)
        clone = self.project.clone['testclone']
        self.assertTrue(osp.exists(clone.projectdir))
        with self.assertRaises(ProjectDoesNotExist):
            self.project.clone['someclone']

    def test_clone_of_clone(self):
        clone = self.project.clone('testclone', verbose=self.verbose)
        clone.clone('testclone2', verbose=self.verbose)
        self.assertTrue(osp.exists(self.cd('testclone2')))

    def test_clone_ignore(self):
        self.project.settings(clone_ignore=['output/*'])
        self.project.clone('testclone', verbose=self.verbose)
        self.assertFalse(osp.exists(self.cd('testclone/output/out.txt')))
        self.assertTrue(osp.exists(self.cd('testclone/output')))

    def test_clone_links(self):
        lns = ['input/params.txt', 'output']
        self.project.settings(clone_links=lns)
        self.project.clone('testclone', verbose=self.verbose)
        for l in lns:
            self.assertTrue(osp.islink(self.cd('testclone', l)))

    def test_unlinked(self):
        clone = self.project.clone('testclone', linked=False,
                                   verbose=self.verbose)
        self.assertFalse(osp.islink(self.cd('testclone/mm')))
        with open(self.cd('testclone/mm/settings.py')) as cdfile:
            with open(self.pd('mm/settings.py')) as pdfile:
                self.assertEqual(pdfile.read(), cdfile.read())
        # clone of clone
        clone.clone('testclone', verbose=self.verbose)
        self.assertTrue(osp.exists(self.cd('testclone/mm/clones/testclone')))

    def test_remove(self):
        clone = self.project.clone('testclone')
        self.assertTrue(osp.isdir(self.cd('testclone')))
        clone.remove()
        self.assertFalse(osp.exists(self.cd('testclone')))


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
