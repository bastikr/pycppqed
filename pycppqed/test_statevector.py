import unittest
import statevector
import numpy

class StateVectorTestCase(unittest.TestCase):
    def test_creation(self):
        sv = statevector.StateVector((1,2,3,4), 1)
        self.assertEqual(sv.dimensions, ((0,3),))
        self.assertEqual(sv.time, 1)
        sv = statevector.StateVector(numpy.empty((12,10)))
        self.assertEqual(sv.dimensions, ((0,11), (0,9)))
        self.assertEqual(sv.time, 0)

    def test_dim2str(self):
        sv = statevector.StateVector(())
        dimstr = sv._dim2str(((0,3),(0,9)))
        self.assertEqual(dimstr, "(0,3) x (0,9)")

    def test_outer(self):
        sv1 = statevector.StateVector((1,2), norm=False)
        sv2 = statevector.StateVector((3,4), norm=False)
        sv = statevector.StateVector(((3,4),(6,8)))
        self.assert_((sv1^sv2==sv).all())
        self.assert_((sv1^(3,4)==sv).all())

    def test_normalize(self):
        sv = statevector.StateVector((5,1,6), norm=True)
        N = (sv*sv.conjugate()).sum()
        self.assert_(0.999<N<1.001)

    def test_adjust(self):
        sv = statevector.StateVector(numpy.sin(numpy.linspace(0,10)))
        sv_new = statevector.adjust(sv, 10)
        self.assertEqual(len(sv_new), 10)


if __name__ == "__main__":
    unittest.main()
