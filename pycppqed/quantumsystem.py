import numpy

class QuantumSystem:
    def __init__(self, statevector, *args):
        ndim = len(args)
        assert len(statevector.dimensions) == ndim,\
            "StateVector rank and amount of subsystems have to be equal."
        self.subsystems = subsystems = [None]*ndim
        for i, arg in enumerate(args):
            if arg in SYSTEMS:
                subsystems[i] = arg(statevector, i)
            else:
                raise ValueError("Argument has to be a System class.")

    def evs(self, subsystems=None):
        if subsystems is None:
            subsystems = range(len(self.subsystems))
        evs = [None]*len(subsystems)
        for n, s in enumerate(subsystems):
            evs[n] = self.subsystems[s].evs()
        return evs


class Particle:
    def __init__(self, statevector, number=0):
        self.statevector = statevector
        self.number = number

    def evs(self, k=True, x=True):
        number = self.number
        sv = self.statevector
        evs = {}
        k_dim = self.statevector.dimensions[number]
        if k:
            K = numpy.arange(-k_dim/2, k_dim/2)
            ev = sv.diagexpvalue((K, K**2), indices=number, multi=True)
            evs["ev_k"] = ev_k = ev.data[:,0]
            evs["var_k"] = ev.data[:,1] - ev_k**2
        if x:
            sv_x = sv.fft(number)
            X = numpy.linspace(-numpy.pi, numpy.pi, k_dim)
            ev = sv_x.diagexpvalue((X, X**2), indices=number, multi=True)
            evs["ev_x"] = ev_x = ev.data[:,0]*2*numpy.pi/k_dim
            evs["var_x"] = ev.data[:,1]*2*numpy.pi/k_dim - ev_x**2
        return evs


class Mode:
    def __init__(self, statevector, number=0):
        self.statevector = statevector
        self.number = number

    def evs(self, n=True, a=True):
        number = self.number
        sv = self.statevector
        evs = {}
        m_dim = self.statevector.dimensions[number]
        if n:
            m = numpy.arange(m_dim)
            ev = sv.diagexpvalue((m, m**2), indices=number, multi=True)
            evs["ev_n"] = ev_n = ev.data[:,0]
            evs["var_n"] = ev.data[:,1] - ev_n**2
        if a:
            m_a = numpy.diag(numpy.sqrt(numpy.arange(1, m_dim)), -1)
            evs["ev_a"] = sv.expvalue(m_a, indices=number)
        return evs

SYSTEMS = (
    Particle,
    Mode,
    )

