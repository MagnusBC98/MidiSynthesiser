# MidiSynthesiser
4th year Audio Programming and Signal Processing Final Assignment

This is a MIDI-controllable synthesiser written in software and with a GUI written in Qt. Signal processing code written in C++ is used to filter white noise to produce the default tone, however saw and sinetooth tones are also available. Since the filtering code is implemented in C++, it is able to be carried out in real time by being called in the wider Python application using the Simple Wrapper Interface Generator (SWIG). The Q dial changes the quality factor of filtering for the white noise, while the detune dial acts as a sort of pitch bend wheel.
