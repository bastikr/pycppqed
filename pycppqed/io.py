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
import utils
import pycppqed
import bz2
try:
    import cio
except:
    print "C extension for 'io.py' is not used ..."
    cio = None
try:
    import ciobin
except:
    print "C++ extension to support binary statevector files not available..."
    ciobin = None

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

def _parse_cppqed(filename, head_handler, ev_handler, sv_handler, basis_handler):
    """
    Split a C++QED output file into expectation values and statevectors.

    *Arguments*
        * *filename*
            Path to the C++QED output file that should be parsed.

        * *ev_handler*
            A function that will be called when an expectation value row is
            found.

        * *sv_handler*
            A function that will be called when a Blitz array is found.

        * *basis_handler*
            A function that will be called when a basis vector is found.

    *Returns*
        * *commentstr*
            A string containing the comment section of the C++QED output file.
    """
    f = _open_possibly_bz2(filename)
    buf = []

    # Iterate over data section.
    while True:
        line = f.next()
        if line.strip(" \n") and not line.startswith("#"):
            break
        buf.append(line)
    head_handler("".join(buf))
    del buf

    # Iterate over data section.
    while True:
        if not line.strip():
            pass
        elif line.startswith("# BASIS"):
            header = line
            buf = []
            while True:
                line = f.next()
                buf.append(line)
                if line.endswith(" ]\n"):
                    break
            basis_handler(header, "".join(buf))
            del buf
        elif line.startswith("#"):
            pass
        elif line.startswith("("):
            buf = [line]
            while True:
                line = f.next()
                buf.append(line)
                if line.endswith(" ]\n"):
                    break
            sv_handler("".join(buf))
        else:
            ev_handler(line)
        try:
            line = f.next()
        except StopIteration:
            break
    f.close()

def _open_possibly_bz2(filename):
    """
    Return a bz2 file object if filename ends with bz2, else return regular file object
    """
    if filename.endswith("bz2"):
        return bz2.BZ2File(filename)
    else:
        return open(filename)

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
        * *svs*
            A :class:`pycppqed.statevector.StateVectorTrajectory` holding all
            state vectors and information about the calculated system.
    """
    # Define handlers for state vector strings and expectation values strings.
    head = []
    evs = [] # Expectation values
    svs = [] # State vectors
    basis = [None] # Holds last basis vector
    def ev_handler(evstr):
        parts = evstr.split("\t")
        ev = []
        for part in parts:
            ev.extend(map(float, part.split()))
        evs.append(ev)
    def sv_handler(svstr):
        t = evs[-1][0]
        data = _blitz2numpy(svstr)
        svs.append(statevector.StateVector(data, t, basis=basis[0]))
    def basis_handler(header, svstr):
        pos1 = header.find("SYS<")+4
        pos2 = header.find(">", pos1)
        sysnumber = int(header[pos1:pos2])
        pos1 = header.find("TYPE<", pos2)+5
        pos2 = header.find(">", pos1)
        basistype = header[pos1:pos2]
        states = _blitz2numpy(svstr)
        BASES = pycppqed.BASES
        if sysnumber != -1:
            if basis[0] is None:
                basis[0] = (None, None)
            l = list(basis[0])
            if basistype in BASES:
                l[sysnumber] = BASES[basistype](states)
            else:
                states
            basis[0] = tuple(l)
        else:
            if basistype in BASES:
                basis[0] = BASES[basistype](states)
            else:
                states
    _parse_cppqed(filename, head.append, ev_handler, sv_handler, basis_handler)
    evs = numpy.array(evs).swapaxes(0,1)
    svstraj = statevector.StateVectorTrajectory(svs)
    time = evs[0,:]
    titles = []
    evstraj = expvalues.ExpectationValueCollection(evs, time=time, copy=False)
    return evstraj, svstraj

def load_statevector(filename):
    """
    Load a C++QED state vector file from the given location.

    *Usage*
        >>> sv = load_statevector("ring.sv")

    *Arguments*
        * *filename*
            Path to the C++QED state vector file that should be loaded.
            If the filename ends with .svbin, the state vector file is expected to be
            a binary file and a :class:`IOError` is raised if the required `ciobin` module is not
            available.

    *Returns*
        * *sv*
            A :class:`pycppqed.statevector.StateVector` instance.
    """
    if filename.endswith(".svbin"):
        if ciobin:
            (ba,t,_) = ciobin.parse(open(filename,'rb').read())
            return statevector.StateVector(ba,t)
        else:
            raise IOError("C++ extension to support binary statevector files not available...")
    f = _open_possibly_bz2(filename)
    buf = f.read()
    f.close()
    if buf.startswith("# "): # Syntax of old statevector files.
        commentstr, datastr = buf.split("\n", 1)
    else:
        datastr, commentstr = buf.rstrip(" \n\t").rsplit("\n", 1)
        datastr = datastr.split('#',1)[0]
        if not commentstr.startswith("# "):
            raise ValueError("Not a valid statevector file.")
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
            If the filename ends with .svbin, a binary state vector file is written
            and a :class:`IOError` is raised if the required `ciobin` module is not available.

        *sv*
            A :class:`pycppqed.statevector.StateVector` instance.
    """
    if filename.endswith(".svbin"):
        if ciobin:
            ciobin.write(filename,sv,sv.time)
            return
        else:
            raise IOError("C++ extension to support binary statevector files not available...")
    f = open(filename, "w")
    f.write(_numpy2blitz(sv))
    f.write("\n# %s 1\n" % sv.time)
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
    head = []
    evs = [] # Expectation values
    def sv_handler(svstr):
        if not evs:
            raise ValueError("Can't find timestamps in given file.")
        ev = evs[-1]
        t = float(ev[:ev.find(" ")])
        f = open("%s_%06f.sv" % (writepath, t), "w")
        if header:
            f.write("# %s 1\n" % t)
        f.write(svstr)
        f.close()

    def basis_handler(name, svstr):
        if not evs:
            raise ValueError("Can't find timestamps in given file.")
        ev = evs[-1]
        t = float(ev[:ev.find(" ")])
        f = open("%s_%06f_basis.sv" % (writepath, t), "w")
        if header:
            f.write("# %s 1\n" % t)
        f.write(svstr)
        f.close()
    _parse_cppqed(readpath, head.append, evs.append, sv_handler, basis_handler)
    f = open(writepath, "w")
    f.write("".join(head))
    f.write("\n\n%s\n" % "\n".join(evs) )
    f.close()

