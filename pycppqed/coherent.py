"""
Provides functionality to calculate in coherent bases.
"""
import itertools
import numpy

try:
    import mpmath as mp
except:
    print "mpmath not found - Calculating coherent bases not posible"

class CoherentBasis:
    """
    A class representing a basis defined by selected coherent vectors.

    It calculates the transformation matrix and provides methods to calculate
    in this basis.

    *Arguments*
        * *states*
            A vector of complex numbers defining the basis states.
    """
    states = None
    trafo = None
    ntrafo = None

    def __init__(self, states):
        self.states = mp.matrix(states)
        self.trafo = self.calculate_trafo(self.states)
        self.ntrafo = numpy.array(self.trafo.tolist(), dtype="complex128")

    @classmethod
    def calculate_trafo(cls, states):
        """
        Calculate the transformation matrix for the given basis vectors.
        """
        return cls.coherent_scalar_product(states, states)

    @staticmethod
    def create_hexagonal_grid(center, d, rings):
        """
        Create a new coherent basis with basis states on a hexagonal grid.

        The basis states are choosen in rings around the center on a hexagonal
        grid with lattice constant d.

        *Arguments*
            * *center*
                A complex number defining the center of the rings.

            * *d*
                A real number defining the lattice constant.

            * *rings*
                An integer giving the number of rings.
        """
        center = mp.mpmathify(center)
        d = mp.mpf(d)
        basis = []
        for i in range(-rings,rings+1):
            if i<0:
                start = -rings-i
                end = rings
            else:
                start = -rings
                end = rings-i
            for j in range(start,end+1):
                basis.append(center+d*i+d/2*j+1j*mp.sqrt(3)/2*d*j)
        return CoherentBasis(basis)

    @staticmethod
    def coherent_scalar_product(alpha,beta):
        """
        Calculate the scalar product of two coherent states.

        *Argument*
            * *alpha*, *beta*
                Complex numbers or vectors of complex numbers, defining the
                coherent states.
        """
        is_matrix = False
        if isinstance(alpha, mp.matrix):
            rows = max((alpha.rows,alpha.cols))
            is_matrix = True
        else:
            alpha = mp.matrix([alpha])
            rows = 1
        if isinstance(beta, mp.matrix):
            cols = max((beta.rows,beta.cols))
            is_matrix = True
        else:
            beta = mp.matrix([beta])
            cols = 1
        r = mp.matrix(rows,cols)
        for i,j in itertools.product(range(rows),range(cols)):
            alpha_i = alpha[i]
            beta_j = beta[j]
            r[i,j] = mp.exp(
                        -mp.mpf(1)/2*(abs(alpha_i)**2 + abs(beta_j)**2)\
                        + mp.conj(alpha_i)*beta_j\
                        )
        if is_matrix:
            return r
        else:
            return r[0,0]

    def dual(self, psi):
        """
        Calculate the dual vector of a vector given in this basis.
        """
        return self.trafo*psi

    def dual_reverse(self, psi):
        """
        Calculate the coordinates of a vector given in the dual basis.
        """
        if psi.cols == 1:
            return mp.cholesky_solve(self.trafo,psi)
        r = mp.matrix(psi.rows,psi.cols)
        for i in range(psi.cols):
            r[:,i] = self.dual_reverse(psi[:,i])
        return r

    def scalar_product(self, psi1, psi2):
        """
        Calculate scalar product of two vectors given in this basis.
        """
        return self.dual(psi1).H*psi2

    def norm(self, psi):
        """
        Calculate the norm of a vector given in this basis.
        """
        return mp.sqrt(self.dual(psi).H*psi)

    def coordinates(self, alpha):
        """
        Calculate the coordinates of the given coherent state in this basis.
        """
        b = self.coherent_scalar_product(self.basis,alpha)
        return self.dual_reverse(b)

    def quantity(self, alpha):
        """
        Calculate the occupation of the states.
        """
        r = alpha.copy()
        for i in range(max([alpha.rows,alpha.cols])):
            r[i] *= mp.conj(dual[i])
        return r

