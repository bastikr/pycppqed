"""
This module provides convenient methods for creating initial conditions.

At the moment the following initial conditions are implemented:
    * :func:`gaussian`
    * :func:`coherent`
"""

import numpy
import numpy.fft as fft
import statevector

def gaussian(x0=0, k0=0, sigma=0.5, fin=6):
    r"""
    Generate a StateVector with a normal distribution.

    *Usage*
        >>> sv = gaussian(x0=0.3, k0=4, sigma=0.6, fin=7)
        >>> print sv
        StateVector(128)

    *Arguments*
        * *x0* (optional)
            Center in the real space.

        * *k0* (optional)
            Center in the k-space.

        * *sigma* (optional)
            Width in the real space :math:`(\sigma = \sqrt{Var(x)})`.

        * *fin* (optional)
            :math:`2^{fin}` determines the amount of sample points.

    *Returns*
        * *sv*
            A :class:`pycppqed.statevector.StateVector` representing this
            gaussian wave packet in the k-space.

    The generated StateVector is normalized and given in the k-space. It
    is the Fourier transformed of the following expression:

        .. math::

            \Psi(x) = \frac {1} {\sqrt[4]{2 \pi}} *
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
    F = F_transl*numpy.exp(-1j*x0*K)
    return statevector.StateVector(F)

def fft_state(sv, position_to_momentum=False):
    r"""
    Convert a particle StateVector between momentum and position space. The
    state `sv` can be a multi-partite StateVector, possibly with different sample points
    in different subspaces. 
    
    *Usage*
        >>> sv1 = gaussian(x0=0.5*numpy.pi)
        >>> sv2 = gaussian(x0=-0.5*numpy.pi, fin=7)
        >>> sv = sv1^sv2
        >>> sv_pos = fft_state(sv)
        >>> pcolor(numpy.abs(sv_pos)**2)
        >>> sv_mom = fft_state(sv_pos, position_to_momentum=True)
        >>> numpy.allclose(sv,sv_mom)
        True
        
    *Arguments*
        * sv
            The StateVector to transform
        
        * *position_to_momentum* (optional)
            If True, convert from position space to momentum space. The default is to convert
            from momentum to position space.
    """
    norm = numpy.sqrt(numpy.prod(sv.shape))
    if position_to_momentum:
        return statevector.StateVector(fft.fftshift(fft.fftn(sv))/norm)
    else:
        return statevector.StateVector(fft.ifftn(fft.ifftshift(sv))*norm)


def coherent(alpha=2, N=20):
    r"""
    Generate a coherent StateVector in the Fock space.

    *Usage*
        >>> sv = coherent(alpha=2, N=20)
        >>> print sv
        StateVector(20)

    *Arguments*
        * *alpha* (optional)
            A complex number specifying the coherent state. (Default is 2)

        * *N* (optional)
            A number determining the dimension of the Fock space. (Default is
            20)

    *Returns*
        * *sv*
            A :class:`pycppqed.statevector.StateVector`.

    The coherent state is given by the formula:

        .. math::

            |\alpha\rangle = e^{-\frac {|\alpha|^2} {2}} \sum_{n=0}^{N}
                                \frac {\alpha^n} {\sqrt{n!}} |n\rangle

    Calculation is done using the recursive formula:

        .. math::

            a_0 = e^{- \frac {|\alpha|^2} {2}}

        .. math::

            a_n = a_{n-1} * \frac {\alpha} {\sqrt n}
    """
    x = numpy.empty(N)
    x[0] = 1
    for n in range(1,N):
        x[n] = x[n-1]*alpha/numpy.sqrt(n)
    x = numpy.exp(-numpy.abs(alpha)**2/2.)*x
    return statevector.StateVector(x)

