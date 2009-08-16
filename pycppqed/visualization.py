import numpy

def statevector(sv, x=None, y=None, re=False, im=False, abs=True, show=True,
                **kwargs):
    import pylab
    dims = len(sv.shape)
    if dims>2:
        raise ValueError("StateVector has too many dimensions.")
    indices = numpy.array(map(bool, (re, im, abs)))
    titles = numpy.array(("$Re(\Psi)$", "$Im(\Psi)$", "$\|\Psi\|^2$"))[indices]
    funcs = numpy.array((lambda x:x.real, lambda x:x.imag,
                         lambda x:numpy.abs(x)**2))[indices]
    length = len(funcs)
    if x is None:
        x = numpy.arange(sv.shape[0])
    if dims == 1:
        for i, title in enumerate(titles):
            pylab.subplot(length, 1, i+1)
            pylab.plot(x, funcs[i](sv), **kwargs)
            pylab.title(title)
    elif dims == 2:
        if y is None:
            y = numpy.arange(sv.shape[1])
        X, Y = numpy.meshgrid(y,x)
        from mpl_toolkits.mplot3d import axes3d
        
        ax = axes3d.Axes3D(pylab.gcf())
        for i, title in enumerate(titles):
            #pylab.subplot(length, 1, i+1)
            ax.plot_wireframe(X, Y, funcs[i](sv), **kwargs)
            pylab.title(title)
            break
    if show:
        pylab.show()

def expvaluetraj(evs, show=True):
    import pylab
    pylab.plot(evs.time, evs)
    pylab.xlabel("time")
    pylab.ylabel(evs.title)
    if show:
        pylab.show()

def expvalues(evs, titles=None, show=True):
    import pylab
    length = len(evs)
    cols = (length+3) // 4
    rows, mod = divmod(length, cols)
    if mod:
        rows += 1
    for i, ev in enumerate(evs):
        pylab.subplot(rows, cols, i+1)
        pylab.plot(ev.time, ev)
        pylab.xlabel("time")
        if titles:
            pylab.ylabel(titles[i])
        else:
            pylab.ylabel(ev.title)
    if show:
        pylab.show()

def expvaluecollection(evc, show=True):
    if evc.subsystems:
        import pylab
        for sysname, data in evc.subsystems.iteritems():
            pylab.figure()
            expvalues(data.evtrajectories, show=False)
            if hasattr(pylab, "suptitle"): # For old versions not available.
                pylab.suptitle(sysname)
                pylab.gcf().canvas.set_window_title(sysname)
        if show:
            pylab.show()
    else:
        titles = ["(%s) %s" % (i, title) for i, title in enumerate(evc.titles)]
        expvalues(evc.evtrajectories, titles, show=show)

def compare_expvaluetraj(*args, **kwargs):
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

def compare_expvaluesubsystem(subs1, subs2, show=True):
    import pylab
    t1 = subs1.evtrajectories
    t2 = subs2.evtrajectories
    length = len(t1)
    assert length == len(t2)
    for i in range(length):
        pylab.subplot(length, 1, i+1)
        pylab.plot(t1[i].time, t1[i], t2[i].time, t2[i], "o")
        pylab.xlabel("time")
        pylab.ylabel(t2[i].title)

def compare_expvaluecollections(coll1, coll2, show=True):
    import pylab
    s1 = coll1.subsystems
    s2 = coll2.subsystems
    assert len(s1) == len(s2)
    for i in range(len(s1)):
        pylab.figure()
        compare_expvaluesubsystem(s1.values()[i], s2.values()[i],
                                        show=False)
        title = "%s vs. %s" % (s1.keys()[i], s2.keys()[i])
        if hasattr(pylab, "suptitle"): # For old versions not available.
            pylab.suptitle(title)
            pylab.gcf().canvas.set_window_title(title)
    if show:
        pylab.show()

