#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>
#include <blitz/array.h>
#include <blitz/tinyvec2.h>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/archive/binary_oarchive.hpp>
#include <boost/serialization/complex.hpp>
#include <boost/preprocessor/iteration/local.hpp>
#include <sstream>
#include <fstream>
#include <string>
#include <iostream>

#define MAX_RANK 11

typedef std::complex<double> dcomp;

using namespace blitz;

template<int RANK>
PyObject *doParse(boost::archive::binary_iarchive &ia) {
  npy_intp dims[RANK];
  Array<dcomp,RANK> a;
  double t,dtTry;
  for (int i=0;i<RANK;i++) { int d; ia>>d; dims[i]=d; }
  ia >> a;
  ia >> t >> dtTry;
  dcomp *data = a.dataFirst();
  PyObject *wrapNumpy = PyArray_SimpleNewFromData(RANK, dims, NPY_CDOUBLE,data);
  PyArrayObject *array = (PyArrayObject *) PyArray_FromAny(wrapNumpy,NULL,0,0,NPY_ARRAY_ENSURECOPY,NULL);
  return Py_BuildValue("(Odd)", PyArray_Return(array), t, dtTry);
}

static PyObject *parse(PyObject *self, PyObject *args){
    // Read in arguments: datastr, length
    char *datastr;
    int size;
    double t,dtTry;
    if (!PyArg_ParseTuple(args, "s#", &datastr, &size)) return NULL;
    int rank;
    std::stringstream datastream(std::string(datastr, size));
    boost::archive::binary_iarchive ia(datastream);
    ia >> rank;
    if (rank>MAX_RANK) {
        std::cerr << "Rank > " << MAX_RANK << " not supported." << std::endl;
        return NULL;
    }

    switch (rank) {
        #define BOOST_PP_LOCAL_MACRO(n) \
          case n: return doParse<n>(ia); break;
        #define BOOST_PP_LOCAL_LIMITS (1, MAX_RANK)
        #include BOOST_PP_LOCAL_ITERATE()
    }
}

template<int RANK>
void doWrite(boost::archive::binary_oarchive &oa, PyArrayObject *array_c, const double time) {
  npy_intp *dims=PyArray_DIMS(array_c);
  TinyVector<int,RANK> shape;
  for (int i=0; i<RANK; i++) {
    int d=dims[i];
    oa << d;
    shape[i]=d;
  }
  Array<dcomp,RANK>  a = Array<dcomp,RANK>(static_cast<dcomp *>(PyArray_DATA(array_c)), shape, duplicateData);
  const double dtTry=1;
  oa << a << time << dtTry;
}

static PyObject *write(PyObject *self, PyObject *args){
  char *filename;
  PyObject *array;
  double time;
  if (!PyArg_ParseTuple(args, "sO!d", &filename, &PyArray_Type, &array, &time)) return NULL;
  PyArrayObject *array_c = (PyArrayObject *) PyArray_FromAny(array, PyArray_DescrFromType(NPY_CDOUBLE),0,0,NPY_ARRAY_CARRAY_RO,NULL);
  std::ofstream ofs(filename,ios_base::out|ios_base::binary|ios_base::trunc);
  boost::archive::binary_oarchive oa(ofs);
  int r=PyArray_NDIM(array_c);
  if (r>MAX_RANK) {
    std::cerr << "Rank > " << MAX_RANK << " not supported." << std::endl;
    return NULL;
  }
  oa << r;

  switch (r) {
    #define BOOST_PP_LOCAL_MACRO(n)               \
      case n: doWrite<n>(oa,array_c,time); break;
    #define BOOST_PP_LOCAL_LIMITS (1, MAX_RANK)
    #include BOOST_PP_LOCAL_ITERATE()
  }
  Py_RETURN_TRUE;
}

static PyMethodDef DataMethods[] = {
    {"parse", parse, METH_VARARGS, "Parse binary blitz array into numpy array."},
    {"write", write, METH_VARARGS, "Write numpy array into binary file usable as C++QED initial file."},
    {NULL, NULL, 0, NULL},
    };


PyMODINIT_FUNC initciobin(void){
    Py_InitModule("ciobin", DataMethods);
    import_array();
    }

