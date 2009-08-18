"""
This module provides convenient functions to visualize pycppqed objects.

Some functions are also available as methods for the specific classes:
    * :func:`statevector`
    * :func:`expvaluetrajectory`
    * :func:`expvaluecollection`

Others can be used to easily compare expecation values:
    * :func:`compare_expvaluecollections`
"""

import numpy

def statevector(sv, x=None, y=None, re=False, im=False, abs=True, show=True,
                **kwargs):
    """
    Visualize a 2d or 3d :class:`pycppqed.statevector.StateVector`.

    *Usage*
        >>> sv = pycppqed.StateVector((0.4,1,2,1,0.4), norm=True)
        >>> sv.plot()

    *Arguments*
        * *x* (optional)
            X-coordinates that should be used for plotting.

        * *y* (optional)
            Y-coordinates that should be used for plotting.

        * *re* (optional)
            If True the real part of the statevector is plotted. (Default
            is False)

        * *im* (optional)
            If True the imaginary part of the state vector is plotted.
            (Default is False)

        * *abs* (optional):
            If True the absolute square of the state vector is plotted.
            (Default is False)

        * *show* (optional):
            If True pylab.show() is called finally. This means a plotting
            window will pop up automatically. (Default is True)

        * Any other arguments that the pylab plotting command can use.
    """
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

def expvaluetrajectory(evt, show=True, **kwargs):
    """
    Visualize a :class:`pycppqed.expvalues.ExpectationValueTrajectory`.

    *Usage*
        >>> evt = pycppqed.expvalues.ExpectationValueTrajectory((1,2,1,0.4))
        >>> evt.plot()

    *Arguments*
        * *evt*
            A :class:`pycppqed.expvalues.ExpectationValueTrajectory`.

        * *show* (optional):
            If True pylab.show() is called finally. This means a plotting
            window will pop up automatically. (Default is True)

        * Any other arguments that the pylab plotting command can use.
    """
    import pylab
    pylab.plot(evt.time, evt, **kwargs)
    pylab.xlabel("time")
    pylab.ylabel(evt.title)
    if show:
        pylab.show()

def _expvalues(evs, titles=None, show=True, **kwargs):
    import pylab
    length = len(evs)
    cols = (length+3) // 4
    rows, mod = divmod(length, cols)
    if mod:
        rows += 1
    for i, ev in enumerate(evs):
        pylab.subplot(rows, cols, i+1)
        pylab.plot(ev.time, ev, **kwargs)
        pylab.xlabel("time")
        if titles:
            pylab.ylabel(titles[i])
        else:
            pylab.ylabel(ev.title)
    if show:
        pylab.show()

def expvaluecollection(evc, show=True, **kwargs):
    """
    Visualize a :class:`pycppqed.expvalues.ExpectationValueCollection`.

    *Usage*
        >>> import numpy as np
        >>> T = np.linspace(0,10)
        >>> d = (np.sin(T), np.cos(T))
        >>> titles = ("<x>", "<y>")
        >>> evc = pycppqed.expvalues.ExpectationValueCollection(d, T, titles)
        >>> evc.plot()

    *Arguments*
        * *evc*
            A :class:`pycppqed.expvalues.ExpectationValueCollection`.

        * *show* (optional):
            If True pylab.show() is called finally. This means a plotting
            window will pop up automatically. (Default is True)

        * Any other arguments that the pylab plotting command can use.
    """
    if evc.subsystems:
        import pylab
        for sysname, data in evc.subsystems.iteritems():
            pylab.figure()
            _expvalues(data.evtrajectories, show=False, **kwargs)
            if hasattr(pylab, "suptitle"): # For old versions not available.
                pylab.suptitle(sysname)
                pylab.gcf().canvas.set_window_title(sysname)
        if show:
            pylab.show()
    else:
        titles = ["(%s) %s" % (i, title) for i, title in enumerate(evc.titles)]
        _expvalues(evc.evtrajectories, titles, show=show, **kwargs)

def _compare_expvaluesubsystems(subs1, subs2, show=True):
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

def compare_expvaluecollections(coll1, coll2, show=True, **kwargs):
    """
    Plot all subsystems of two ExpectationValueCollections.
    
    *Arguments*
        * *coll1*
            First :class:`pycppqed.expvalues.ExpectationValue.Collection`.

        * *coll2*
            Second :class:`pycppqed.expvalues.ExpectationValue.Collection`.

        * *show* (optional):
            If True pylab.show() is called finally. This means a plotting
            window will pop up automatically. (Default is True)

        * Any other arguments that the pylab plotting command can use.

    This function allows a fast comparison between two sets of expectation
    values that were obtained by different calculations.
    """
    import pylab
    s1 = coll1.subsystems
    s2 = coll2.subsystems
    assert len(s1) == len(s2)
    for i in range(len(s1)):
        pylab.figure()
        _compare_expvaluesubsystems(s1.values()[i], s2.values()[i],
                                        show=False, **kwargs)
        title = "%s vs. %s" % (s1.keys()[i], s2.keys()[i])
        if hasattr(pylab, "suptitle"): # For old versions not available.
            pylab.suptitle(title)
            pylab.gcf().canvas.set_window_title(title)
    if show:
        pylab.show()

