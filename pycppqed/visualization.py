import numpy

def plot_statevector(sv, x=None, show=True, **kwargs):
    import pylab
    dims = len(sv.shape)
    if x is None:
        x = numpy.arange(sv.shape[0])
    if dims == 1:
        pylab.subplot(311)
        pylab.plot(x, numpy.real(sv), **kwargs)
        pylab.title("Real part")
        pylab.subplot(312)
        pylab.plot(x, numpy.imag(sv), **kwargs)
        pylab.title("Imaginary part")
        pylab.subplot(313)
        pylab.plot(x, sv*sv.conjugate(), **kwargs)
        pylab.title("Abs square")
    elif dims == 2:
        pylab.subplot(311)
        pylab.imshow(numpy.real(sv), interpolation="nearest", **kwargs)
        pylab.title("Real part")
        pylab.subplot(312)
        pylab.imshow(numpy.real(sv), interpolation="nearest", **kwargs)
        pylab.title("Imaginary part")
        pylab.subplot(313)
        pylab.imshow(sv*sv.conjugate(), interpolation="nearest",
                        **kwargs)
        pylab.title("Abs square")
    else:
        raise TypeError("Too many dimensions to plot!")
    if show:
        pylab.show()

def plot_expvalues(time, evs, titles, show=True):
    import pylab
    length = len(evs)
    cols = length // 4 + 1
    rows = length // cols + 1
    for i, ev in enumerate(evs):
        pylab.subplot(rows, cols, i+1)
        pylab.plot(time, ev)
        pylab.xlabel("time")
        pylab.ylabel(titles[i])
    if show:
        pylab.show()

def plot_expvaluecollection(evc, show=True):
    if evc.subsystems:
        import pylab
        i = 0
        for sysname, data in evc.subsystems.iteritems():
            i += 1
            pylab.figure(i)
            plot_expvalues(evc.time, data.evtrajectories, data.titles, show=False)
            if hasattr(pylab, "suptitle"): # For old versions not available.
                pylab.suptitle(sysname)
                pylab.gcf().canvas.set_window_title(sysname)
        if show:
            pylab.show()
    else:
        titles = ["(%s) %s" % (i, title) for i, title in enumerate(evc.titles)]
        plot_expvalues(evc.time, evc.evtrajectories, titles, show=show)

def plot_compare_evs(*args, **kwargs):
    import pylab
    show = kwargs.pop("show", True)
    evs = []
    for arg in args:
        if isinstance(arg, basestring):
            evs[-1].append(arg)
        else:
            evs.append([arg.time, arg])
    for ev in evs:
        pylab.plot(*ev)
    pylab.ylabel(args[0].title)
    pylab.xlabel("time")
    if show:
        pylab.show()

