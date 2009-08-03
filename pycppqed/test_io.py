import unittest
import os
import io
import numpy

class BlitzTestCase(unittest.TestCase):
    def test_blitz(self):
        arrays = []
        arrays.append(numpy.arange(12).reshape((3,4)))
        arrays.append(numpy.arange(60).reshape((3,4,5)))
        for a in arrays:
            blitzstr = io._numpy2blitz(a)
            na = io._blitz2numpy(blitzstr)
            self.assert_((a==na).all())


class CppqedTestCase(unittest.TestCase):
    def test_loadoutput(self):
        basedir = os.path.dirname(__file__)
        testdir = os.path.join(basedir, "test")
        for name in os.listdir(testdir):
            path = os.path.join(testdir, name)
            traj, svs = io.load_cppqed_output(path)


if __name__ == "__main__":
    unittest.main()
