from distutils.core import setup, Extension, Command
import unittest
from pycppqed import test_initialconditions, test_io, test_statevector

cio = Extension("cio", sources=["pycppqed/io.c"])

testsuits = {
    "initialconditions": test_initialconditions.suite(),
    "io": test_io.suite(),
    "statevector": test_statevector.suite(),
    }

class test(Command):
    """
    Run all available tests of pycppqed.
    """
    user_options = []
    initialize_options = lambda s:None
    finalize_options = lambda s:None
    def run(self):
        suite = unittest.TestSuite(testsuits.values())
        unittest.TextTestRunner(verbosity=2).run(suite)


setup(
    name = "cppqed-scripts",
    version = "0.1",
    ext_modules = [cio],
    cmdclass = {
        "test": test,
        }
    )
