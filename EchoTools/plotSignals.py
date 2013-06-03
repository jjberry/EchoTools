'''
Created on May 29, 2013

Displays the mean pixel counts of positive and negative colors defined by the 
ColorConfig objects. The results are displayed as a percentage of the total ROI.
Standard deviations and significant differences (from a t-test) can be optionally
displayed. The title can be changed by the user, and the plot can be saved.

@author: Jeff Berry
'''
import numpy as np
from scipy import stats
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import collections

class PlotSignals(QMdiSubWindow):
    '''
    A widget for displaying results
    '''
    ########################
    # Initializing Methods #
    ########################
    def __init__(self, ROIs, control, parent=None):
        '''
        Initializes internal variables
        '''
        QMdiSubWindow.__init__(self, parent)
        self.setWindowTitle('Results') 
        self.ROIs = ROIs
        self.sequence = control.sequence
        self.onset = control.onset
        self.control = control
        self.title = 'Results'
        self.STD = True
        self.TTEST = True
        
        self.createMainFrame()

    def createMainFrame(self):
        '''
        Creates the main window
        '''
        # Widgets 
        self.main_frame = QWidget()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.axes = self.fig.add_subplot(111)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        self.stdCB = QCheckBox("Show standard deviation")
        self.stdCB.setChecked(True)        
        self.ttestCB = QCheckBox("Show significant difference")
        self.ttestCB.setChecked(True)
        titleLabel = QLabel('Set Title:')
        self.titleText = QLineEdit()
        self.titleText.setText(self.title)

        # Connections 
        for roi in self.ROIs:
            roi.plotSignal.connect(self.onDraw)
        self.control.sequenceChanged.connect(self.onSequenceChanged)
        self.control.closeSignal.connect(self.close)
        self.control.exportData.connect(self.onExport)
        self.connect(self.stdCB, SIGNAL('stateChanged(int)'), self.onStdChecked)
        self.connect(self.ttestCB, SIGNAL('stateChanged(int)'), self.onTtestChecked)
        self.connect(self.titleText, SIGNAL('editingFinished()'), self.onChangeTitle)
        
        # Layouts 
        hbox = QHBoxLayout()
        hbox.addWidget(titleLabel)
        hbox.addWidget(self.titleText)
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.stdCB)
        vbox.addWidget(self.ttestCB)
        vbox.addLayout(hbox)

        self.main_frame.setLayout(vbox)
        self.setWidget(self.main_frame)

    #####################
    #  Internal Methods #
    #####################
    def getResults(self):
        '''
        Helper function that extracts the pixel counts from the images.
        Currently set up to calculate results from 2 ColorConfig objects.
        returns 4 nRepetitions x nFrames numpy arrays, 2 for each ROI 
        (pos and neg pixels). 
        '''
        output = []
        for roi in self.ROIs:
            maxval = len(roi.ROI[roi.ROI])
            posRange = (2, 50)
            negRange = (59, 118)
            posVal = []
            negVal = []
            for j in range(self.sequence.shape[0]):
                cpVal = []
                cnVal = []
                for i in range(self.sequence.shape[1]):
                    pmask = (self.sequence[j,i,:,:]>=posRange[0])&(self.sequence[j,i,:,:]<=posRange[1])&roi.ROI
                    nmask = (self.sequence[j,i,:,:]>=negRange[0])&(self.sequence[j,i,:,:]<=negRange[1])&roi.ROI
                    cpVal.append(float(len(self.sequence[j,i,:,:][pmask]))/maxval)
                    cnVal.append(float(len(self.sequence[j,i,:,:][nmask]))/maxval)
                posVal.append(np.array(cpVal))
                negVal.append(np.array(cnVal))
            posVal = np.array(posVal)
            negVal = np.array(negVal)
            output.append(posVal)
            output.append(negVal)
        return output

    #########
    # Slots #
    #########    
    def onDraw(self):
        '''
        Draws the plot on the MPL canvas widget
        '''
        self.axes.clear()
        fs = 83.0
        step = 1.0 / fs
        xt = np.arange(0, self.sequence.shape[1]*step, step)
        xt -= xt[self.onset]

        signals = self.getResults()

        for i in range(0, len(signals), 2):        
            self.axes.plot(xt[:signals[i].shape[1]], (signals[i].mean(axis=0))+(i/2), 'r-')
            self.axes.plot(xt[:signals[i].shape[1]], (signals[i+1].mean(axis=0))+(i/2), 'b-')

        if self.STD:
            for i in range(0, len(signals), 2):
                self.axes.plot(xt[:signals[i].shape[1]], (signals[i].mean(axis=0))+(signals[i].std(axis=0))+(i/2), 'r--', alpha=0.5)
                self.axes.plot(xt[:signals[i].shape[1]], (signals[i].mean(axis=0))-(signals[i].std(axis=0))+(i/2), 'r--', alpha=0.5)
                self.axes.plot(xt[:signals[i].shape[1]], (signals[i+1].mean(axis=0))+(signals[i+1].std(axis=0))+(i/2), 'b--', alpha=0.5)
                self.axes.plot(xt[:signals[i].shape[1]], (signals[i+1].mean(axis=0))-(signals[i+1].std(axis=0))+(i/2), 'b--', alpha=0.5)

        if self.TTEST:
            for i in range(0, len(signals), 2):
                t1, p1 = stats.ttest_ind(signals[i], signals[i+1], axis=0)
                collection1 = collections.BrokenBarHCollection.span_where(xt, ymin=(i/2), ymax=(i/2)+1, where=p1<0.05,
                                                                  facecolor='0.5', alpha=0.25)
                self.axes.add_collection(collection1)
        
        self.axes.hlines(range((len(signals)+2)/2), xt[0], xt[signals[0].shape[1]-1], color='black')
        self.axes.vlines(xt[self.onset], 0, (len(signals)+1)/2, color='black', linewidth=2)
        self.axes.set_xlim(xt[0], xt[signals[0].shape[1]-1])    
        self.axes.set_yticks(list(np.arange(len(signals)/2)+0.5))
        labels = []
        count = 1
        for i in range((len(signals)+1)/2):
            labels.append('ROI %d'%count)
            count += 1
        self.axes.set_yticklabels(labels)
        self.axes.set_ylim(-0.25, (len(signals)/2)+0.25)
        self.axes.set_title(self.title)

        self.canvas.draw()

    def onExport(self, fname):
        '''
        Exports the values used to create the current plot (unaveraged signals)
        to a comma-separated plaintext file.
        '''
        signals = self.getResults()
        out = open(fname, 'w')
        out.write('signalName,posNeg,')
        for i in range(signals[0].shape[1]):
            out.write('v%02d,'%(i+1))
        out.write('\n')
        count = 0
        for s in range(len(signals)):
            if s%2 == 0:
                count += 1
            for i in range(signals[s].shape[0]):
                if s%2 == 0:
                    name = "ROI%d_pos" % count
                else:
                    name = "ROI%d_neg" % count
                out.write('%s,%s,'%(name, name[-3:]))
                for j in range(signals[s].shape[1]):
                    out.write('%0.6f,'%signals[s][i,j])
                out.write('\n')
        out.close()

    def onSequenceChanged(self, sequence, onset):
        '''
        Catches signal from ControlPanel when sequence has changed.
        '''
        self.sequence = sequence
        self.onset = onset
        self.onDraw()
    
    def onStdChecked(self):
        '''
        Catches the signal from the show standard deviations check box
        '''
        self.STD = not self.STD
        self.onDraw()
    
    def onTtestChecked(self):
        '''
        Catches the signal from the show significant differences check box
        '''
        self.TTEST = not self.TTEST
        self.onDraw()
 
    def onChangeTitle(self):
        '''
        Changes the title of the plot when the user changes the text
        '''
        title = str(self.titleText.text())
        if title != self.title:
            self.title = title
            self.onDraw()
           