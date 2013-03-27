#include <Python.h>
#include <numpy/arrayobject.h>
#include <string.h>

static PyObject *parse(PyObject *self, PyObject *args){
    // Read in arguments: datastr, length
    char *datastr;
    int length;
    if (!PyArg_ParseTuple(args, "si", &datastr, &length)) return NULL;

    // Create Array with right dimensions, length and content.
    npy_intp dims[1];
    dims[0] = length;
    PyArrayObject *array = (PyArrayObject *)
        PyArray_SimpleNew(1, dims, PyArray_CDOUBLE);

    // Create pointer to data.
    double *data;
    data = (double*)array->data;

    // Go through the string and extract all numbers.
    strtok(datastr, "(");
    int i;
    for (i=0; i<2*length; i+=2){
        data[i] = strtod(strtok(NULL, ","), NULL);
        data[i+1] = strtod(strtok(NULL, ")"), NULL);
        strtok(NULL, "(");
        }
    return PyArray_Return(array);
    }


static PyMethodDef DataMethods[] = {
    {"parse", parse, METH_VARARGS, "Parse blitz array into numpy array."},
    {NULL, NULL, 0, NULL},
    };


PyMODINIT_FUNC initcio(void){
    Py_InitModule("cio", DataMethods);
    import_array();
    }

