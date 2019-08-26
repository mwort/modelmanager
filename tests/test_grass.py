from __future__ import print_function, absolute_import
import unittest
import sys
import os
import subprocess
import cProfile, pstats
import shutil

import pandas as pd

from test_project import create_project
from modelmanager.plugins.grass import GrassSession, GrassAttributeTable

TEST_SETTINGS = """
grass_db = "grassproject/testgrassdb"
grass_location = "testlocation"
grass_mapset =  "testmapset"
"""


class testgrasstbl(GrassAttributeTable):
    vector = 'testvector@PERMANENT'
    key = 'cat'
    obs = pd.DataFrame({1: [12, 2, 2, 4]})


def skip_if_py3(f):
    """Unittest skip test if PY3 decorator."""
    PY2 = sys.version_info < (3, 0)
    return f if PY2 else lambda self: print('not run in PY3.')


class TestGrass(unittest.TestCase):
    projectdir = 'grassproject'

    @classmethod
    def setUpClass(self):
        self.project = create_project(self.projectdir, TEST_SETTINGS)
        # creat test grass db
        locp = os.path.join(self.project.grass_db, self.project.grass_location)
        subprocess.call(('grass -e -c EPSG:4632 '+locp).split())
        # create test vector
        vectorascii = os.path.join(self.project.projectdir, 'testvector.ascii')
        with open(vectorascii, 'w') as f:
            f.write("0|1|s1 \n 1|0|s2")
        subprocess.call(['grass', locp+'/PERMANENT', '--exec', 'v.in.ascii',
                         'in='+vectorascii, 'out=testvector', '--q'])

    def test_session(self):
        with GrassSession(self.project, mapset='PERMANENT') as grass:
            vects = grass.list_strings('vect')
            self.assertIn('testvector@PERMANENT', vects)
        return

    def test_attribute_table(self):
        self.project.settings(testgrasstbl)
        self.assertTrue(hasattr(self.project, 'testgrasstbl'))
        self.assertIsInstance(self.project.testgrasstbl.obs[1], pd.Series)
        self.project.testgrasstbl['new'] = 1000
        self.project.testgrasstbl.write()
        self.project.testgrasstbl.read()
        self.assertEqual(self.project.testgrasstbl['new'].mean(), 1000)

    def test_subset_attribute_table(self):
        class testgrasssubsettbl(testgrasstbl):
            subset_columns = ['cat', 'int_2', 'str_1']
            add_attributes = None
        # read
        self.project.settings(testgrasssubsettbl)
        self.assertTrue(hasattr(self.project, 'testgrasssubsettbl'))
        ptgt = self.project.testgrasssubsettbl
        cols = [ptgt.index.name]+list(ptgt.columns)
        self.assertEqual(cols, testgrasssubsettbl.subset_columns)
        # write
        self.project.testgrasssubsettbl['int_2'] = [9, 9]
        self.project.testgrasssubsettbl.write()
        self.project.testgrasssubsettbl.read()
        self.assertEqual(sum(self.project.testgrasssubsettbl['int_2']), 18)

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.projectdir)
        return


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
