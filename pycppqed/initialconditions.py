import numpy
import numpy.fft as fft
import statevector

def gaussian(x0=0, k0=0, sigma=0.3, fin=6):
    r"""
    Generate a StateVector with a normal distribution.

    *Usage*
        >>> sv = gaussian(x0=0.3, k0=4, sigma=0.6, fin=7)

    *Arguments*
        * *x0*
            Center in the real space.

        * *k0*
            Center in the k-space.

        * *sigma*
            Width in the real space (= sqrt(Var(x))).

        * *fin*
            2**fin determines the amount of sample points.

    The generated StateVector is normalized and given in the k-space. It
    is the Fourier transformed of the following expression:

        .. math::
            
            \Psi(x) = (frac {1} {2 \pi})^{1/4} *
                            e^{-\frac {x^2} {4*{\Delta x}^2}}
    """
    N = 2**fin
    L = 2*numpy.pi
    if 6.*sigma > L:
        print "Warning: Sigma is maybe too big."
    dx = L/float(N)
    if sigma < dx:
        print "Warning: Sigma is maybe too small."
    kc = numpy.pi/dx
    K = numpy.linspace(-kc, kc, N, endpoint=False)
    X_transl = numpy.linspace(-L/2., L/2., N, endpoint=False)
    X = X_transl + x0
    phase = numpy.exp(1j*X*k0)
    Norm = 1/(2*numpy.pi)**(1./4)/numpy.sqrt(sigma)
    f_transl = Norm*numpy.exp(-X_transl**2/(4*sigma**2))*phase
    F_transl = fft.fftshift(fft.fft(f_transl))*dx/numpy.sqrt(2*numpy.pi)
    F = F_transl*numpy.exp(-1j*(x0-L/2)*K)
    return statevector.StateVector(F)


def coherent(alpha, N):
    r"""
    Generate a coherent StateVector in the Fock space.

    *Usage*
        >>> sv = coherent(alpha=2, N=20)
        >>> print sv
        StateVector(20)

    *Arguments*
        * *alpha*
            A complex number specifying the coherent state.

        * *N*
            A number determining the dimension of the Fock space.

    The coherent state is calculated by the formula:

        .. math::

            |\alpha\rangle = e^{-\frac {|\alpha|^2} {2}} \sum_{n=0}^{N}
                                \frac {\alpha^n} {\sqrt{n!}} |n\rangle
    """
    import scipy
    n = numpy.arange(N)
    x = alpha**n/(numpy.sqrt(scipy.factorial(n)))
    return statevector.StateVector(x, norm=True)

