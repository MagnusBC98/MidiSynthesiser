# Import various Python libraries as well as Qt classes
import sys
import numpy as np
import mido
from scipy import signal
from SignalProcessing import Noise, Filter

from PyQt5.QtCore import Qt, pyqtSlot, QByteArray, QIODevice, QObject, pyqtSignal, QThread
from PyQt5.QtMultimedia import QAudioFormat, QAudioOutput
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSlider, QPushButton, \
    QMessageBox, QVBoxLayout, QHBoxLayout, QLCDNumber, QDial
from PyQt5.QtGui import QFont, QFontDatabase


# Define constants for audio synthesis and
# noise object
SAMPLE_RATE = 32000
AUDIO_CHANS = 1
SAMPLE_SIZE = 16
CTRL_INTERVAL = 100  # milliseconds of audio
n = Noise()


################### Class for reading MIDI input #####################


class MidiPortReader(QObject):

    # create a signal for when a new midi note is played
    newNoteFrequency = pyqtSignal(float)

    def __init__(self):
        QObject.__init__(self)

    def listener(self):

        # with loop waits for MIDI signals which
        # are routed to virtual port 'pipes'
        with mido.open_input(
                'pipes',
                virtual=True
        ) as mip:

            for mmsg in mip:
                # when a new note is played, frequency
                # of note is calculated and passed out
                # through the Qt signal emit command
                if mmsg.type == "note_on":
                    f = 2**((mmsg.note-69)/12)*440
                    self.newNoteFrequency.emit(f)


##################### End of MIDI reader class #######################


######### Class for generating filtered noise in real-time ###########


