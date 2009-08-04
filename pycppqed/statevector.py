import numpy
try:
    set()
except NameError:
    from sets import Set as set

class StateVector(numpy.ndarray):
    r"""
    A class representing a quantum mechanical state vector.

    **Usage**
        >>> sv = StateVector((0.3, 0.4, 0.51, 0.7), 0.2)
        >>> sv = StateVector(numpy.arange(12).reshape(3,4))

    **Arguments**
        * *data*
            Anything a numpy array can use as first argument, e.g. a
            nested tuple or another numpy array.

        * *time*
            A number giving the point of time when this state vector was
            reached. (Default is 0)

        * Any other argument that a numpy array can use.
    """
    def __new__(cls, data, time=0, norm=False, **kwargs):
        array = numpy.array(data, **kwargs)
        if norm:
            array = normalize(array)
        array = array.view(cls)
        array.time = time
        return array

    def __array_finalize__(self, obj):
        dimensions = []
        for dim in obj.shape:
            dimensions.append((0,dim-1))
        self.dimensions = tuple(dimensions)
    
    def _dim2str(self, dimensions):
        """
        Return the corresponding dimension string for the given nested tuple.
        """
        dims = []
        for d in dimensions:
            dims.append("(%s,%s)" % d)
        return " x ".join(dims)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           self._dim2str(self.dimensions))

    def norm(self):
        """
        Calculate the norm of the StateVector.
        """
        return norm(self)

    def normalize(self):
        """
        Return a normalized StateVector.
        """
        return normalize(self)

    def reduce(self, indices):
        """
        Calculate the reduced StateVector.

        **Usage**
            >>> rsv = sv.reduce(1)
            >>> rsv = sv.reduce((1,2))

        **Arguments**
            * *indices*
                An integer or a list of integers specifying over which
                subsystems should be summated.
        """
        if isinstance(indices, int):
            a = (indices,)
        else:
            a = list(set(indices))
            a.sort()
            a.reverse()
        array = self
        for i in a:
            array = array.sum(axis=i).normalize()
        return array

    def reducesquare(self, indices):
        if isinstance(indices, int):
            indices = (indices,)
        else:
            a = list(indices)
            a.sort()
        return numpy.tensordot(self, self.conjugate(), (a,a))

    def _conjugate_indices(self, indices):
        if isinstance(indices, int):
            indices = (indices,)
        return set(range(len(self.shape))).difference(indices)

    def expvalue(self, baseexpvalues, indices=None):
        if indices is not None:    
            A = self.reducesquare(self._conjugate_indices(indices))
        else:
            A = self^self.conjugate()
        return (A*baseexpvalues).sum()

    def diagexpvalue(self, baseexpvalues, indices=None):
        A = self*self.conjugate()
        if indices is not None:
            indices = list(self._conjugate_indices(indices))
            indices.sort()
            indices.reverse()
            for index in indices:
                A = A.sum(index)
        return (A*baseexpvalues).sum()

    def outer(self, other):
        """
        Return the outer product between this and the given StateVector.
        
        **Usage**
            >>> nsv = sv.outer(StateVector((1,2)))
            >>> nsv = sv.outer((1,2))
            >>> nsv = sv.outer(numpy.array((1,2)))
        """
        return StateVector(numpy.multiply.outer(self, other))

    __xor__ = outer

    def plot(self, x=None, show=True, **kwargs):
        import pylab
        dims = len(self.shape)
        if x is None:
            x = numpy.arange(self.shape[0])
        if dims == 1:
            pylab.subplot(311)
            pylab.plot(x, numpy.real(self), **kwargs)
            pylab.title("Real part")
            pylab.subplot(312)
            pylab.plot(x, numpy.imag(self), **kwargs)
            pylab.title("Imaginary part")
            pylab.subplot(313)
            pylab.plot(x, self*self.conjugate(), **kwargs)
            pylab.title("Abs square")
        elif dims == 2:
            pylab.subplot(311)
            pylab.imshow(numpy.real(self), interpolation="nearest", **kwargs)
            pylab.title("Real part")
            pylab.subplot(312)
            pylab.imshow(numpy.real(self), interpolation="nearest", **kwargs)
            pylab.title("Imaginary part")
            pylab.subplot(313)
            pylab.imshow(self*self.conjugate(), interpolation="nearest",
                         **kwargs)
            pylab.title("Abs square")
        else:
            raise TypeError("Too many dimensions to plot!")
        if show:
            pylab.show()


def norm(array):
    """
    Return the norm of the array.
    """
    return numpy.sqrt((array*array.conj()).sum())

def normalize(array):
    """
    Return a normalized array.
    """
    return array/norm(array)

def adjust(array, length):
    """
    Adjust the dimensionality of a 1D array.
    """
    import scipy.interpolate
    X_old = numpy.linspace(0,1,len(array))
    f = scipy.interpolate.interp1d(X_old, array)
    X_new = numpy.linspace(0,1,length)
    return StateVector(f(X_new))

