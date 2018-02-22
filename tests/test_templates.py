"""Test module for the Templates plugin."""
import unittest
import os
import cProfile, pstats

import test_project

test_project.TEST_SETTINGS += """
from modelmanager.plugins.templates import Templates
"""

TEST_TEMPLATES = {'input/test_param.txt': ("Test parameters\n{n:d} {d:f}",
                                           "Test parameters\n 1     1.1 "),
                  'input/test_config.pr': ("parameters {test}\n{time}",
                                           "parameters XYZ \n2000-01-01")}


class TestTemplates(test_project.ProjectTestCase):

    def setUp(self):
        super(TestTemplates, self).setUp()
        self.assertTrue(hasattr(self.project, 'templates'))
        self.templates = self.project.templates
        os.mkdir(os.path.join(self.project.projectdir, 'input'))
        os.mkdir(os.path.join(self.templates.resourcedir, 'input'))
        for p, (tmplt, tfile) in TEST_TEMPLATES.items():
            with file(os.path.join(self.templates.resourcedir, p), 'w') as f:
                f.write(tmplt)
            with file(os.path.join(self.project.projectdir, p), 'w') as f:
                f.write(tfile)
        return

    def test_get_template(self):
        for i in ['param', 'config']:
            tmplt = self.templates.get_template(i)
            self.assertIn(os.path.relpath(tmplt.filepath, self.projectdir),
                          TEST_TEMPLATES)

    def test_read_values(self):
        self.assertEqual(self.templates('n'), 1)
        self.assertEqual(self.templates('d'), 1.1)
        self.assertEqual(self.templates('test'), "XYZ")
        self.assertRaises(KeyError, self.templates, "unknown")
        config = self.templates['config']
        # return value only
        self.assertEqual(config.read_values('test'), 'XYZ')
        # return dict
        d = config.read_values('test', 'time')
        self.assertEqual(d['time'], '2000-01-01')
        self.assertRaises(KeyError, config.read_values, 'unknown')

    def test_write_values(self):
        self.templates(n=100)
        self.assertEqual(self.templates('n'), 100)
        self.templates(d=1.111)
        self.assertEqual(self.templates('d'), 1.111)
        self.templates(test='Somelongstr')
        self.assertEqual(self.templates('test'), "Somelongstr")
        self.assertRaises(KeyError, self.templates, unknown=1)
        param = self.templates['param']
        self.assertRaises(KeyError, param.write_values, unknown=1)


if __name__ == '__main__':
    cProfile.run('unittest.main()', 'pstats')
    # print profile stats ordered by time
    pstats.Stats('pstats').strip_dirs().sort_stats('time').print_stats(5)
