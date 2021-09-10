/* File: SignalProcessing.i */
/* Name our python module */
%module SignalProcessing
/* We'll be using C++ standard library strings */
%include <std_string.i>
/* Put the literal code needed at the top of the output file */
%{
#define SWIG_FILE_WITH_INIT
#include "SignalProcessing.h"
%}

/* The typemaps interface file lets us use the *OUTPUT Typemap.
This will enable us to use pointers to variables as return results.
If more than one *OUTPUT is matched, a tuple gets constructed. */
%include <typemaps.i>

/* Use the numpy interface for ndarrays. See the warning below */
%include <numpy.i>

%init %{
import_array();
%}

/* Match the arguments of our various C++ methods */
%apply (double* INPLACE_ARRAY1, int DIM1) { (double* out, size_t out_size) };
%apply (double* INPLACE_ARRAY1, int DIM1) { (double* in, size_t in_size) };


/* Parse the c++ header file and generate the output file */
%include "SignalProcessing.h"
