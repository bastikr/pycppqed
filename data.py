import numpy
import time
try:
    import cdata
except:
    cdata = None

class BlitzArray:
    """
    Class for working with ASCII representations of Blitz arrays.

    >> ba = BlitzArray("(0,1)x(0,1)", "[ (1,2) (3,4) \n  (5,6) (7,8) ]")

    A BlitzArray is defined by its dimensions, data and optionally by the
    time when it was created.
    
    * dimensions:
        Either a string of the form "(0,12) x (0,31)" or a nested tuple/list
        of the form ((0,12),(0,31))

    * data:
        Either a string of the blitz array form or nested tuple/lists/
        numpy-array.

    * time:
        Any value. (Default value is 0)


    All values can be easily accessed:

    >> print ba.time
    0

    >> print ba.dimensions
    ((0, 1), (0, 1))

    >> print ba.data
    array([[ 1.+2.j,  3.+4.j],
           [ 5.+6.j,  7.+8.j]])

    >> print ba
    BlitzArray((0,1) x (0,1))

    It's also possible to change these values, but there are absolutely no
    consistency checks!
    """
    def __init__(self, dimensions, data, time=0):
        if isinstance(dimensions, basestring):
            self.dimensions = self._str2dim(dimensions)
        elif isinstance(dimensions, (tuple, list)):
            d = []
            for entry in dimensions:
                d.append(tuple(entry))
            self.dimensions = tuple(d)
        else:
            raise ValueError("Dimension argument must be string or tuple.")
        if isinstance(data, basestring):
            self.data = self._str2data(data, self.dimensions)
        elif isinstance(data, (tuple, list, numpy.array)):
            self.data = numpy.array(data)
        else:
            raise ValueError("Data must be string, tuple, list or numpy array.")
        self.time = time

    def _str2dim(self, dimstr):
        """
        Return the corresponding nested tuple for the given dimension string.
        """
        return eval("(%s,)" % dimstr.replace(" x ", ","))

    def _dim2str(self, dimensions):
        """
        Return the corresponding dimension string for the given nested tuple.
        """
        dims = []
        for d in dimensions:
            dims.append("(%s,%s)" % d)
        return " x ".join(dims)

    def _str2data(self, datastr, dimensions):
        """
        Return the corresponding numpy array for the given parameters.
        """
        dims = []
        for d in dimensions:
            dims.append(d[1] - d[0] + 1)
        length = reduce(int.__mul__, dims)
        if cdata is not None:
            array = numpy.array(cdata.parse(datastr, length))
        else:
            array = numpy.empty(length, dtype="complex")
            data = datastr.replace(" \n ", "")[3:-3].split(") (")
            for i, entry in enumerate(data):
                re, im = entry.split(",")
                array[i] = complex(float(re), float(im))
        return array.reshape(*dims)

    def _data2str(self, data, dimensions):
        """
        Return the corresponding data string for the given parameters.
        """
        def data2D(data,):
            datastr = []
            for row in data:
                rowstr = []
                for number in row:
                    rowstr.append("(%s,%s)" % (number.real, number.imag))
                datastr.append(" ".join(rowstr))
            return " \n  ".join(datastr)
        def dataMD(data, dimensions):
            dim0, otherdims = dimensions[0], dimensions[1:]
            length = len(otherdims)
            datastr = []
            if length > 2:
                for i in range(dim0[1] - dim0[0]):
                    datastr.append(dataMD(data[i], otherdims))
                return "\n".join(datastr)
            elif length == 2:
                for i in range(dim0[1] - dim0[0]):
                    datastr.append(data2D(data[i]))
                return " \n  ".join(datastr)
            else:
                raise AssertionError("There should be 2 or more dimensions.")
        length = len(dimensions)
        if length == 2:
            datastr = data2D(data)
        elif length > 2:
            datastr = dataMD(data, dimensions)
        return "[ %s ]" % datastr

    def _save(self, func, path):
        d = {
            "data":self.data,
            #"dimensions":self.dimensions,
            #"time":self.time,
            }
        func(path, d)

    def savemat(self, path):
        """
        Save BlitzArray as Matlab file.
        """
        from scipy.io import savemat
        self._save(savemat, path)
        
    def savenpy(self, path):
        """
        Save BlitzArray as numpy file.
        """
        from scipy.io import save
        self._save(save, path)

    def saveascii(self, path):
        """
        Save Blitz array as ascii file.
        """
        f = open(path, "w")
        f.write(self.ascii())
        f.close()
        
    def ascii(self):
        """
        Return an ascii representation.
        """
        dims = self.dimensions
        data = self.data
        return "%s\n%s" % (self._dim2str(dims), self._data2str(data, dims))

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           self._dim2str(self.dimensions))

class Cppqed:
    def __init__(self):
        self.comments = None
        self.trajectory = None
        self.statevectors = None
        
    def load(self, path):
        # Read file into ram.
        f = open(path)
        buf = f.read()
        f.close()
        # Define different lists for trajectory and statevectors.
        self.trajectory = trajectory = []
        self.statevectors = arrays = []
        # Find end of comment section.
        pos = 0
        while buf[pos] in ("\n", "#"):
            pos = buf.find("\n\n", pos) + 2
        # Store comments.
        self.comments = buf[:pos].splitlines()
        # Eliminate comment section from buffer.
        buf = buf[pos:]
        print buf[:200]
        # Separate trajectory data and statevectors.
        pos = 0
        while True:
            arraypos = buf.find("\n(", pos)
            if arraypos == -1:
                trajectory.extend(buf[pos:].splitlines())
                break
            trajectory.extend(buf[pos:arraypos].splitlines())
            arrayendpos = buf.find("]", arraypos)
            assert arrayendpos != -1
            pt = trajectory[-1]
            t = float(pt[:pt.find(" ")])
            dimstr, datastr = buf[arraypos+1:arrayendpos+1].split("\n", 1)
            arrays.append(BlitzArray(dimstr, datastr, t))
            pos = arrayendpos+2

    def savetraj(self, path):
        f = open(path, "w")
        f.write("\n".join(self.comments) + "\n" + "\n".join(self.trajectory))
        f.close()

    def savesv(self, path, split=True):
        if split is True:
            for sv in self.statevectors:
                sv.saveascii("%s_%s.dat.sv" % (path, sv.time))
        else:
            f = open(path, "w+")
            for sv in self.statevectors:
                f.write(sv.ascii())
            f.close()

    def savematsv(self, path):
        for sv in self.statevectors:
            sv.savemat("%s_%s.dat.sv" % (path, sv.time))

