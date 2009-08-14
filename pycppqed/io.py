import numpy
import statevector
import expvalues
import quantumsystem
import description
import utils
try:
    import cio
except:
    print "C extension 'cio' is not used ..."
    cio = None

def _blitz2numpy(blitzstr):
    """
    Transform a string representation of a blitz array into a numpy array.
    """
    # Split array into dimension and data part.
    dimstr, datastr = blitzstr.split("\n", 1)
    # Parse dimension part.
    dimensions = eval("(%s,)" % dimstr.replace(" x ", ","))
    dims = []
    for d in dimensions:
        dims.append(d[1] - d[0] + 1)
    length = reduce(int.__mul__, dims)
    # Parse data part either with c-extension or with python code.
    if cio is not None:
        array = numpy.array(cio.parse(datastr, length))
    else:
        array = numpy.empty(length, dtype="complex")
        data = datastr.replace(" \n ", "").rstrip("\n")[3:-3].split(") (")
        for i, entry in enumerate(data):
            re, im = entry.split(",")
            array[i] = complex(float(re), float(im))
    return array.reshape(*dims)

def _numpy2blitz(array):
    """
    Create blitz array string representation from the given numpy array.
    """
    def data1D(array):
        # Function handling 1D arrays.
        datastr = ["(%s,%s)" % (number.real, number.imag) for number in array]
        return " ".join(datastr)
    def data2D(array):
        # Function handling 2D arrays.
        datastr = [data1D(row) for row in array]
        return " \n  ".join(datastr)
    def dataMD(array, dimensions):
        # Function handling > 2D arrays.
        dim0, otherdims = dimensions[0], dimensions[1:]
        length = len(otherdims)
        datastr = []
        if length > 2:
            for i in range(dim0[1] - dim0[0]):
                datastr.append(dataMD(array[i], otherdims))
            return " \n  ".join(datastr)
        elif length == 2:
            for i in range(dim0[1] - dim0[0] + 1):
                datastr.append(data2D(array[i]))
            return " \n  ".join(datastr)
    # Determine dimensionality of array.
    if hasattr(array, "dimensions"):
        dimensions = array.dimensions
    else:
        dimensions = array.shape
    dimensions = [(0,dim-1) for dim in array.shape]
    ndim = len(dimensions)
    if ndim == 1:
        datastr = data1D(array)
    elif ndim == 2:
        datastr = data2D(array)
    elif ndim > 2:
        datastr = dataMD(array, dimensions)
    dims = []
    for d in dimensions:
        dims.append("(%s,%s)" % d)
    dimensionstr = " x ".join(dims)
    return "%s \n[ %s ]\n\n" % (dimensionstr, datastr)

def _split_cppqed_output(path, ev_handler, sv_handler):
    f = open(path)
    buf = f.read()
    f.close()
    # Find end of comment section.
    pos = 0
    while buf[pos] in ("\n", "#"):
        pos = buf.find("\n\n", pos) + 2
    # Store comments in Info object.
    descr = buf[:pos-2]
    # Eliminate comment section from buffer.
    buf = buf[pos:]
    pos = 0
    length = len(buf)
    while pos < length:
        # Find start of next state vector.
        sv_start = buf.find("\n(", pos)
        # Handle the expectation values that were calculated before the state
        # vector.
        map(ev_handler, buf[pos:sv_start].splitlines())
        # If there is no other state vector stop searching.
        if sv_start == -1:
            break
        sv_end = buf.find("]", sv_start)
        assert sv_end != -1
        sv_handler(buf[sv_start+1:sv_end+1])
        pos = sv_end + 2
    return descr

def load_cppqed(path):
    """
    Load a C++QED output file from the given location.

    *Usage*
        >>> evs, svs = load_cppqed("ring.dat")

    *Arguments*
        * *path*
            Path to a C++QED output file.

    Returns an :class:`pycppqed.expvalues.ExpectationValueCollection` and a 
    :class:`pycppqed.statevector.StateVectorTrajectory`.
    """
    # Define handlers for state vector strings and expectation values strings.
    evs = [] # Expectation values
    svs = [] # State vectors
    def ev_handler(evstr):
        parts = evstr.split("\t")
        ev = []
        for part in parts:
            ev.extend(map(float, part.split()))
        evs.append(ev)
    def sv_handler(svstr):
        t = evs[-1][0]
        ba = _blitz2numpy(svstr)
        svs.append(statevector.StateVector(ba, t))
    descstr = _split_cppqed_output(path, ev_handler, sv_handler)
    desc = description.Description(descstr)
    titles = []
    subsystems = utils.OrderedDict()
    start = 0
    _systems = desc.quantumsystem.subsystems
    length = len(_systems)
    for i, subs in enumerate(desc.expvalues.subsystems):
        titles.extend(subs.entrys.values())
        end = len(titles)
        if 0<i<=length:
            subsystems["(%s)%s" % (i-1, _systems[i-1].__name__)] = (start, end)
        start = end

    evs = numpy.array(evs).swapaxes(0,1)
    time = evs[0,:]
    evstraj = expvalues.ExpectationValueCollection(evs, time=time,
                            titles=titles, subsystems=subsystems, copy=False)
    svstraj = statevector.StateVectorTrajectory(svs)
    qs = quantumsystem.QuantumSystem(svstraj, *_systems)
    return evstraj, qs

def load_statevector(path):
    """
    Load a C++QED state vector from the given location.

    *Usage*
        >>> sv = load_statevector("ring.sv")

    *Arguments*
        * *path*
            Path to a C++QED state vector file or a file-like object.

    Returns a StateVector instance.
    """
    if isinstance(path, basestring):
        f = open(path)
        buf = f.read()
        f.close()
    else:
        buf = path.read()
    assert buf.startswith("# ")
    commentstr, datastr = buf.split("\n", 1)
    time = commentstr[2:commentstr.find(" ", 4)]
    ba = _blitz2numpy(datastr)
    return statevector.StateVector(ba, float(time))

def save_statevector(path, sv):
    """
    Save a C++QED state vector to the given location.

    *Usage*
        >>> sv = StateVector((1,2,3), time=1.5)
        >>> save_statevector("my_statevector.sv", sv)

    *Arguments*
        *path*
            Either the path to the location where the StateVector should be
            saved to or a file.

        *sv*
            A StateVector instance.
    """
    if isinstance(path, basestring):
        isfile = False
        f = open(path, "w")
    else:
        isfile = True
        f = path
    f.write("# %s 1\n" % sv.time)
    f.write(_numpy2blitz(sv))
    if not isfile:
        f.close()

def split_cppqed(readpath, writepath):
    """
    Split a C++QED output file into default part and state vectors.

    *Usage*
        >>> split_cppqed("ring.dat", "r.dat")

    *Arguments*
        * *readpath*
            Path to a C++QED output file.

        * *writepath*
            Path where the output should be saved to.

    The standard part of the C++QED output file is saved to the given path,
    while the state vectors are saved to the same directory with the
    naming convention ``{path}_{time}.sv``.
    """
    evs = [] # Expectation values
    def sv_handler(svstr):
        if evs:
            ev = evs[-1]
            t = ev[:ev.find(" ")]
            f = open("%s_%s.sv" % (writepath, t), "w")
            f.write(svstr)
            f.close()
    descstr = _split_cppqed_output(path, evs.append, sv_handler)
    f = open(writepath, "w")
    f.write(descstr)
    f.write("\n" + "\n".join(evs))
    f.close()

