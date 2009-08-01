from distutils.core import setup, Extension

cio = Extension("cio", sources=["pycppqed/io.c"])

setup(
    name = "cppqed-scripts",
    version = "0.1",
    ext_modules = [cio]
    )
