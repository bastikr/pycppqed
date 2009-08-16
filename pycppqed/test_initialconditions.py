import unittest
import numpy
import initialconditions as ic

eps = 1e-12

class InitialConditionsTestCase(unittest.TestCase):
    def test_gaussian(self):
        pars = (
            (1,0,0.1,7),
            (0,5,0.07,7),
            (1.2,7.6,0.23,7),
            )
        for x0, k0, sigma, fin in pars:
            F = ic.gaussian(x0, k0, sigma, fin)
            N = 2**fin
            X = numpy.linspace(-numpy.pi, numpy.pi, N, endpoint=False)
            dx = X[1]-X[0]
            K = numpy.arange(-N/2, N/2)
            self.assert_(numpy.abs(F.norm()-1)<eps)
            self.assert_(numpy.abs(F.diagexpvalue(K)-k0)<eps)
            f = F.fft()
            self.assert_(numpy.abs(f.norm()*numpy.sqrt(dx)-1)<eps)
            ev_x0 = f.diagexpvalue(X)*dx
            ev_x0square = f.diagexpvalue(X**2)*dx
            std_x0 = numpy.sqrt(ev_x0square - ev_x0**2)
            self.assert_(numpy.abs(ev_x0-x0)<eps)
            self.assert_(numpy.abs(std_x0-sigma)<eps)

    def test_coherentstate(self):
        pars = (
            (4.2,100),
            (3,50),
            (2,40),
            (1.2,30),
            (0.9,20),
            )
        for alpha, N in pars:
            sv = ic.coherent(alpha, N)
            self.assert_(numpy.abs(sv.norm()-1)<eps)
            a = numpy.diag(numpy.sqrt(numpy.arange(1,N)),1)
            at = numpy.diag(numpy.sqrt(numpy.arange(1,N)),-1)
            ev_a = sv.expvalue(a)
            ev_n = sv.expvalue(numpy.dot(at,a))
            self.assert_(numpy.abs(ev_a - alpha)<eps)
            self.assert_(numpy.abs(ev_n - numpy.abs(alpha)**2)<eps) 


def suite():
    load = unittest.defaultTestLoader.loadTestsFromTestCase
    suite = unittest.TestSuite([
            load(InitialConditionsTestCase),
            ])
    return suite


if __name__ == "__main__":
    unittest.main()
