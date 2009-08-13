import unittest
import os
import io
import statevector
import numpy
import tempfile

eps = 1e-10

class BlitzTestCase(unittest.TestCase):
    def test_blitz(self):
        cio = io.cio
        io.cio = None
        arrays = []
        arrays.append(numpy.arange(12).reshape((3,4)))
        arrays.append(numpy.arange(60).reshape((3,4,5)))
        #arrays.append(numpy.arange(120).reshape((2,3,4,5)))
        for a in arrays:
            blitzstr1 = io._numpy2blitz(a)
            na1 = io._blitz2numpy(blitzstr1)
            blitzstr2 = io._numpy2blitz(statevector.StateVector(a))
            na2 = io._blitz2numpy(blitzstr2)
            self.assert_((numpy.abs(a-na1)<eps).all())
            self.assert_((numpy.abs(a-na2)<eps).all())
        io.cio = cio

    def test_cblitz(self):
        if io.cio is None:
            raise Exception("Can't test c extension!")
        arrays = []
        arrays.append(numpy.arange(12).reshape((3,4)))
        arrays.append(numpy.arange(60).reshape((3,4,5)))
        #arrays.append(numpy.arange(120).reshape((2,3,4,5)))
        for a in arrays:
            blitzstr1 = io._numpy2blitz(a)
            na1 = io._blitz2numpy(blitzstr1)
            blitzstr2 = io._numpy2blitz(statevector.StateVector(a))
            na2 = io._blitz2numpy(blitzstr2)
            self.assert_((a==na1).all())
            self.assert_((a==na2).all())

"""
class CppqedTestCase(unittest.TestCase):
    def test_loadcppqed(self):
        basedir = os.path.dirname(__file__)
        testdir = os.path.join(basedir, "test/cppqed")
        for name in os.listdir(testdir):
            path = os.path.join(testdir, name)
            traj, svs = io.load_cppqed(path)

    def test_loadsavestatevector(self):
        basedir = os.path.dirname(__file__)
        testdir = os.path.join(basedir, "test/blitzarray")
        for name in os.listdir(testdir):
            path = os.path.join(testdir, name)
            sv = 

    def test_saveloadstatevector(self):
        SV = statevector.StateVector
        a = SV((1,2,3), time=1)
        b = SV((0,2+1j,5-2j,6), time=1.2)
        pars = (
            a,
            b,
            a^b,
            a^b^a,
            a^a^a^a,
            )
        for sv in pars:
            f = tempfile.TemporaryFile()
            io.save_statevector(f, sv)
            f.seek(0)
            sv2 = io.load_statevector(f)
"""


if __name__ == "__main__":
    unittest.main()
