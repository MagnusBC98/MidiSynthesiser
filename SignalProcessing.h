class Noise {
    public:
	void generate_noise(double* out, size_t out_size);
};

class Filter {
    public:
        float f, Fs,q;
        double alpha, x, y;
        int a1, a2;
        double b1, b2, d1, d0;
        Filter(float a, float b,float c);
	void process(double* out, size_t out_size,
		     double* in, size_t in_size);
};

