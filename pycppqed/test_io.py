import unittest
import os
import io
import statevector
import numpy
import tempfile
import shutil

eps = 1e-10

class BlitzTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.arrays = arrays = []
        arrays.append(numpy.arange(12).reshape((3,4)))
        arrays.append(numpy.arange(60).reshape((3,4,5)))
        arrays.append(numpy.arange(120).reshape((2,3,4,5)))
        arrays.append(numpy.arange(840).reshape((2,3,4,5,7)))

    def test_blitz(self):
        cio = io.cio
        io.cio = None
        for a in self.arrays:
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
        for a in self.arrays:
            blitzstr1 = io._numpy2blitz(a)
            na1 = io._blitz2numpy(blitzstr1)
            blitzstr2 = io._numpy2blitz(statevector.StateVector(a))
            na2 = io._blitz2numpy(blitzstr2)
            self.assert_((a==na1).all())
            self.assert_((a==na2).all())

    def test_loadblitz(self):
        basedir = os.path.dirname(os.path.abspath(__file__))
        testdir = os.path.join(basedir, "test/blitzarray")
        names = os.listdir(testdir)
        names.sort()
        for i, name in enumerate(names):
            path = os.path.join(testdir, name)
            f = open(path)
            blitzstr = f.read()
            f.close()
            array = io._blitz2numpy(blitzstr)
            self.assertEqual(array.ndim, i+1)


class CppqedTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        basedir = os.path.abspath(os.path.dirname(__file__))
        self.cppqeddir = os.path.join(basedir, "test/cppqed")
        self.blitzdir = os.path.join(basedir, "test/blitzarray")

    def test_loadcppqed(self):
        testdir = self.cppqeddir
        for name in os.listdir(testdir):
            path = os.path.join(testdir, name)
            evs, qs = io.load_cppqed(path)

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
            f, path = tempfile.mkstemp(prefix="pycppqed_test_")
            io.save_statevector(path, sv)
            sv2 = io.load_statevector(path)
            os.remove(path)
            self.assert_((sv==sv2).all())

    def test_splitstatevector(self):
        testdir = self.cppqeddir
        for name in os.listdir(testdir):
            readpath = os.path.join(testdir, name)
            evs, qs = io.load_cppqed(readpath)
            tempdirpath = tempfile.mkdtemp(prefix="pycppqed_test_")
            writepath = os.path.join(tempdirpath, "cppqed")
            io.split_cppqed(readpath, writepath)
            evs2, qs2 = io.load_cppqed(writepath)
            svnames = os.listdir(tempdirpath)
            svnames.sort()
            svs2 = [io.load_statevector(os.path.join(tempdirpath, svname))\
                    for svname in svnames[1:]]
            shutil.rmtree(tempdirpath)
            self.assert_((evs2==evs).all())
            svs2 = statevector.StateVectorTrajectory(svs2)
            self.assert_((svs2==qs.statevector).all())


if __name__ == "__main__":
    unittest.main()
