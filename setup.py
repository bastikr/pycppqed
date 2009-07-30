from distutils.core import setup, Extension

cdata = Extension("cdata", sources=["pycppqed/data.c"])

setup(
    name = "cppqed-scripts",
    version = "0.1",
    ext_modules = [cdata]
    )
