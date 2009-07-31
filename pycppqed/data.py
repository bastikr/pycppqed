import numpy
import time
try:
    import cdata
except:
    cdata = None

class BlitzArray:
    r"""
    Class for working with ASCII representations of Blitz arrays.
    
    **Usage**
        >>> ba = BlitzArray("(0,1)x(0,1)", "[ (1,2) (3,4) \n  (5,6) (7,8) ]")

    **Arguments**
        * *data*
            Either a string of the blitz array form or nested tuple/lists/
            numpy-array.

        * *dimensions*
            Either a string of the form "(0,12) x (0,31)" or a nested
            tuple/list of the form ((0,12),(0,31))

    All values can be easily accessed::
        >>> print ba.data
        array([[ 1.+2.j,  3.+4.j],
               [ 5.+6.j,  7.+8.j]])
        >>> print ba.dimensions
        ((0, 1), (0, 1))
        >>> print ba
        BlitzArray((0,1) x (0,1))

    It's also possible to change these values, but be aware that there are
    absolutely no consistency checks! 
    """
    def __init__(self, data, dimensions):
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

    def savemat(self, path):
        """
        Save BlitzArray as Matlab file.
        """
        from scipy.io import savemat
        savemat(path, {"data": self.data})
        
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

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           self._dim2str(self.dimensions))


class StateVector(BlitzArray):
    r"""
    A class for working with state vectors generated by C++QED.

    **Usage**
        >>> dims_str = "(0,1)x(0,1)"
        >>> sv_str = "[ (1,2) (3,4) \n  (5,6) (7,8) ]"
        >>> sv = StateVector(dims_str, sv_str, 0.2)

    **Arguments**
        * *data*
            Either a string of the blitz array form or nested tuple/lists/
            numpy-array.

        * *dimensions*
            Either a string of the form "(0,12) x (0,31)" or a nested
            tuple/list of the form ((0,12),(0,31))

        * *time*
            A number giving the point of time when this state vector was
            reached.
    """
    def __init__(self, data, dimensions=None, time=0):
        if dimensions is None:
            # The dimensions can be determined from a numpy array but not
            # from a Blitz array ascii representation.
            assert isinstance(data, numpy.array)
            dimensions = []
            for dim in data.shape:
                dimensions.append((0,dim-1))
        BlitzArray.__init__(self, data, dimensions)
        self.time = time

    def saveascii(self, path, head=True):
        """
        Write the ascii representation of this StateVector to a file.

        **Usage** 
            >>> sv.saveascii("ring")

        **Arguments**
            * *path*
                A path where the output should written. If it doesn't end with
                ".sv" this suffix is appended.
        
            * *head*
                If set True a comment line of the form "# time 1" is written 
                before the ascii representation of the StateVector. (Default is 
                True)
        """
        if not path.endswith(".sv"):
            path += ".sv"
        f = open(path, "w+")
        f.write("# %s\n 1" % self.time)
        f.write(self.ascii())
        f.close()


class Info:
    """
    A class for working with the comment section of a C++QED output file.

    **Arguments**
        * *commentstr*
            A string following the style of the comment section of C++QED
            output files.
    """
    def __init__(self, commentstr):
        sections = commentstr.split("\n\n")
        self.head = sections[0]
        self.subsystems = sections[1:-1]
        self.datakey = DataKeyInfo(sections[-1])

    def __str__(self):
        return "%s\n\n%s\n\n%s" % (self.head, self.subsystems, self.datakey)


class DataKeyInfo:
    """
    A class representing the datakey section of C++QED output files.
    """
    def __init__(self, datakeystr):
        sectionstrs = datakeystr.split("\n# ")[1:]
        self.sections = sections = []
        for sectionstr in sectionstrs:
            sections.append(DataKeySectionInfo(sectionstr))

    def __str__(self):
        return "Keys:\n  " + "\n  ".join(map(str, self.sections))


