import numpy
import expvalues
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
    
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, _dim2str(self.dimensions))

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
            a = _sorted_list(indices)
        return numpy.tensordot(self, self.conjugate(), (a,a))

    def expvalue(self, baseexpvalues, indices=None):
        if indices is not None:    
            A = self.reducesquare(_conjugate_indices(indices, self.ndim))
        else:
            A = self^self.conjugate()
        return [(A*exp).sum() for exp in baseexpvalues]

    def diagexpvalue(self, baseexpvalues, indices=None):
        A = self*self.conjugate()
        if indices is not None:
            indices = _sorted_list(_conjugate_indices(indices, self.ndim),
                                   True)
            for index in indices:
                A = A.sum(index)
        return [(A*exp).sum() for exp in baseexpvalues]

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


class StateVectorTrajectory(numpy.ndarray):
    def __new__(cls, data, **kwargs):
        array = numpy.array(data, **kwargs)
        array = array.view(cls)
        array.time = numpy.array([sv.time for sv in data])
        svs = [None]*array.shape[0]
        for i, entry in enumerate(array):
            svs[i] = StateVector(entry, copy=False)
        array.statevectors = svs
        return array

    def __array_finalize__(self, obj):
        dimensions = []
        for dim in obj.shape[1:]:
            dimensions.append((0,dim-1))
        self.dimensions = tuple(dimensions)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, _dim2str(self.dimensions))

    def expvalue(self, baseexpvalues, indices=None, titles=None,
                       subsystems=None):
        evs = [None]*self.shape[0]
        for i, sv in enumerate(self.statevectors):
            evs[i] = sv.expvalue(baseexpvalues, indices)
        evstraj = expvalues.ExpectationValuesTrajectory(evs, self.time, titles,
                                    subsystems) 
        return evstraj

    def diagexpvalue(self, baseexpvalues, indices=None, titles=None,
                           subsystems=None):
        evs = [None]*self.shape[0]
        for i, sv in enumerate(self.statevectors):
            evs[i] = sv.diagexpvalue(baseexpvalues, indices)
        evstraj = expvalues.ExpectationValuesTrajectory(evs, self.time, titles,
                            subsystems)
        return evstraj
        

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

def _dim2str(dimensions):
    """
    Return the corresponding dimension string for the given nested tuple.
    """
    dims = []
    for d in dimensions:
        dims.append("(%s,%s)" % d)
    return " x ".join(dims)

def _conjugate_indices(indices, ndim):
    if isinstance(indices, int):
        indices = (indices,)
    return set(range(ndim)).difference(indices)

def _sorted_list(iterable, reverse=False):
    a = list(iterable)
    a.sort()
    if reverse:
        a.reverse()
    return a
