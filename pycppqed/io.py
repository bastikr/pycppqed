import os
import numpy
import statevector
import expvalues
import description
try:
    import cio
except:
    raise
    print "C extension 'cio' is not used ..."
    cio = None

def _blitz2numpy(blitzstr):
    """
    Return the corresponding numpy array for the given parameters.
    """
    dimstr, datastr = blitzstr.split("\n", 1)
    dimensions = eval("(%s,)" % dimstr.replace(" x ", ","))
    dims = []
    for d in dimensions:
        dims.append(d[1] - d[0] + 1)
    length = reduce(int.__mul__, dims)
    if cio is not None:
        array = numpy.array(cio.parse(datastr, length))
    else:
        array = numpy.empty(length, dtype="complex")
        data = datastr.replace(" \n ", "")[3:-3].split(") (")
        for i, entry in enumerate(data):
            re, im = entry.split(",")
            array[i] = complex(float(re), float(im))
    return array.reshape(*dims)

def _numpy2blitz(array):
    """
    Return the corresponding data string for the given parameters.
    """
    def data2D(array):
        datastr = []
        for row in array:
            rowstr = []
            for number in row:
                rowstr.append("(%s,%s)" % (number.real, number.imag))
            datastr.append(" ".join(rowstr))
        return " \n  ".join(datastr)
    def dataMD(array, dimensions):
        dim0, otherdims = dimensions[0], dimensions[1:]
        length = len(otherdims)
        datastr = []
        if length > 2:
            for i in range(dim0[1] - dim0[0]):
                datastr.append(dataMD(array[i], otherdims))
            return "\n".join(datastr)
        elif length == 2:
            for i in range(dim0[1] - dim0[0] + 1):
                datastr.append(data2D(array[i]))
            return " \n  ".join(datastr)
        else:
            raise AssertionError("There should be 2 or more dimensions.")
    if hasattr(array, "dimensions"):
        dimensions = array.dimensions
    else:
        dimensions = []
        for dim in array.shape:
            dimensions.append((0,dim-1))
    length = len(dimensions)
    if length == 2:
        datastr = data2D(array)
    elif length > 2:
        datastr = dataMD(array, dimensions)
    dims = []
    for d in dimensions:
        dims.append("(%s,%s)" % d)
    dimensionstr = " x ".join(dims)
    return "%s \n[ %s ]" % (dimensionstr, datastr)

def load_cppqed_output(path):
    f = open(path)
    buf = f.read()
    f.close()
    # Find end of comment section.
    pos = 0
    while buf[pos] in ("\n", "#"):
        pos = buf.find("\n\n", pos) + 2
    # Store comments in Info object.
    desc = description.Description(buf[:pos-2])
    # Eliminate comment section from buffer.
    buf = buf[pos:]
    # Define handlers for state vector strings and expectation values strings.
    evs = [] # Expectation values
    svs = [] # State vectors
    def ev_handler(evstr):
        parts = evstr.split("\t")
        ev = []
        for part in parts:
            ev.append(map(float, part.split()))
        evs.append(ev)
    def sv_handler(svstr):
        t = evs[-1][0][0]
        ba = _blitz2numpy(svstr)
        svs.append(statevector.StateVector(ba, t))
    # Go through the datasection and extract state vectors and expectation values.
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
    traj = expvalues.Trajectory(evs, desc)
    return traj, svs

def save_cppqed_output(path):
    raise NotImplementedError()

def load_cppqed_sv(path):
    f = open(path)
    buf = f.read()
    f.close()
    assert buf.startswith("# ")
    commentstr, datastr = buf.split("\n", 1)
    time = commentstr[2:commentstr.find(" ", 4)]
    ba = _blitz2numpy(datastr)
    return StateVector(ba, float(time))

def save_cppqed_sv(path, sv):
    f = open(path, "w")
    f.write("# %s 1\n" % sv.time)
    f.write(_numpy2blitz(sv))
    f.close()

def load_mat_exptraj(path):
    raise NotImplementedError()

def save_mat_exptraj(path):
    raise NotImplementedError()

def load_mat_svtraj(path):
    raise NotImplementedError()

def save_mat_svtraj(path):
    raise NotImplementedError()

def load_mat_sv(path):
    from scipy.io import loadmat
    return loadmat(path)

def save_mat_sv(path, sv):
    from scipy.io import savemat
    savemat(path, {"sv": sv})

def load_pycppqed(path):
    raise NotImplementedError()

def save_pycppqed(path):
    raise NotImplementedError()