class DataKeySectionInfo:
    """
    A class representing a single set of keys in the datakey section.
    """
    def __init__(self, sectionstr):
        self.name, keystr = sectionstr.split(" ", 1)
        self.content = items = {}
        pos_dot = keystr.find(".")
        pos_start = 0
        while True:
            pos_nextdot = keystr.find(".", pos_dot+1)
            if pos_nextdot == -1:
                key = int(keystr[pos_start:pos_dot])
                value = keystr[pos_dot+1:].strip()
                items[key] = value
                break
            pos_nextstart = keystr.rfind(" ", 0, pos_nextdot)
            key = int(keystr[pos_start:pos_dot])
            value = keystr[pos_dot+1:pos_nextstart].strip()
            items[key] = value
            pos_start, pos_dot = pos_nextstart, pos_nextdot
            
    def __str__(self):
        return "%s: '%s'" % (self.name, "', '".join(self.content.values()))


class Trajectory:
    """
    A class for working with the expectation values generated by C++QED.
    
    **Usage**
        >>> tr = Trajectory(traj, info)
    
    **Arguments**
        * *traj*
            A nested tuple of the following structure: The outest tuple holds
            tuples for different time steps. The next inner tuples hold tuples
            for the different parameter sets.
        * *info*
            A Info object describing the data given as parameter "traj".
    """
    def __init__(self, traj, info=None):
        if info is None:
            self.info = self._generateinfo(traj)
        else:
            self.info = info
        parts = [0]
        i = 0
        for part in traj[0]:
            i += len(part)
            parts.append(i)
        self.data = data = numpy.empty((len(traj), parts[-1]))
        for trajpos, entry in enumerate(traj):
            for entrypos, part in enumerate(entry):
                a, b = parts[entrypos:entrypos+2]
                data[trajpos][a:b] = part
        class S:
            def __init__(self, data, info):
                self.data = data
                self.info = info
            def plot(s, show=True):
                self.plot_section(s.info, show)
                
        self.sections = sections = []
        for section in self.info.datakey.sections:
            items = section.content.items()
            items.sort(lambda x,y:cmp(x[0], y[0]))
            view = self.data[:,items[0][0]-1:items[-1][0]:]
            sections.append(S(view, section))

    def _generateinfo(self, traj):
        # TODO: Implement Trajectory._generateinfo method.
        raise NotImplementedError()

    def plot(self, show=True):
        """
        Plot all sections into separate figures.

        **Usage**
            >>> tr.plot()

        **Arguments**
            *show*
                If set True pylab.show() will be called in the end and therefor
                a window containing the plot will appear automatically.
                (Default is True)
        """
        import pylab
        for i in range(1, len(self.info.datakey.sections)):
            pylab.figure(i)
            self.plot_section(i, show=False)
        if show:
            pylab.show()

    def plot_section(self, section, show=True):
        """
        Plot the given section.

        **Usage**
            >>> tr.plot_section(2)
            >>> tr.plot_section(tr.info.datakey.section[2])

        **Arguments**
            * *section*
                A number or a DataKeySectionInfo object.
        """
        import pylab
        if isinstance(section, int):
            section = self.info.datakey.sections[section]
        pylab.suptitle(section.name)
        pylab.gcf().canvas.set_window_title(section.name)
        count = len(section.content)
        i = 0
        for pos, key in section.content.items():
            i += 1
            pylab.subplot(count, 1, i)
            pylab.xlabel("time")
            pylab.ylabel(key)
            pylab.plot(self.data[:,0], self.data[:,pos-1])
        if show:
            pylab.show()


