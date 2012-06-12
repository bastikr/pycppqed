#include <Python.h>
#include <numpy/arrayobject.h>
#include <blitz/array.h>
#include <blitz/tinyvec2.h>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/serialization/complex.hpp>
#include <boost/preprocessor/iteration/local.hpp>
#include <sstream>
#include <string>
#include <iostream>

#define MAX_RANK 11

typedef std::complex<double> dcomp;

using namespace blitz;

static PyObject *parse(PyObject *self, PyObject *args){
    // Read in arguments: datastr, length
    char *datastr;
    int size,d;
    double t,dtTry;
    if (!PyArg_ParseTuple(args, "s#", &datastr, &size)) return NULL;
    
    std::complex<double> *data;
    int rank=1;
    npy_intp *dims;
    std::stringstream datastream(std::string(datastr, size));

    #define BOOST_PP_LOCAL_MACRO(n) Array<dcomp,n> a##n;
    #define BOOST_PP_LOCAL_LIMITS (1, MAX_RANK)
    #include BOOST_PP_LOCAL_ITERATE()

    boost::archive::binary_iarchive ia(datastream);
    ia >> rank;
    if (rank>MAX_RANK) {
        std::cerr << "Rank > " << MAX_RANK << " not supported." << std::endl;
        return NULL;
    }
    dims = new npy_intp[rank];
    for (int i=0;i<rank;i++) { ia>>d; dims[i]=d; }
    switch (rank) {
        #define BOOST_PP_LOCAL_MACRO(n) \
          case n: ia >> a##n; data = a##n.dataFirst(); break; \
        /**/
        #define BOOST_PP_LOCAL_LIMITS (1, MAX_RANK)
        #include BOOST_PP_LOCAL_ITERATE()
    }
    ia>>t>>dtTry;
    PyObject *wrapNumpy = PyArray_SimpleNewFromData(rank, dims, PyArray_CDOUBLE,data);
    PyArrayObject *array = (PyArrayObject *) PyArray_FromAny(wrapNumpy,NULL,0,0,NPY_ENSURECOPY,NULL);
    delete[] dims;
    return Py_BuildValue("(Odd)", PyArray_Return(array), t, dtTry);
    }


static PyMethodDef DataMethods[] = {
    {"parse", parse, METH_VARARGS, "Parse binary blitz array into numpy array."},
    {NULL, NULL, 0, NULL},
    };


PyMODINIT_FUNC initciobin(void){
    Py_InitModule("ciobin", DataMethods);
    import_array();
    }

