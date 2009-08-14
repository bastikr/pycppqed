import numpy

def statevector(sv, x=None, show=True, **kwargs):
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
        pylab.plot(x, numpy.abs(sv)**2, **kwargs)
        pylab.title("Abs square")
    elif dims == 2:
        pylab.subplot(311)
        pylab.imshow(numpy.real(sv), interpolation="nearest", **kwargs)
        pylab.title("Real part")
        pylab.subplot(312)
        pylab.imshow(numpy.real(sv), interpolation="nearest", **kwargs)
        pylab.title("Imaginary part")
        pylab.subplot(313)
        pylab.imshow(numpy.abs(sv)**2, interpolation="nearest",
                        **kwargs)
        pylab.title("Abs square")
    else:
        raise TypeError("Too many dimensions to plot!")
    if show:
        pylab.show()

def statevector_animation(svs, re=False, im=False, abs=True):
    import pylab
    from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg
    from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg
    import gtk, gobject
    ndims = len(svs.dimensions)
    length = len(svs.time)
    funcs = []
    if re:
        funcs.append(lambda i:svs[i].real)
    if im:
        funcs.append(lambda i:svs[i].imag)
    if abs:
        funcs.append(lambda i:numpy.abs(svs[i]))
    if ndims == 1:
        win = gtk.Window()
        win.connect("destroy", lambda x: gtk.main_quit())
        win.set_title("State Vector")
        win.set_default_size(400,300)
        vbox = gtk.VBox()
        win.add(vbox)
        #pylab.ion()
        fig = pylab.gcf()
        canvas = FigureCanvasGTKAgg(fig)
        vbox.pack_start(canvas)
        playbutton = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
        toolbar = NavigationToolbar2GTKAgg(canvas, win)
        vbox.pack_start(toolbar, False, False)
        toolbar.insert(gtk.SeparatorToolItem(), 8)
        toolbar.insert(playbutton, 9)
        min = svs.min()
        max = svs.max()
        max = max + 0.1*numpy.abs(max)
        axes = []
        lines = []
        for i in range(len(funcs)):
            axes.append(fig.add_subplot(len(funcs),1,i+1))
            lines.append(axes[-1].plot(funcs[i](0), animated=True)[0])
            axes[-1].set_ylim(min, max)
        canvas.draw()
        def update(*args):
            if not hasattr(update, "background"):
                update.background = canvas.copy_from_bbox(fig.bbox)
                update.cnt = 0
            canvas.restore_region(update.background)
            for i, line in enumerate(lines):
                line.set_ydata(funcs[i](update.cnt))
                axes[i].draw_artist(line)
                canvas.blit(axes[i].bbox)
            update.cnt += 1
            if update.cnt < length:
                return True
            else:
                return False
        gobject.idle_add(update)
        win.show_all()
        gtk.main()


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

