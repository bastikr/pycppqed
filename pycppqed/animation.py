"""
This module implements animations with matplotlib.

The function :func:`animate_statevector` provides an easy way to animate
2D and 3D StateVectorTrajectories. This function can also be accessed through
:meth:`pycppqed.statevector.StateVectorTrajectory.animate`.
"""

import numpy
import tempfile
import os
import shutil
    
try:
    import pylab
except:
    print "matplotlib not found - plotting not possible."

try:
    import gtk
except:
    print "gtk not found - animations not possible"
    class gtk(object):
        def __getattr__(self, name):
            return object
    gtk = gtk()

try:
    import gobject
except:
    print "gobject not found - animations not possible."
    class gobject(object):
        def __getattr__(self, name):
            return lambda *args, **kwargs:None
    gobject = gobject()

try:
    from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg,\
        FigureCanvasGTKAgg
    from matplotlib.backends.backend_gtk import FileChooserDialog
except:
    print "Can't import matplotlib gtk backends - animations not possible."
    NavigationToolbar2GTKAgg = object
    FigureCanvasGTKAgg = object
    FileChooserDialog = object

try:
    from mpl_toolkits.mplot3d import axes3d, art3d
except:
    print "Can't import matplotlib 3D toolkit - 3D animations not possible."


class PlayButton(gtk.ToolButton):
    def __init__(self):
        gtk.ToolButton.__init__(self, gtk.STOCK_MEDIA_PLAY)
        self._plays = False
        self.connect("clicked", self.handle_clicked)

    def handle_clicked(self, *args):
        if self.plays():
            self.pause()
        else:
            self.play()

    def plays(self):
        return self._plays

    def play(self):
        self.set_stock_id(gtk.STOCK_MEDIA_PAUSE)
        self._plays = True
        self.emit("clicked-play")

    def pause(self):
        self.set_stock_id(gtk.STOCK_MEDIA_PLAY)
        self._plays = False
        self.emit("clicked-pause")

gobject.signal_new("clicked-play", PlayButton, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())
gobject.signal_new("clicked-pause", PlayButton, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())


class PositionScale(gtk.ToolItem):
    def __init__(self, steps):
        gtk.ToolItem.__init__(self)
        self.scale = gtk.HScale()
        self.scale.set_draw_value(False)
        self.scale.set_range(0, steps-1)
        self.scale.set_increments(1,10)
        self.add(self.scale)
        self.set_expand(True)


class AnimationToolbar(NavigationToolbar2GTKAgg):
    def __init__(self, canvas, window, steps):
        NavigationToolbar2GTKAgg.__init__(self, canvas, window)
        item = self.get_nth_item(8)
        self.remove(item)
        self.playbutton = PlayButton()
        self.positionscale = PositionScale(steps)
        self.savemoviebutton = gtk.ToolButton(gtk.STOCK_SAVE_AS)
        self.insert(gtk.SeparatorToolItem(), 8)
        self.insert(self.playbutton, 9)
        self.insert(self.savemoviebutton, 10)
        self.insert(self.positionscale, 11)
        self.savemoviebutton.connect("clicked", self.handle_save_movie)

    def handle_save_movie(self, *args):
        fname, format = FileChooserDialog(parent=self.win,
                filetypes={"avi":"avi"}, default_filetype = "avi"
                            ).get_filename_from_user()
        if fname:
            self.win.save_movie(fname, format=format)


class Canvas(FigureCanvasGTKAgg):
    def plot(self, step):
        raise NotImplementedError()

    def fast_plot(self, step):
        return self.plot(step)

    

class StateVectorCanvas(Canvas):
    def __init__(self, figure, x, data, lims):
        Canvas.__init__(self, figure)
        self.x = x
        self.data = data
        self.spcount = len(data)
        self.lims = lims

    def plot(self, step):
        self._axes = []
        self._lines = []
        for i in range(self.spcount):
            self._axes.append(self.figure.add_subplot(self.spcount, 1, i+1))
            self._lines.append(self._axes[-1].plot(self.x, self.data[i][step],
                                                   "b", animated=True)[0])
            self._axes[-1].set_ylim(self.lims[i])
        self.draw()
        self._background = self.copy_from_bbox(self.figure.bbox)
        for i in range(self.spcount):
            self._axes[i].draw_artist(self._lines[i])
            self.blit(self._axes[i].bbox)

    def fast_plot(self, step):
        self.restore_region(self._background)
        for i in range(self.spcount):
            self._lines[i].set_ydata(self.data[i][step])
            self._axes[i].draw_artist(self._lines[i])
            self.blit(self._axes[i].bbox)


class StateVectorCanvas3D(Canvas):
    def __init__(self, figure, X, Y, data, lims):
        Canvas.__init__(self, figure)
        self.X = X
        self.Y = Y
        self.data = data
        self.lims = lims
        self.ax = axes3d.Axes3D(figure)
        self._lines = ()
 
    def plot(self, step):
        for line in self._lines:
            line.remove()
        self._lines = [self.ax.plot_wireframe(self.X, self.Y,
                                    self.data[0][step], animated=True)]
        self.ax.set_zlim3d(self.lims[0])
        self.draw()
        self.ax.draw_artist(self._lines[0])
        self.blit(self.ax.bbox)

    def fast_plot(self, step):
        array = numpy.array([self.X, self.Y, self.data[0][step]])
        array1 = art3d.Line3DCollection(array.transpose((2,1,0)))
        array = numpy.array([self.X.T, self.Y.T, self.data[0][step].T])
        array2 = art3d.Line3DCollection(array.transpose((2,1,0)))
        for line in self._lines:
            line.remove()
        self._lines = (array1, array2)
        self.ax.add_collection(array1)
        self.ax.add_collection(array2)
        self.draw()


