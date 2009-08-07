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
        >>> sv = StateVector((1, 3, 7, 2), time=0.2, norm=True)
        >>> sv = StateVector(numpy.arange(12).reshape(3,4))

    **Arguments**
        * *data*
            Anything a numpy array can use, e.g. a nested tuple or another
            numpy array.

        * *time*
            A number giving the point of time when this state vector was
            reached. (Default is 0)

        * *norm*
            If set True the StateVector will be automatically normalized.
        
        * Any other argument that a numpy array can use. E.g. copy=False can
          be used so that the Statevector uses the same data as the given
          numpy array.

    Most useful is maybe the tensor product which lets you easily calculate
    state vectors for combined systems::
        
        >>> sv1 = StateVector((1,2,3), norm=True)
        >>> sv2 = StateVector((2,0,0), norm=True)
        >>> sv = sv1 ^ sv2

    The tensor product is abbrevated by the "^" operator. But be aware that
    this operator follows the built-in operator precedence - that means "+", 
    "*" etc. have **higher** precedence!
    """
    def __new__(cls, data, time=None, norm=False, **kwargs):
        array = numpy.array(data, **kwargs)
        if norm:
            array = normalize(array)
        array = numpy.asarray(array).view(cls)
        if time is not None:
            array.time = time
        elif hasattr(data, "time"):
            array.time = data.time
        return array

    def __array_finalize__(self, obj):
        self.dimensions = obj.shape
        if hasattr(obj, "time"):
            self.time = obj.time
        else:
            self.time = 0
    
    def __str__(self):
        clsname = self.__class__.__name__
        return "%s(%s)" % (clsname, " x ".join(map(str, self.dimensions)))

    def norm(self):
        """
        Calculate the norm of the StateVector.

        **Usage**
            >>> sv = StateVector((1,2,3,4,5), norm=True)
            >>> sv.norm()
            1.0
        """
        return norm(self)

    def normalize(self):
        """
        Return a normalized StateVector.

        **Usage**
            >>> sv = StateVector((1,2,1,3,1))
            >>> sv.norm()
            4.0
            >>> nsv = sv.normalize()
            >>> nsv.norm()
            1.0
        """
        return normalize(self)

    def reduce(self, indices, norm=True):
        r"""
        Return a StateVector where the given indices are reduced.

        **Usage**
            >>> rsv = sv.reduce(1)
            >>> rsv = sv.reduce((1,2))

        **Arguments**
            * *indices*
                An integer or a list of integers specifying over which
                subsystems should be summated.
            * *norm*
                If set True the resulting StateVector will be renormalized.

        Reducing means nothing else then summing up over all given indices.
        E.g. a StateVector of rank 4 can be reduced to the first two indices::

            >>> sv1 = StateVector((1,2), norm=True)
            >>> sv2 = StateVector((1,2,3), norm=True)
            >>> sv3 = StateVector((1,2,3,4), norm=True)
            >>> sv4 = StateVector((1,2,3,4,5), norm=True)
            >>> sv = sv1^sv2^sv3^sv4
            >>> print sv
            StateVector((0,1) x (0,2) x (0,3) x (0,4))
            >>> print sv.reduce((2,3))
            StateVector((0,1) x (0,2))

        This is mathematically equivalent to:

        .. math::

            \Psi_{\alpha, \beta} = \sum_{\gamma,\delta}{\Psi_{\alpha,\beta,
                                                              \gamma,\delta}}

        Reducing is an easy way to find out how subspaces of a high rank
        state vectors behave. Don't use reduced StateVectors for calculating
        expectation values - this will most likely give wrong answers!
        """
        if isinstance(indices, int):
            a = (indices,)
        else:
            a = _sorted_list(indices, True)
        array = self
        if norm:
            for i in a:
                array = array.sum(axis=i).normalize()
        else:
            for i in a:
                array = array.sum(axis=i)
        return array

    def reducesquare(self, indices):
        r"""
        Return a reduced Psi-square tensor.
        
        **Usage**
            >>> sv1 = StateVector((0,1,2,1,0), norm=True)
            >>> sv2 = StateVector((1,0,1), norm=True)
            >>> sv = sv1^sv2
            >>> sqtensor = sv.reducesquare(1)

        **Arguments**
            * *indices*
                An integer or a list of integers specifying over which
                subsystems should be summated.

        This method calculates the following quantity (simplified for rank 2
        state vectors):

        .. math::

            \sum_{\beta}{\Psi_{\alpha_1,\beta}^{*}*\Psi_{\alpha_2,\beta}}

        Where :math:`\beta` is the reduced index.

        This quantity is useful to calculate expectation values in the
        corresponding subsystems.
        """
        if isinstance(indices, int):
            a = (indices,)
        else:
            a = _sorted_list(indices)
        return numpy.tensordot(self, self.conjugate(), (a,a))

    def fft(self, axis=0):
        """
        Return a StateVector where the given axis is Fourier transformed.

        **Usage**
            >>> sv = StateVector((0,1,1.7,2,1.7,1,0), norm=True)
            >>> print sv.fft()
            StateVector((0,6))

        **Arguments**
            * *axis*
                Axis over which the fft is done. (Default is 0)
        """
        f = numpy.fft
        N = self.shape[axis]
        array = f.fftshift(f.ifft(f.ifftshift(self, axes=(axis,)), axis=axis),
                           axes=(axis,)) * N/numpy.sqrt(2*numpy.pi)
        return StateVector(array, time=self.time)

    def expvalue(self, operator, indices=None, multi=False):
        """
        Calculate the expectation value of the given operator.

        **Usage**
            >>> a = numpy.diag(numpy.ones(3), -1)
            >>> print a
            array([[ 0.,  0.,  0.,  0.],
                   [ 1.,  0.,  0.,  0.],
                   [ 0.,  1.,  0.,  0.],
                   [ 0.,  0.,  1.,  0.]])
            >>> sv = StateVector((1,2,1,2), norm=True)
            >>> print sv.expvalue(a)
            0.6

        **Arguments**
            * *operator*
                A tensor representing an arbitrary operator in the
                basis of the StateVector.

            * *indices*
                Specifies which subsystems should be taken. If None is given
                the whole system is used.

            * *multi*
                If multi is True it is assumed that a list of operators is
                given. (Default is False)

        Expectation values for combined systems are calculated in the following
        way (Assuming the operator only acts on first subsystem):

        .. math::
            
            #TODO: write mathematical expression for expectation values.
        """
        if indices is not None:    
            A = self.reducesquare(_conjugate_indices(indices, self.ndim))
        else:
            A = self^self.conjugate()
        if multi:
            return [(A*op).sum() for op in operator]
        else:
            return (A*operator).sum()

    def diagexpvalue(self, operator, indices=None, multi=False):
        """
        Calculate the expectation value for the given diagonal operator.

        **Usage**
            >>> a = numpy.arange(4)
            >>> print a
            array([ 0.,  1.,  2.,  3.])
            >>> sv = StateVector((1,2,1,4), norm=True)
            >>> print sv.diagexpvalue(a)
            2.45454545455

        **Arguments**
            * *operator*
                The diagonal elements of a tensor representing an arbitrary
                diagonal operator in the basis of the StateVector.

            * *indices*
                Specifies which subsystems should be taken. If None is given
                the whole system is used.

            * *multi*
                If multi is True it is assumed that a list of operators is
                given. (Default is False)

        
        .. math::
            
            #TODO: Write mathematical expression for diagonal expectation
                   values.
        """
        if isinstance(indices, int):
            indices = (indices,)
        A = self*self.conjugate()
        if indices is not None:
            indices = _sorted_list(_conjugate_indices(indices, self.ndim),
                                   True)
            for index in indices:
                A = A.sum(index)
        if multi:
            return [(A*op).sum() for op in operator]
        else:
            return (A*operator).sum()

    def outer(self, array):
        """
        Return the outer product between this and the given StateVector.
        
        **Usage**
            >>> sv = StateVector((0,1,2), norm=True)
            >>> print repr(sv.outer(StateVector((3,4), norm=True)))
            StateVector([[ 0.        ,  0.        ],
                   [ 0.26832816,  0.35777088],
                   [ 0.53665631,  0.71554175]])
            >>> print sv.outer((3,4)) # Not normalized!
            StateVector([[ 0.        ,  0.        ],
                   [ 1.34164079,  1.78885438],
                   [ 2.68328157,  3.57770876]])

        **Arguments**
            * *array*
                Some kind of array (E.g. StateVector, numpy.array, list, ...).

        As abreviation you can write "sv1^sv2" instead of sv1.outer(sv2). But
        be aware that the operator precedence of "^" follows the python rules -
        that means "sv1 ^ sv2 + sv3" is the same as "sv1 ^ (sv2 + sv3)"!
        """
        return StateVector(numpy.multiply.outer(self, array))

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
    """
    A class holding StateVectors for different points of time.

    Most methods are simple mapped to all single StateVectors. For more
    documentation regarding these methods look into the docstrings of the 
    corresponding StateVector methods.
    """
    def __new__(cls, data, **kwargs):
        array = numpy.array(data, **kwargs)
        array = array.view(cls)
        array.time = numpy.array([sv.time for sv in data])
        svs = [None]*array.shape[0]
        for i, entry in enumerate(array):
            svs[i] = StateVector(entry, time=array.time[i], copy=False)
        array.statevectors = svs
        return array

    def __array_finalize__(self, obj):
        self.dimensions = obj.shape[1:]

    def __str__(self):
        clsname = self.__class__.__name__
        dims = " x ".join(map(str, self.dimensions))
        return "%s(%s x (%s))" % (clsname, self.shape[0], dims)

    def map(self, func, svt=True):
        """
        Apply the given function to every single StateVector.

        **Arguments**
            * *func*
                Function that takes a StateVector as argument.

            * *svt*
                If svt is True, the return value will be an instance of
                StateVectorTrajectory.
        """
        svs = [None]*self.shape[0]
        for i, sv in enumerate(self.statevectors):
            svs[i] = func(sv)
        if svt:
            return StateVectorTrajectory(svs)
        else:
            return svs

    def norm(self):
        """
        Return a list of norms for every single StateVector.
        """
        return self.map(lambda sv:sv.norm(), False)

    def normalize(self):
        """
        Return a StateVectorTrajectory where all StateVectors are normalized.
        """
        return self.map(lambda sv:sv.normalize())

    def reduce(self, indices, norm=True):
        """
        Return a StateVectorTrajectory where all StateVectors are reduced.
        """
        return self.map(lambda sv:sv.reduce(indices, norm=norm))

    def fft(self, axis=0):
        """
        Return a StateVectorTrajectory whith Fourier transformed StateVectors.
        """
        return self.map(lambda sv:sv.fft(axis))

    def expvalue(self, operator, indices=None, multi=False, titles=None,
                 subsystems=None):
        """
        Calculate the expectation value of the operator for all StateVectors.

        Returns an ExpectationValuesTrajectory instance.
        """
        evs = self.map(lambda sv:sv.expvalue(operator, indices, multi), False)
        if not multi:
            evs = numpy.array(evs).reshape((-1,1))
        return expvalues.ExpectationValuesTrajectory(evs, self.time, titles,
                                    subsystems) 

    def diagexpvalue(self, operator, indices=None, multi=False, titles=None,
                     subsystems=None):
        """
        Calculate the expectation value of the diagonal operator for all SVs.

        Returns an ExpectationValuesTrajectory instance.
        """
        evs = self.map(lambda sv:sv.diagexpvalue(operator, indices, multi),
                       False)
        if not multi:
            evs = numpy.array(evs).reshape((-1,1))
        return expvalues.ExpectationValuesTrajectory(evs, self.time, titles,
                            subsystems)
        

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
    """
    Return all numbers from 0 to ndim which are not in indices.
    """
    if isinstance(indices, int):
        indices = (indices,)
    return set(range(ndim)).difference(indices)

def _sorted_list(iterable, reverse=False):
    """
    Transform an iterable to a sorted list.
    """
    a = list(iterable)
    a.sort()
    if reverse:
        a.reverse()
    return a
