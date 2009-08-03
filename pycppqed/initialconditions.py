import numpy
import numpy.fft as fft
import statevector

def gaussian(x0=0, k0=0, sigma=0.3, fin=6):
    import scipy.stats
    if 8.*sigma > 2*numpy.pi:
        print "Warning: Sigma is maybe too big."
    N = 2**fin
    L = 2*numpy.pi
    dx = L/float(N)
    if sigma < dx:
        print "Warning: Sigma is maybe too small."
    kc = numpy.pi/dx
    K = numpy.linspace(-kc, kc, N, endpoint=False)
    Norm = numpy.sqrt(2*sigma)*numpy.pi**(1./4)
    X_transl = numpy.linspace(-L/2., L/2., N, endpoint=False)
    X = X_transl + x0
    phase = numpy.exp(1j*X*k0)
    f_transl = Norm*scipy.stats.norm(loc=0, scale=sigma).pdf(X_transl)*phase
    F_transl = fft.fftshift(fft.fft(f_transl))*dx/numpy.sqrt(2*numpy.pi)
    F = F_transl*numpy.exp(-1j*(x0-L/2)*K)
    return statevector.StateVector(F)

