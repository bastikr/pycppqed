"""
This module provides classes to represent quantum systems calculated by C++QED.

Following components are implemented:
    * :class:`Particle`
    * :class:`Mode`

Components can be combined to new systems in the class
:class:`QuantumSystemCombound`.

All classes in this module inherit from :class:`QuantumSystem`.

# TODO: Improve quantumsystem.py
"""
import numpy
import expvalues
import utils

class QuantumSystem:
    """
    A base class for all other specific quantum system.
    """
    def __init__(self, statevector, number=0):
        self.statevector = statevector
        self.number = number

    def __str__(self):
        clsname = self.__class__.__name__
        dims = self.statevector.dimensions[self.number]
        return "%s(%s)" % (clsname, dims)

    def expvalues(self):
        """
        Calculate the default expectation values for this system.

        This method has to be overridden in all inheriting classes.
        """
        raise NotImplementedError


class QuantumSystemCompound(QuantumSystem):
    """
    A class representing a combined quantum system.

    *Usage*
        >>> sv1 = StateVector((1,2,1), norm=True)
        >>> sv2 = StateVector((4,2,1,0,0), norm = True)
        >>> sv = sv1 ^ sv2
        >>> qs = QuantumSystem(sv, Particle, Mode)
        >>> evs = qs.evs()
        >>> print evs[0]
        ExpectationValueCollection('<k>', 'Var(k)', '<x>', 'Var(x)')
        >>> print repr(evs[1])
        ExpectationValueCollection('<n>', 'Var(n)', '<a>')

    *Arguments*
        * *statevector*
            A :class:`pycppqed.statevector.StateVector` or 
            :class:`pycppqed.statevector.StateVectorTrajectory` describing
            this system.

        * *\*args*
            Elementary quantum systems which together build this combined
            quantum system.
    """
    def __init__(self, statevector, *args):
        ndim = len(args)
        # This assertion is not good if there is an empty StateVector.
        #assert len(statevector.dimensions) == ndim,\
        #    "StateVector rank and amount of subsystems have to be equal."
        self.statevector = statevector
        self.subsystems = subsystems = [None]*ndim
        for i, arg in enumerate(args):
            if arg in SYSTEMS:
                subsystems[i] = arg(statevector, i)
            else:
                raise ValueError("Argument has to be a System class.")

    def expvalues(self, subsystems=None):
        """
        Calculate the default expectation values for this system.

        *Arguments*
            * *subsystems* (optional)
                A list of integers specifying for which subsystems the 
                expectation values should be calculated.
                (Default is None which means all subsystems are calculated).

        *Returns*
            * *expvalues*
                An :class:`pycppqed.expvalues.ExpectationValuesCollection`.
        """
        if subsystems is None:
            subsystems = range(len(self.subsystems))
        evs = []
        titles = []
        subsys = utils.OrderedDict()
        pos_start = 0
        for n, s in enumerate(subsystems):
            sub = self.subsystems[s]
            ev = sub.expvalues()
            evs.extend(ev.evtrajectories)
            pos_end = len(evs)
            titles.extend(ev.titles)
            subsys["(%s)%s" % (n, sub.__class__.__name__)] = (pos_start,pos_end)
            pos_start = pos_end
        return expvalues.ExpectationValueCollection(evs, evs[0].time, titles,
                                                    subsys)

    def __str__(self):
        clsname = self.__class__.__name__
        return "%s(%s)" % (clsname, ", ".join(map(str, self.subsystems)))


class Particle(QuantumSystem):
    """
    A class representing a single particle.
    """
    def expvalues(self, k=True, x=True):
        r"""
        Calculate the default expectation values for this particle.

        *Arguments*
            * *k* (optional)
                If True all k related expectation values are calculated. That
                means :math:`\langle k \rangle` and :math:`Var(k)`.
                (Default is True)

            * *x* (optional)
                If True all x related expectation values are calculated. That
                means :math:`\langle x \rangle` and :math:`\Delta x`.
                (Default is True)

        *Returns*
            * *expvalues*
                A :class:`pycppqed.expvalues.ExpectationValuesCollection`.
        """
        number = self.number
        sv = self.statevector
        evs = []
        titles = []
        k_dim = self.statevector.dimensions[number]
        if k:
            K = numpy.arange(-k_dim/2, k_dim/2)
            ev = sv.diagexpvalue((K, K**2), indices=number, multi=True)
            ev_k = ev[0]
            var_k = ev[1] - ev_k**2
            evs.append(ev_k)
            titles.append("<k>")
            evs.append(var_k)
            titles.append("Var(k)")
        if x:
            sv_x = sv.fft(number)
            X = numpy.linspace(-numpy.pi, numpy.pi, k_dim, endpoint=False)
            ev = sv_x.diagexpvalue((X, X**2), indices=number, multi=True)
            ev_x = ev[0]*2*numpy.pi/k_dim
            std_x = numpy.sqrt(ev[1]*2*numpy.pi/k_dim - ev_x**2)
            evs.append(ev_x)
            titles.append("<x>")
            evs.append(std_x)
            titles.append("Std(x)")
        return expvalues.ExpectationValueCollection(evs, sv.time, titles)


class Mode(QuantumSystem):
    """
    A class representing a single mode.
    """
    def expvalues(self, n=True, a=True):
        r"""
        Calculate the default expectation values for this particle.

        *Arguments*
            * *n* (optional)
                If True all n related expectation values are calculated. That
                means :math:`\langle n \rangle` and :math:`Var(n)`.
                (Default is True)

            * *a* (optional)
                If True all a related expectation values are calculated. That
                means :math:`Re(\langle a \rangle)` and
                :math:`Im(\langle a \rangle)`. (Default is True)

        *Returns*
            * *expvalues*
                A :class:`pycppqed.expvalues.ExpectationValuesCollection`.
        """
        number = self.number
        sv = self.statevector
        evs = []
        titles = []
        m_dim = self.statevector.dimensions[number]
        if n:
            m = numpy.arange(m_dim)
            ev = sv.diagexpvalue((m, m**2), indices=number, multi=True)
            ev_n = ev[0]
            var_n = ev[1] - ev_n**2
            evs.append(ev_n)
            titles.append("<n>")
            evs.append(var_n)
            titles.append("Var(n)")
        if a:
            m_a = numpy.diag(numpy.sqrt(numpy.arange(1, m_dim)), -1)
            ev_a = sv.expvalue(m_a, indices=number)
            evs.append(ev_a.real)
            titles.append("Re(<a>)")
            evs.append(ev_a.imag)
            titles.append("Im(<a>)")
        return expvalues.ExpectationValueCollection(evs, sv.time, titles)


SYSTEMS = (
    Particle,
    Mode,
    )