class Animation(gtk.Window):
    def __init__(self, canvas, steps):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self.step = 0
        self.steps = steps
        self._play = False
        self.canvas = canvas
        self.toolbar = AnimationToolbar(self.canvas, self, steps)
        
        self.connect("destroy", lambda x: gtk.main_quit())
        self.toolbar.playbutton.connect("clicked-play", self.handle_play)
        self.toolbar.playbutton.connect("clicked-pause", self.handle_pause)
        self.toolbar.positionscale.scale.connect("change-value", self.scroll)

        vbox = gtk.VBox()
        self.add(vbox)
        vbox.pack_start(self.canvas)
        vbox.pack_start(self.toolbar, False, False)

        width = int(self.canvas.figure.bbox.width)
        height = int(self.canvas.figure.bbox.height)
        tb_w, tb_h = self.toolbar.size_request()
        self.set_default_size(width, height + tb_h)

        self.show_all()
        self.canvas.mpl_connect("resize_event", self.handle_resize)
        self.canvas.plot(0)

    def handle_play(self, *args):
        if self.step >= self.steps-1:
            self.step = 0
        def _play():
            if self.step < self.steps-1:
                self.step += 1
                self.canvas.fast_plot(self.step)
                self.toolbar.positionscale.scale.set_value(self.step)
                return True
            self.toolbar.playbutton.pause()
            return False
        self._play = gobject.idle_add(_play)

    def handle_pause(self, *args):
        if self._play is not None:
            gobject.source_remove(self._play)
            self._play = None

    def scroll(self, range, scroll, value):
        if value < 0:
            self.step = 0
        elif value < self.steps:
            self.step = int(value)
        else:
            self.step = self.steps-1
        self.canvas.fast_plot(self.step)

    def handle_resize(self, *args):
        self.canvas.plot(self.step)
    
    def save_movie(self, filename, format="avi"):
        import subprocess
        self.step = 0
        self.canvas.plot(self.step)
        tempdirpath = tempfile.mkdtemp(prefix="pycppqed_movie_")
        w, h = self.canvas.get_width_height()
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
        while self.step < self.steps:
            self.canvas.fast_plot(self.step)
            path = os.path.join(tempdirpath, "%04d.png" % self.step)
            pixbuf.get_from_drawable(self.canvas.window, self.get_colormap(),
                                     0, 0, 0, 0, w, h)
            pixbuf.save(path, "png")
            self.step += 1

        COMMAND = ('mencoder',
                'mf://' + os.path.join(tempdirpath, "*.png"),
                '-mf',
                'type=png:w=%s:h=%s:fps=25' % (w, h), 
                #'type=png:w=%s:h=%s:fps=25' % (640, 480), 
                '-ovc',
                'lavc',
                '-lavcopts',
                #'vcodec=ffvhuff',
                #'vcodec=ffv1',
                'vcodec=mpeg4',
                #'vcodec=snow:vstrict=-2',
                '-oac',
                'copy',
                '-o',
                filename)

        subprocess.call(COMMAND)
        shutil.rmtree(tempdirpath)


def animate_statevector(svtraj, x=None, y=None, re=False, im=False, abs=True):
    """
    Create an interactive animation of the given StateVectorTrajectory.

    *Usage*
        >>> import numpy as np
        >>> X = np.linspace(-0.5, 0.5, 100)
        >>> svs = [pycppqed.gaussian(x) for x in X]
        >>> svtraj = pycppqed.StateVectorTrajectory(svs)
        >>> animate_statevector(svtraj)

    *Arguments*
        * *svtraj*
            A :class:`pycppqed.statevector.StateVectorTrajectory` that should
            be animated.

        * *x* (optional)
            An array giving the 1st-coordinates of the state vectors.

        * *y* (optional)
            An array giving the 2nd-coordinates of the state vectors.

        * *re* (optional)
            If set True the real part of the state vectors will be animated.
            (Default is False)
        
        * *im* (optional)
            If set True the imaginary part of the state vectors will be
            animated. (Default is False)
        
        * *abs* (optional)
            If set True the absolute square of the state vectors will be
            animated. (Default is True)
    """
    ndim = len(svtraj.dimensions)
    if ndim>2:
        raise ValueError("StateVectors have too many dimensions.")
    length = len(svtraj.time)
    if x is None:
        x = numpy.arange(svtraj.dimensions[0])
    titles = []
    data = []
    lims = []
    if re:
        svtraj_re = svtraj.real
        titles.append("$Re(\Psi)$")
        data.append(svtraj_re)
        lims.append((svtraj_re.min(), svtraj_re.max()))
    if im:
        svtraj_im = svtraj.imag
        titles.append("$Im(\Psi)$")
        data.append(svtraj_im)
        lims.append((svtraj_im.min(), svtraj_im.max()))
    if abs:
        svtraj_abs = numpy.abs(svtraj)**2
        titles.append("$\|\Psi\|^2$")
        data.append(svtraj_abs)
        lims.append((svtraj_abs.min(), svtraj_abs.max()))

    fig = pylab.gcf()
    fig.clear()
    if ndim == 1:
        canvas = StateVectorCanvas(fig, x, data, lims)
    elif ndim == 2:
        if y is None:
            y = numpy.arange(svtraj.dimensions[1])
        X, Y = numpy.meshgrid(y,x)
        canvas = StateVectorCanvas3D(fig, X, Y, data, lims)
    canvas = Animation(canvas, length)
    gtk.main()