class CppqedOutputReader:
    """
    Class for working with C++QED output files.
    
    **Usage**
        >>> co = CppqedOutput("Ring.dat")
        >>> traj, svs = co.convert2python()
        >>> co.writemat("Ring")

    **Arguments**
        * *path*
            The path to a C++QED output file.

        * *read*
            If set True the file is read automatically during instantiation. 
            Otherwise it is necessary to call the "read" method separately.
            This only needs to be done explicitly if you want access the
            attributes "datastr" or "commentstr" directly. 
    """
    def __init__(self, path, read=True):
        self.path = path
        self.commentstr = None
        self.datastr = None
        if read:
            self.read()

    def read(self):
        """
        Read C++QED output file and split it into comments and data section.

        This data is stored in the attributes "commentstr" and "datastr".
        """
        # Read file into ram.
        f = open(self.path)
        buf = f.read()
        f.close()
        # Find end of comment section.
        pos = 0
        while buf[pos] in ("\n", "#"):
            pos = buf.find("\n\n", pos) + 2
        # Store comments.
        self.commentstr = buf[:pos-2]
        # Eliminate comment section from buffer.
        self.datastr = buf[pos:]

    def _parsedatastr(self, traj_handler, sv_handler):
        """
        Call appropriate handler for each state vector and trajectory entry.
        """
        buf = self.datastr
        pos = 0
        while True:
            arraypos = buf.find("\n(", pos)
            if arraypos == -1:
                map(traj_handler, buf[pos:].splitlines())
                break
            map(traj_handler, buf[pos:arraypos].splitlines())
            arrayendpos = buf.find("]", arraypos)
            assert arrayendpos != -1
            sv_handler(buf[arraypos+1:arrayendpos+1])
            pos = arrayendpos+2

    def convert2python(self, update=False):
        """
        Convert datastr into Trajectory object and list of StateVector objects.

        **Usage**
            >>> traj, svs = co.convert2python()

        **Arguments**
            *update*
                Read the C++QED output file before doing the conversion. This
                is done automatically if datastr is not yet available. (Default
                is False)
        """
        if update or self.datastr is None:
            self.read()
        traj = []
        svs = []
        def traj_handler(trajstr):
            parts = trajstr.split("\t")
            step = []
            for part in parts:
                step.append(map(float, part.split()))
            traj.append(step)
        def sv_handler(svstr):
            dimstr, datastr = svstr.split("\n", 1)
            t = traj[-1][0][0]
            svs.append(StateVector(datastr, dimstr, t))
        self._parsedatastr(traj_handler, sv_handler)
        info = Info(self.commentstr)
        return Trajectory(traj, info), svs

    def saveascii(self, path, update=False, traj=True, svs=True):
        """
        Save data from C++QED output file as ascii file(s).

        **Arguments**
            * *path*
                The path where the output should be written. For state vectors
                ".sv" is appended to this path automatically.

            * *update*
                Read the C++QED output file before doing the writing. This
                is done automatically if datastr is not yet available. (Default
                is False)

            * *traj*
                If set True the Trajectory data is written to file. (Default is
                True)

            * *svs*
                If set True all the state vectors are written to different
                files named like "path_time.sv". (Default is True)
        """
        if update or self.datastr is None:
            self.read()
        assert self.commentstr is not None
        _traj = []
        def sv_handler(svstr):
            if svs:
                tr = _traj[-1]
                t = tr[:tr.find(" ")]
                if split:
                    f = open("%s_%s.sv" % (path, t), "w")
                    f.write(svstr)
                    f.close()
        self._parsedatastr(_traj.append, sv_handler)
        if traj:
            f = open(path, "w+")
            f.write(self.commentstr)
            f.write("\n" + "\n".join(_traj))
            f.close()
       
    def savemat(self, path, update=True, traj=True, svs=True, split=False):
        """
        Save data from C++QED output file as mat file(s).
        
        **Arguments**
            * *path*
                The path where the output should be written. For state vectors
                ".sv" is appended to this path automatically and in general
                ".mat" is appended to all files.

            * *update*
                Read the C++QED output file before doing the writing. This
                is done automatically if datastr is not yet available. (Default
                is False)

            * *traj*
                If set True the Trajectory data is written to file. (Default is
                True)

            * *svs*
                If set True state vectors are written. (Default is True)

            * *split*
                If set True all state vectors are written to different files
                named like "path_time.sv.mat". (Default is False)
        """
        _traj, _svs = self.convert2python(update)
        if svs:
            if split is True:
                for sv in _svs:
                    sv.savemat("%s_%s.sv" % (path, sv.time))
            else:
                from scipy.io import savemat
                d = {}
                for sv in _svs:
                    name = "sv_%s" % sv.time
                    d[name.replace(".", "_")] = sv.data
                savemat("%s.sv" % path, d)
        if traj:
            from scipy.io import savemat
            savemat(path, {"traj":_traj.data})