class FiltGenerator(QIODevice):

    # max no. of samples generated
    # per request. Giving this a slightly higher
    # value seemed to reduce clicking noises.
    SAMPLES_PER_READ = 3000

    def __init__(self, format,  parent=None):

        QIODevice.__init__(self, parent)
        self.data = QByteArray()
        self.phase = 0

        # perform checks to see if format
        # is valid
        if format.isValid() and \
                format.sampleSize() == 16 and \
                format.byteOrder() == \
        QAudioFormat.LittleEndian and \
                format.sampleType() == \
        QAudioFormat.SignedInt and \
                format.channelCount() == 1:
            self.format = format

    # start method takes filtering
    # frequency as argument
    def start(self, f, q):

        self.open(QIODevice.ReadOnly)
        self.f = f
        self.q = q
        # declare Filter object for given
        # frequency and q
        self.y = Filter(self.f, SAMPLE_RATE, self.q)
        # declare input buffer
        self.buffer = np.zeros(FiltGenerator.SAMPLES_PER_READ)

    # generateData method performs filtering
    def generateData(self, format, samples):

        # Noise object creates a buffer of noise
        n.generate_noise(self.buffer)
        # create array for filter class to write
        # values out to
        output = np.zeros(FiltGenerator.SAMPLES_PER_READ)
        # perform dsp on noise buffer, write values
        # to output array
        self.y.process(output, self.buffer)
        # convert output values to 16 bit int
        # and return as byte array
        output = output.astype(np.int16)
        return output.tostring()

    def readData(self, bytes):

        if bytes > 2 * FiltGenerator.SAMPLES_PER_READ:
            bytes = 2 * FiltGenerator.SAMPLES_PER_READ
        return self.generateData(self.format,
                                 bytes//2)


############### End of Filtered Noise generator class ################


############ Class for generating sine tones in real-time ############


class SineGenerator(QIODevice):

    # initialiser and readData methods are same as above

    SAMPLES_PER_READ = 1024

    def __init__(self, format, parent=None):

        QIODevice.__init__(self, parent)
        self.data = QByteArray()

        self.phase = 0

        if format.isValid() and \
                format.sampleSize() == 16 and \
                format.byteOrder() == \
        QAudioFormat.LittleEndian and \
                format.sampleType() == \
        QAudioFormat.SignedInt and \
                format.channelCount() == 1:
            self.format = format

    def start(self, f):

        self.open(QIODevice.ReadOnly)
        self.f = f

    def generateData(self, format, samples):
        # this is the same as the code from the class
        # notes
        pps = self.f*2*np.pi/format.sampleRate()
        finalphase = samples*pps + self.phase
        tone = (
            100 * np.sin(
                np.arange(self.phase,
                          finalphase,
                          pps)
            )
        ).astype(np.int16)
        self.phase = finalphase % (2*np.pi)
        return tone.tostring()

    def readData(self, bytes):

        if bytes > 2 * SineGenerator.SAMPLES_PER_READ:
            bytes = 2 * SineGenerator.SAMPLES_PER_READ
        return self.generateData(self.format,
                                 bytes//2)


#################### End of sine generator class #####################


########## Class for generating sawtooth tones in real-time ##########


class SawGenerator(QIODevice):

    # initialiser and readData methods are same as above

    SAMPLES_PER_READ = 1024

    def __init__(self, format, parent=None):

        QIODevice.__init__(self, parent)
        self.data = QByteArray()

        self.phase = 0

        if format.isValid() and \
                format.sampleSize() == 16 and \
                format.byteOrder() == \
        QAudioFormat.LittleEndian and \
                format.sampleType() == \
        QAudioFormat.SignedInt and \
                format.channelCount() == 1:
            self.format = format

    def start(self, f):

        self.open(QIODevice.ReadOnly)
        self.f = f

    def generateData(self, format, samples):
        pps = self.f*2*np.pi/format.sampleRate()
        finalphase = samples*pps + self.phase
        tone = (
            # scipy's sawtooth function used instead
            # of np.sin
            100 * signal.sawtooth(
                np.arange(self.phase,
                          finalphase,
                          pps)
            )
        ).astype(np.int16)
        self.phase = finalphase % (2*np.pi)
        return tone.tostring()

    def readData(self, bytes):

        if bytes > 2 * SawGenerator.SAMPLES_PER_READ:
            bytes = 2 * SawGenerator.SAMPLES_PER_READ
        return self.generateData(self.format,
                                 bytes//2)


################### End of sawtooth generator class ##################


########################## Main GUI class ############################


class MainWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.create_UI(parent)

        # set appropriate format for output object
        format = QAudioFormat()
        format.setChannelCount(AUDIO_CHANS)
        format.setSampleRate(SAMPLE_RATE)
        format.setSampleSize(SAMPLE_SIZE)
        format.setCodec("audio/pcm")
        format.setByteOrder(
            QAudioFormat.LittleEndian
        )
        format.setSampleType(
            QAudioFormat.SignedInt
        )

        # declare audio output object for samples to
        # be written to
        self.output = QAudioOutput(format, self)
        output_buffer_size = \
            int(2*SAMPLE_RATE
                 * CTRL_INTERVAL/1000)
        self.output.setBufferSize(
            output_buffer_size
        )

        # declare objects of each of the audio synthesis
        # classes

        self.filtgenerator = FiltGenerator(format, self)
        self.sinegenerator = SineGenerator(format, self)
        self.sawgenerator = SawGenerator(format, self)

    # this is quite messy but Qt needs all the UI stuff to be in this one method
    def create_UI(self, parent):

        ################# Creation of Widgets ################

        # create a title widget with suitable font,
        # size and colour
        self.title = QLabel()
        font = QFont("Serif", 50)
        self.title.setFont(font)
        self.title.setAlignment(Qt.AlignHCenter)
        self.title.setStyleSheet("QLabel { color : blue; }")
        self.title.setText("AP4 Midi Synthesiser")

        # create quit and options buttons - these will appear
        # on either side of the title at the top
        self.quitbutton = QPushButton(self.tr('&Quit'))
        self.optionsbutton = QPushButton(self.tr('&Options'))

        # create a dial widget to vary the filter Q, with
        # corresponding label widget. Min. and max. values will
        # later be scaled to go between 0.99 and 0.9999
        self.qdial = QDial()
        self.qdial.setMinimum(9900)
        self.qdial.setMaximum(9999)
        # default value at relatively high q
        self.qdial.setValue(9990)
        self.qlabel = QLabel()
        self.qlabel.setText("Q")

        # create the other dial widget - detune - with
        # corresponding label. Limits are set as these
        # values will be later used to vary frequency
        # of notes.
        self.detunedial = QDial()
        self.detunedial.setMinimum(80)
        self.detunedial.setMaximum(120)
        # default 12 o'clock - 'in tune'
        self.detunedial.setValue(100)
        self.detunelabel = QLabel()
        self.detunelabel.setText("Detune")

        # create the 3 button widgets for each of the
        # different sound options
        self.noisebutton = QPushButton(self.tr('&Filtered Noise'))
        self.noisebutton.setMinimumSize(100, 75)
        self.sinebutton = QPushButton(self.tr('&Sine'))
        self.sinebutton.setMinimumSize(100, 75)
        self.sawbutton = QPushButton(self.tr('&Sawtooth'))
        self.sawbutton.setMinimumSize(100, 75)

        # create the sustain button widget
        self.sustainbutton = QPushButton(self.tr('&Sustain'))

        # create the volume-related widgets - vertical slider,
        # box to display value and text label
        self.volumeslider = QSlider(Qt.Vertical)
        self.volumeslider.setRange(0, 100)
        self.volumebox = QLCDNumber()
        self.volumelabel = QLabel()
        self.volumelabel.setText("Volume")

        ############### End of Widget Creation ###############

        #################### Widget Layout ###################

        # layout for Q dial and label
        qlayout = QVBoxLayout()
        qlayout.addWidget(self.qdial)
        qlayout.addWidget(self.qlabel)
        self.qlabel.setAlignment(Qt.AlignHCenter)

        # layout for detune dial and label
        detunelayout = QVBoxLayout()
        detunelayout.addWidget(self.detunedial)
        detunelayout.addWidget(self.detunelabel)
        self.detunelabel.setAlignment(Qt.AlignHCenter)

        # layout to combine both dial layouts
        layout1 = QHBoxLayout()
        layout1.addStretch(1)
        layout1.addLayout(qlayout)
        layout1.addStretch(1)
        layout1.addLayout(detunelayout)
        layout1.addStretch(1)

        # layout for the 3 sound source buttons
        layout2 = QHBoxLayout()
        layout2.addStretch(1)
        layout2.addWidget(self.noisebutton)
        layout2.addStretch(1)
        layout2.addWidget(self.sinebutton)
        layout2.addStretch(1)
        layout2.addWidget(self.sawbutton)
        layout2.addStretch(1)

        # layout to combine dial layouts, button layout
        # and sustain button
        layout3 = QVBoxLayout()
        layout3.addLayout(layout1)
        layout3.addStretch(1)
        layout3.addLayout(layout2)
        layout3.addStretch(1)
        layout3.addWidget(self.sustainbutton)
        layout3.addStretch(1)

        # layout to combine volume-related widgets
        volumelayout = QVBoxLayout()
        volumelayout.addWidget(self.volumeslider)
        volumelayout.addWidget(self.volumebox)
        volumelayout.addWidget(self.volumelabel)

        # layout to combine previous layout with
        # volume layout
        layout4 = QHBoxLayout()
        layout4.addLayout(layout3)
        layout4.addLayout(volumelayout)

        # layout for top layer with title, and quit
        # and options buttons
        toplayout = QHBoxLayout()
        toplayout.addWidget(self.quitbutton)
        toplayout.addStretch(1)
        toplayout.addWidget(self.title)
        toplayout.addStretch(1)
        toplayout.addWidget(self.optionsbutton)

        # final layout - combines previous layout with
        # top layout
        masterlayout = QVBoxLayout(self)
        masterlayout.addLayout(toplayout)
        masterlayout.addLayout(layout4)

        ################ End of widget layout ################

        ####################### Slot Connections ######################

        # when quit button is clicked, call
        # slot to quit program
        self.quitbutton.clicked.connect(self.quitClicked)

        # when value of volume slider is changed, call
        # slot to change number display and output volume
        self.volumeslider.valueChanged.connect(self.volumeslidercontrol)

        # when options button is clicked, call slot to
        # open up new options window

        self.optionsbutton.clicked.connect(self.optionsClicked)

        # when each of the respective sound buttons are clicked,
        # call slot which will perform connections
        # to generate the appropriate audio
        self.noisebutton.clicked.connect(self.filtClicked)
        self.sinebutton.clicked.connect(self.sineClicked)
        self.sawbutton.clicked.connect(self.sawClicked)

        ################### End of Slot Connections ###################

        ############### Creation of MIDI Reader Thread ################

        # create instance of MidiPortReader class
        self.midiListener = MidiPortReader()
        # create a QThread
        self.listenerThread = QThread()
        # move the listener object into the new thread
        self.midiListener.moveToThread(self.listenerThread)
        # when thread starts, connect to the listener function
        # which reads MIDI input
        self.listenerThread.started.connect(self.midiListener.listener)
        # start the thread
        self.listenerThread.start()

        #################### End of thread stuff ######################

    ################################### Slots #######################################

    # slot to close window

    @pyqtSlot()
    def quitClicked(self):
        self.close()

    # slot to display options box

    @pyqtSlot()
    def optionsClicked(self):
        # creates a message box
        optionsbox = QMessageBox()
        optionsbox.setIcon(QMessageBox.Information)
        optionsbox.setWindowTitle('Options')
        # provide user with various standard options - though these have
        # no functionality and act as a demonstration of the various possibilities
        # of Qt design
        optionsbox.setStandardButtons(QMessageBox.Open | QMessageBox.Save |
                                      QMessageBox.RestoreDefaults | QMessageBox.Cancel | QMessageBox.SaveAll)
        optionsbox.exec()

    # slot to to change volume-related parameters

    @pyqtSlot()
    def volumeslidercontrol(self):
        # in the numbered box, display the value of the slider
        self.volumebox.display(self.volumeslider.value())
        # set the volume of the output object proportional to
        # value of the slider
        self.output.setVolume(self.volumeslider.value()/100)

    # slot for when filtered noise button is clicked

    @pyqtSlot()
    def filtClicked(self):
        # connect newNoteFrequency signal to filtered noise generation slot
        self.midiListener.newNoteFrequency.connect(self.generatefilt)

    # slot for when sine button is clicked

    @pyqtSlot()
    def sineClicked(self):
        # connect newNoteFrequency signal to sine generation slot
        self.midiListener.newNoteFrequency.connect(self.generatesine)

    # slot for when saw button is clicked

    @pyqtSlot()
    def sawClicked(self):
        # connect newNoteFrequency signal to sawtooth generation slot.
        # These 3 slots allow a user to change the audio being generated
        # by clicking on the different buttons.
        self.midiListener.newNoteFrequency.connect(self.generatesaw)

    # slot for generating filtered noise (only if filtclicked has been called)

    @pyqtSlot(float)
    def generatefilt(self, freq):
        # scale the frequency value based on the detune dial value
        freq = freq * self.detunedial.value() * 0.01
        # scale the q factor based on the qdial value - set to
        # vary between 0.99 and 0.9999
        q = self.qdial.value() / 10000
        # start the generator object (from line 294) for the
        # given frequency and calculated q
        self.filtgenerator.start(freq, q)
        # start the output object - audio is generated
        self.output.start(self.filtgenerator)

    # slot for generating sine tones (only if sineclicked has been called)

    @pyqtSlot(float)
    def generatesine(self, freq):
        # scale the frequency value based on the detune dial value
        freq = freq * self.detunedial.value() * 0.01
        # start the generator object (from line 295) for the
        # given frequency
        self.sinegenerator.start(freq)
        # start the output object - audio is generated
        self.output.start(self.sinegenerator)

    # slot for generating sawtooth tones (only if sawclicked has been called)

    @pyqtSlot(float)
    def generatesaw(self, freq):
        # scale the frequency value based on the detune dial value
        freq = freq * self.detunedial.value() * 0.01
        # start the generator object (from line 296) for the
        # given frequency
        self.sawgenerator.start(freq)
        # start the output object - audio is generated
        self.output.start(self.sawgenerator)

    ################################ End of Slots ##################################


if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
