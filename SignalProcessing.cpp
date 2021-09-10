#include <iostream>
#include <cmath>
#include <algorithm>
#include "SignalProcessing.h"
//#include <array>
# define pi  3.14159265358979323846
using namespace std;

// generate_noise method takes a given numpy array, out, and generates a random 
// value for every element in said array. rand() / (RAND_MAX) scales the 
// values between 0 and 1
void Noise::generate_noise(double* out, size_t out_size){
	for(int i=0;i<out_size;i++){
		out[i] = ((double) rand() / (RAND_MAX));
	}
}


// Filter class constructor takes two arguments - sampling rate and desired 
// frequency - and from these generates values for the coefficients 
Filter::Filter(float a, float b, float c){
	f = a;
        Fs = b;
	q = c;
// the angle of the poles to the unit circle
        alpha = (2*pi*f)/Fs;	
// the x position of the poles	
        x = -(q*cos(alpha));
// the y position of the poles (note: +ve and -ve values)	
        y = (q*sin(alpha));	
// coefficients for zeros to satisfy z^2-1	
        a1 = 0;				
        a2 = 1;
// coefficients for poles to satisfy z^2 + 2xz + (x^2 + y^2)
        b1 = 2*x;
        b2 = pow(x,2) + pow(y,2);
// set delayed 'nodes' to 0 initially. That way they aren't 
// reset every time the process method is called.
	d0 = 0;
	d1 = 0;

}

// process method takes given numpy array in, does filtering maths
// and writes values out to a given numpy array out
void Filter::process(double* out, size_t out_size,
		     double* in, size_t in_size){
		for (int i=0;i<in_size;i++){
			// calculate middle 'node' from bi-quadratic diagram
			double m = in[i] - (b1*d0) - (b2*d1);
			// calculate output of filter from diagram
			out[i] = m + (a1*d0) + (a2*d1);
			// shift the delayed values along - equiv. to
			// Delay.process method
			d1 = d0;
			d0 = m;
		}
	
}

     
int main(){
    return 0;
}


