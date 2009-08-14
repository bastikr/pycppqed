import numpy
import expvalues
import utils

class QuantumSystem:
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
            A StateVector or StateVectorTrajectory describing this system.

        * *\*args*
            Elementary quantum systems which together build this combined
            QuantumSystem.
    """
    def __init__(self, statevector, *args):
        ndim = len(args)
        assert len(statevector.dimensions) == ndim,\
            "StateVector rank and amount of subsystems have to be equal."
        self.statevector = statevector
        self.subsystems = subsystems = [None]*ndim
        for i, arg in enumerate(args):
            if arg in SYSTEMS:
                subsystems[i] = arg(statevector, i)
            else:
                raise ValueError("Argument has to be a System class.")

    def expvalues(self, subsystems=None):
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


class Particle:
    """
    A class representing a single particle.
    """
    def __init__(self, statevector, number=0):
        self.statevector = statevector
        self.number = number

    def expvalues(self, k=True, x=True):
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
            X = numpy.linspace(-numpy.pi, numpy.pi, k_dim)
            ev = sv_x.diagexpvalue((X, X**2), indices=number, multi=True)
            ev_x = ev[0]*2*numpy.pi/k_dim
            std_x = numpy.sqrt(ev[1]*2*numpy.pi/k_dim - ev_x**2)
            evs.append(ev_x)
            titles.append("<x>")
            evs.append(std_x)
            titles.append("Std(x)")
        return expvalues.ExpectationValueCollection(evs, sv.time, titles)

    def __str__(self):
        return self.__class__.__name__


class Mode:
    """
    A class representing a single mode.
    """
    def __init__(self, statevector, number=0):
        self.statevector = statevector
        self.number = number

    def expvalues(self, n=True, a=True):
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

    def __str__(self):
        return self.__class__.__name__


SYSTEMS = (
    Particle,
    Mode,
    )

