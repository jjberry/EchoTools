'''
Created on Jun 4, 2013

@author: Jeff
'''
import sys, os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
import Image
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure


class MaxMovement(QMdiSubWindow):
    ###########
    # Signals #
    ###########
    plotSignal = pyqtSignal()

    ########################
    # Initializing Methods #
    ########################

    def __init__(self, title, imgfile, control, parent=None):
        QMdiSubWindow.__init__(self, parent)
        self.setWindowTitle(title)
        self.imgfile = imgfile
        self.control = control
        self.start = self.control.framesBefore
        self.end = self.control.framesAfter
        self.ROI = np.zeros((600,800)).astype(np.bool)
        valid = np.load('validinds.npy')
        self.valid = valid.reshape((600,800), order='F')
        self.notvalid = np.logical_not(self.valid)

        self.createMainFrame()
        self.getROI()
        self.onDraw()
        
    def createMainFrame(self):
        self.mainFrame = QWidget()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.mainFrame)
        self.axes = self.fig.add_subplot(111)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.mainFrame)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)

        self.mainFrame.setLayout(vbox)
        self.setWidget(self.mainFrame)

    def convertScale(self, H):
        pos = (2,30)
        neg = (60,118)
        H[self.notvalid] = (np.zeros_like(H))[self.notvalid]
        converted = np.zeros(H.shape)
        nmask = (H>=neg[0])&(H<=neg[1])
        pmask = (H>=pos[0])&(H<=pos[1])
        converted[nmask] = -(119 - H[nmask])
        converted[pmask] = H[pmask] * 2
        
        return converted
        
    def getROI(self):
        #shape of sequence is (3, nframe, 600, 800)
        pass
        #seq = self.control.sequence
        #for r in range(seq.shape[0]):
        #    for f in range(self.start, self.end+1):
        #        frame = seq[r,f,:,:]

        
    
    def onDraw(self):
        self.axes.clear()
        #img = Image.open(self.imgfile)
        #img = np.asarray(img)
        img = self.convertScale(self.control.sequence[0,2,:,:])
        self.axes.imshow(img)
        
        self.plotSignal.emit()
        self.canvas.draw()
        
        
