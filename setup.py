from distutils.core import setup, Extension, Command
import unittest
import numpy as np
import sys

cio = Extension("pycppqed.cio", sources=["pycppqed/io.c"])

library_dirs_args = filter(lambda s:s.startswith('--library-dirs'), sys.argv)
if library_dirs_args:
    library_dirs = []
    for l in library_dirs_args:
        library_dirs += l.split('=')[1].split(':')
    sys.argv.remove(l)
else:
    library_dirs = None


ciobin = Extension("pycppqed.ciobin", sources=["pycppqed/iobin.cc"], libraries=['boost_serialization','blitz'], library_dirs=library_dirs, runtime_library_dirs=library_dirs)

class test(Command):
    """
    Run all available tests of pycppqed.
    """
    user_options = []
    initialize_options = lambda s:None
    finalize_options = lambda s:None
    def run(self):
        from pycppqed import test_initialconditions, test_io, test_statevector
        testsuits = {
            "initialconditions": test_initialconditions.suite(),
            "io": test_io.suite(),
            "statevector": test_statevector.suite(),
            }
        suite = unittest.TestSuite(testsuits.values())
        unittest.TextTestRunner(verbosity=2).run(suite)


ext_modules = [cio]
if '--add-iobin' in sys.argv:
    ext_modules.append(ciobin)
    sys.argv.remove('--add-iobin')


setup(
    name = "PyCppQED",
    version = "0.1.2",
    author = "Sebastian Kraemer",
    author_email = "basti.kr@gmail.com",
    url = "http://github.com/bastikr/pycppqed",
    license = "BSD",
    packages = ('pycppqed',),
    ext_modules = ext_modules,
    cmdclass = {
        "test": test,
        },
    include_dirs = [np.get_include()]
    )
