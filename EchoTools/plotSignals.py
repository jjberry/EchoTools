'''
Created on May 29, 2013

@author: Jeff
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

class PlotSignals(QMainWindow):
    def __init__(self, posCC, negCC, control, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Results') 
        self.posCC = posCC
        self.negCC = negCC
        self.sequence = control.sequence
        self.onset = control.onset
        self.control = control
        self.STD = True
        self.TTEST = True
        self.createMainFrame()

    def getResults(self):
        maxval = len(self.posCC.ROI[self.posCC.ROI])
        posRange = (2, 50)
        negRange = (59, 118)
        posVal1 = []
        negVal1 = []
        posVal2 = []
        negVal2 = []
        for j in range(self.sequence.shape[0]):
            cpVal1 = []
            cnVal1 = []
            cpVal2 = []
            cnVal2 = []
            for i in range(self.sequence.shape[1]):
                pmask = (self.sequence[j,i,:,:]>=posRange[0])&(self.sequence[j,i,:,:]<=posRange[1])&self.posCC.ROI
                nmask = (self.sequence[j,i,:,:]>=negRange[0])&(self.sequence[j,i,:,:]<=negRange[1])&self.posCC.ROI
                cpVal1.append(float(len(self.sequence[j,i,:,:][pmask]))/maxval)
                cnVal1.append(float(len(self.sequence[j,i,:,:][nmask]))/maxval)
                pmask = (self.sequence[j,i,:,:]>=posRange[0])&(self.sequence[j,i,:,:]<=posRange[1])&self.negCC.ROI
                nmask = (self.sequence[j,i,:,:]>=negRange[0])&(self.sequence[j,i,:,:]<=negRange[1])&self.negCC.ROI
                cpVal2.append(float(len(self.sequence[j,i,:,:][pmask]))/maxval)
                cnVal2.append(float(len(self.sequence[j,i,:,:][nmask]))/maxval)    
            posVal1.append(np.array(cpVal1))
            negVal1.append(np.array(cnVal1))
            posVal2.append(np.array(cpVal2))
            negVal2.append(np.array(cnVal2))
        posVal1 = np.array(posVal1)
        negVal1 = np.array(negVal1)
        posVal2 = np.array(posVal2)
        negVal2 = np.array(negVal2)
        
        return posVal1, negVal1, posVal2, negVal2
    
    def onDraw(self):
        self.axes.clear()
        fs = 83.0
        step = 1.0 / fs
        xt = np.arange(0, self.sequence.shape[1]*step, step)
        xt -= xt[self.onset]

        posVal1, negVal1, posVal2, negVal2 = self.getResults()
        
        self.axes.plot(xt[:posVal1.shape[1]], (posVal1.mean(axis=0))+1, 'r-')
        self.axes.plot(xt[:posVal1.shape[1]], (negVal1.mean(axis=0))+1, 'b-')
        self.axes.plot(xt[:posVal1.shape[1]], posVal2.mean(axis=0), 'r-')
        self.axes.plot(xt[:posVal1.shape[1]], negVal2.mean(axis=0), 'b-')

        if self.STD:
            self.axes.plot(xt[:posVal1.shape[1]], (posVal1.mean(axis=0))+(posVal1.std(axis=0))+1, 'r--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (posVal1.mean(axis=0))-(posVal1.std(axis=0))+1, 'r--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (negVal1.mean(axis=0))+(negVal1.std(axis=0))+1, 'b--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (negVal1.mean(axis=0))-(negVal1.std(axis=0))+1, 'b--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (posVal2.mean(axis=0))+(posVal2.std(axis=0)), 'r--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (posVal2.mean(axis=0))-(posVal2.std(axis=0)), 'r--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (negVal2.mean(axis=0))+(negVal2.std(axis=0)), 'b--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (negVal2.mean(axis=0))-(negVal2.std(axis=0)), 'b--', alpha=0.5)

        if self.TTEST:
            t1, p1 = stats.ttest_ind(posVal1, negVal1, axis=0)
            t2, p2 = stats.ttest_ind(posVal2, negVal2, axis=0)
            collection1 = collections.BrokenBarHCollection.span_where(xt, ymin=1, ymax=2, where=p1<0.05,
                                                                  facecolor='0.5', alpha=0.25)
            self.axes.add_collection(collection1)
            collection2 = collections.BrokenBarHCollection.span_where(xt, ymin=0, ymax=1, where=p2<0.05,
                                                                  facecolor='0.5', alpha=0.25)
            self.axes.add_collection(collection2)
        
        self.axes.hlines([0,1,2], xt[0], xt[posVal1.shape[1]-1], color='black')
        self.axes.vlines(xt[self.onset], 0, 2, color='black', linewidth=2)
        self.axes.set_xlim(xt[0], xt[posVal1.shape[1]-1])    
        self.axes.set_yticks([0.5, 1.5])
        self.axes.set_yticklabels(['Neg ROI', 'Pos ROI'])
        self.axes.set_ylim(-0.25, 2.25)

        self.canvas.draw()

    def onExport(self, fname):
        posVal1, negVal1, posVal2, negVal2 = self.getResults()
        out = open(fname, 'w')
        out.write('signalName,posNeg,')
        for i in range(posVal1.shape[1]):
            out.write('v%02d,'%(i+1))
        out.write('\n')
        for sig, name in zip([posVal1, negVal1, posVal2, negVal2],
                            ['posROI_pos', 'posROI_neg', 'negROI_pos', 'negROI_neg']):
            for i in range(sig.shape[0]):
                out.write('%s,%s,'%(name, name[-3:]))
                for j in range(sig.shape[1]):
                    out.write('%0.6f,'%sig[i,j])
                out.write('\n')
        out.close()

    def onSequenceChanged(self, sequence, onset):
        self.sequence = sequence
        self.onset = onset
        self.onDraw()
    
    def onStdChecked(self):
        self.STD = not self.STD
        self.onDraw()
    
    def onTtestChecked(self):
        self.TTEST = not self.TTEST
        self.onDraw()
        
    def createMainFrame(self):
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

        self.posCC.plotSignal.connect(self.onDraw)
        self.negCC.plotSignal.connect(self.onDraw)
        self.control.sequenceChanged.connect(self.onSequenceChanged)
        self.control.closeSignal.connect(self.close)
        self.control.exportData.connect(self.onExport)
        self.connect(self.stdCB, SIGNAL('stateChanged(int)'), self.onStdChecked)
        self.connect(self.ttestCB, SIGNAL('stateChanged(int)'), self.onTtestChecked)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.stdCB)
        vbox.addWidget(self.ttestCB)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
