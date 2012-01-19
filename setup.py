from distutils.core import setup, Extension, Command
import unittest
import numpy as np

cio = Extension("pycppqed.cio", sources=["pycppqed/io.c"])

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


setup(
    name = "PyCppQED",
    version = "0.1.2",
    author = "Sebastian Kraemer",
    author_email = "basti.kr@gmail.com",
    url = "http://github.com/bastikr/pycppqed",
    license = "BSD",
    packages = ('pycppqed',),
    ext_modules = [cio],
    cmdclass = {
        "test": test,
        },
    include_dirs = [np.get_include()]
    )
