import numpy

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
    def __new__(cls, data, time=0, norm=True, **kwargs):
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

    def plot(self, show=True):
        import pylab
        dims = len(self.shape)
        if dims == 1:
            pylab.subplot(311)
            pylab.plot(numpy.real(self))
            pylab.title("Real part")
            pylab.subplot(312)
            pylab.plot(numpy.imag(self))
            pylab.title("Imaginary part")
            pylab.subplot(313)
            pylab.plot(self*self.conjugate())
            pylab.title("Abs square")
        elif dims == 2:
            pylab.subplot(311)
            pylab.imshow(numpy.real(self), interpolation="nearest")
            pylab.title("Real part")
            pylab.subplot(312)
            pylab.imshow(numpy.real(self), interpolation="nearest")
            pylab.title("Imaginary part")
            pylab.subplot(313)
            pylab.imshow(self*self.conjugate(), interpolation="nearest")
            pylab.title("Abs square")
        else:
            raise TypeError("Too many dimensions to plot!")
        if show:
            pylab.show()


def normalize(array):
    N = (array*array.conj()).sum()
    return array/numpy.sqrt(N)
