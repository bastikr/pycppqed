========
Tutorial
========

This document gives some basic instructions on how to use pycppqed.

.. contents::
    :depth: 3
    :backlinks: top


Introduction
============

PyCppQED is a python library that helps working with `C++QED`_ - a framework
simulating open quantum dynamics written in C++. Since C++ is not the favorite
programming language of everyone, PyCppQED extends this framework with useful
functionality:

 * Import of C++QED output files into python.
 * Export of this data as `Matlab`_ *.mat* files.
 * Fast and easy visualization of imported data.
 * Generating arbitrary initial condition vectors for C++QED. 


Installation
============

It's neither possible nor necessary to install PyCppQED. Just take care that
the base directory (where the setup.py file lives) is on your PYTHONPATH. 
Optionally there is a C extension which speeds up importing C++QED output
files. To get this extension working go to the base directory and type::

    python setup.py build

This will compile the extension file and save it to a path like
*build/lib.linux-i686-2.6/cio.so* relative to the base directory. Copy this
file into the pycppqed directory and enjoy the speed.


Usage
=====

All following commands assume that PyCppQED is already imported::

    >>> import pycppqed as qed


Split up C++QED output file into standard output and state vectors
------------------------------------------------------------------

When a C++QED script is invoked using the :option:`svdc` argument state vectors
are written into the output file between the calculated expectation values.
With PyCppQED it's easy to extract the state vectors into own files and
getting a standard C++QED output file.

Every time you want to read/write something from/as a C++QED output file you
will need the :mod:`pycppqed.io` module. It has several functions to load,
save  and convert C++QED output files. One of the of them is the
:func:`pycppqed.io.split_cppqed` function::

    >>> qed.io.split_cppqed("ring.dat", "newring.dat")

This writes the standard output file to :file:`newring` and the state vectors
into separate files named :file:`ring_time.dat.sv` where :token:`time` is
substituted by the time when this state vector was reached.


.. _import2python:

Import C++QED output file into python
-------------------------------------

Again we use the io module, but now the function 
:func:`pycppqed.io.load_cppqed`::

    >>> evs, svs = qed.io.load_cppqed_output("ring.dat")

This returns two objects which represent the whole information stored
in the C++QED output file:

 * A :class:`pycppqed.expvalues.ExpectationValueCollection` instance which
   holds all expectation values calculated by C++QED.

 * A :class:`pycppqed.statevector.StateVectorTrajectory` instance representing
   the state vector at different points of time.


Export python data as *.mat* file
---------------------------------

If you want to use `Matlab`_ or `Octave`_ for further processing of the data
you can use PyCppQED to convert a C++QED output file into a *.mat* file.
Again, we have load the file like in :ref:`import2python`. The obtained 
objects (or only parts of it, or any other array ...) can be saved with
the :meth:`scipy.io.savemat` function::

    >>> import scipy.io
    >>> scipy.io.savemat("out.mat", {"evs":evs, "svs":svs})

This file can be used from `Matlab`_ and `Octave`_:

.. code-block:: c

    >>> load("out.mat")
    >>> size(evs)
    ans = 15   175
    >>> size(svs)
    ans = 9   64   10   10
    
    
Visualization
-------------

There are some convenient shortcuts to visualize the data using 
`matplotlib`_. Assuming you imported the data as in :ref:`import2python` using
the :meth:`plot` of :obj:`traj` plots some beautiful graphs::

    >>> traj.plot()

.. image:: media/thumb_graph1.png
    :target: media/graph1.png

.. image:: media/thumb_graph2.png
    :target: media/graph2.png

.. image:: media/thumb_graph3.png
    :target: media/graph3.png


Using Trajectory and StateVector classes for further calculations
-----------------------------------------------------------------


.. _C++QED: http://sourceforge.net/projects/cppqed/
.. _Matlab: http://www.mathworks.com/
.. _Octave: http://www.gnu.org/software/octave/
.. _matplotlib: http://matplotlib.sourceforge.net/
