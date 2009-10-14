"""
This module provides functions to read and write C++QED files.

Most important are:
    * :func:`load_cppqed`
    * :func:`load_statevector`
    * :func:`save_statevector`
    * :func:`split_cppqed`
"""
import numpy
import statevector
import expvalues
import quantumsystem
import description
import utils
try:
    import cio
except:
    print "C extension for 'io.py' is not used ..."
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
        import locale
        locale.setlocale(locale.LC_ALL, "en_US.utf8")
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
            for i in range(dim0[1] - dim0[0] + 1):
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

def _split_cppqed_output(filename, ev_handler, sv_handler):
    """
    Split a C++QED output file into expextation values and statevectors.

    *Arguments*
        * *filename*
            Path to the C++QED output file that should be parsed.

        * *ev_handler*
            A function that will be called when an expectation value row is
            found.

        * *sv_handler*
            A function that will be called when a Blitz array is found.

    *Returns*
        * *commentstr*
            A string containing the comment section of the C++QED output file.
    """
    f = open(filename)
    buf = f.read()
    f.close()
    # Find end of comment section.
    pos = 0
    while buf[pos] in ("\n", "#"):
        pos = buf.find("\n\n", pos) + 2
        assert pos != -1
    # Store comments in Info object.
    commentstr = buf[:pos-2]
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
    return commentstr

def load_cppqed(filename):
    """
    Load a C++QED output file from the given location.

    *Usage*
        >>> evs, svs = load_cppqed("ring.dat")

    *Arguments*
        * *filename*
            Path to the C++QED output file that should be loaded.

    *Returns*
        * *evs*
            A :class:`pycppqed.expvalues.ExpectationValueCollection` holding
            all expectation values.
        * *qs*
            A :class:`pycppqed.quantumsystem.QuantumSystem` holding all
            state vectors and information about the calculated system.
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
    commentstr = _split_cppqed_output(filename, ev_handler, sv_handler)
    desc = description.Description(commentstr)
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
    qs = quantumsystem.QuantumSystemCompound(svstraj, *_systems)
    return evstraj, qs

def load_statevector(filename):
    """
    Load a C++QED state vector file from the given location.

    *Usage*
        >>> sv = load_statevector("ring.sv")

    *Arguments*
        * *filename*
            Path to the C++QED state vector file that should be loaded.

    *Returns*
        * *sv*
            A :class:`pycppqed.statevector.StateVector` instance.
    """
    f = open(filename)
    buf = f.read()
    f.close()
    assert buf.startswith("# ")
    commentstr, datastr = buf.split("\n", 1)
    time = commentstr[2:commentstr.find(" ", 3)]
    ba = _blitz2numpy(datastr)
    return statevector.StateVector(ba, float(time))

def save_statevector(filename, sv):
    """
    Save a C++QED state vector to the given location.

    *Usage*
        >>> sv = StateVector((1,2,3), time=1.5)
        >>> save_statevector("my_statevector.sv", sv)

    *Arguments*
        *filename*
            Path to the location where the StateVector should be saved to.

        *sv*
            A :class:`pycppqed.statevector.StateVector` instance.
    """
    isfile = False
    f = open(filename, "w")
    f.write("# %s 1\n" % sv.time)
    f.write(_numpy2blitz(sv))
    f.close()

def split_cppqed(readpath, writepath, header=True):
    """
    Split a C++QED output file into default part and state vectors.

    *Usage*
        >>> split_cppqed("ring.dat", "r.dat")

    *Arguments*
        * *readpath*
            Path to the C++QED output file that should be split up.

        * *writepath*
            Path where the output should be saved to.

        * *header* (optional)
            If True a header line of the form ``# {time} {next_time_step}``
            is written. (Default is True)

    The standard part of the C++QED output file is saved to the given path,
    while the state vectors are saved to the same directory with the
    naming convention ``{path}_{time}.sv``.
    """
    evs = [] # Expectation values
    def sv_handler(svstr):
        if evs:
            ev = evs[-1]
            t = float(ev[:ev.find(" ")])
            f = open("%s_%06f.sv" % (writepath, t), "w")
            if header:
                f.write("# %s 1\n" % t)
            f.write(svstr)
            f.close()
    commentstr = _split_cppqed_output(readpath, evs.append, sv_handler)
    f = open(writepath, "w")
    f.write(commentstr)
    f.write("\n\n%s\n" % "\n".join(evs) )
    f.close()

