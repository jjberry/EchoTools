'''
Created on Jun 4, 2013

@author: Jeff
'''
import sys, os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
import Image
from scipy import ndimage
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from Rgb2Hsv import RGB2HSV

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
        self.ROI = np.zeros((600,800)).astype(np.bool)
        valid = np.load('validinds.npy')
        self.valid = valid.reshape((600,800), order='F')
        self.notvalid = np.logical_not(self.valid)
        self.ROItype = 'absolute peak-peak difference'
        self.radius = 50
        
        self.getStartEnd(self.control.framesBefore, self.control.framesAfter)
        self.convertSequence()
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
        self.ROItypeCombo = QComboBox()
        self.ROItypeCombo.addItems(['absolute peak-peak difference', 'sum of frame-by-frame change'])
        ROItypetext = QLabel('Calculate ROI using:')
        ROIboundL = QLabel('Calculate ROI from frame:')
        ROIboundU = QLabel('to:')
        self.ROIboundLText = QLineEdit()
        self.ROIboundLText.setText(str(self.control.framesBefore))
        self.ROIboundUText = QLineEdit()
        self.ROIboundUText.setText(str(self.control.framesAfter))

        self.connect(self.ROItypeCombo, SIGNAL('activated(QString)'), self.onCombo)
        self.control.imageChanged.connect(self.onImageChanged)
        self.control.closeSignal.connect(self.close)
        self.control.sequenceChanged.connect(self.onSequenceChanged)
        self.control.radiusChanged.connect(self.onRadiusChanged)
        self.connect(self.ROIboundLText, SIGNAL('editingFinished()'), self.onBoundsChanged)
        self.connect(self.ROIboundUText, SIGNAL('editingFinished()'), self.onBoundsChanged)

        hbox = QHBoxLayout()
        hbox.addWidget(ROItypetext)
        hbox.addWidget(self.ROItypeCombo)
        boundHbox = QHBoxLayout()
        boundHbox.addWidget(ROIboundL)
        boundHbox.addWidget(self.ROIboundLText)
        boundHbox.addWidget(ROIboundU)
        boundHbox.addWidget(self.ROIboundUText)
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)
        vbox.addLayout(boundHbox)

        self.mainFrame.setLayout(vbox)
        self.setWidget(self.mainFrame)

    def convertSequence(self):
        '''
        Converts the sequence inherited from control panel from HSV-based hue values to
        a more useful scale, using self.convertScale
        '''
        converted = np.zeros_like(self.control.sequence, dtype='int') 
        for rep in range(self.control.sequence.shape[0]):
            for frame in range(self.control.sequence.shape[1]):
                converted[rep,frame,:,:] = self.convertScale(self.control.sequence[rep,frame,:,:])
        self.converted = converted
            
    def convertScale(self, H):
        '''
        This takes the relevant colors on the HSV scale (determined by looking at the
        positive and negative color bars in the images) and converts them to a more
        meaningful scale, i.e. blues & greens (negative) are now in about (-1, -60) and 
        oranges & yellows (positive) in (1, 60). Other colors are zeros
        '''
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
        if self.ROItype == 'absolute peak-peak difference':
            center = self.getPeakMax()
        else:
            center = self.getFrameMax()
        xx, yy = np.mgrid[:600, :800]
        circle = (xx-center[0])**2 + (yy-center[1])**2
        self.ROI = circle<(self.radius**2)
        self.center = center
    
    def getPeakMax(self):
        mins = np.zeros((600,800),dtype='int')
        maxes = np.zeros((600,800),dtype='int')
        for rep in range(self.converted.shape[0]):
            for frame in range(self.start, self.end):
                current = self.converted[rep,frame,:,:]
                minmask = (current < mins)
                maxmask = (current > maxes)
                mins[minmask] = current[minmask]
                maxes[maxmask] = current[maxmask]
        peakdiff = np.abs(maxes - mins)
        maxval = peakdiff.max()
        maxmask = peakdiff==maxval
        filt = np.zeros_like(peakdiff)
        filt[maxmask] = peakdiff[maxmask]
        center = ndimage.measurements.center_of_mass(filt)
        return center
    
    def getFrameMax(self):
        diffs = np.zeros((600,800), dtype='int')
        for rep in range(self.converted.shape[0]):
            for frame in range(self.start, self.end-1):
                current = self.converted[rep,frame,:,:]
                nextf = self.converted[rep,frame+1,:,:]
                diff = np.abs(current - nextf).astype('int')
                diffs += diff
        maxval = diffs.max()
        maxmask = diffs==maxval
        filt = np.zeros_like(diffs)
        filt[maxmask] = diffs[maxmask]
        center = ndimage.measurements.center_of_mass(filt)
        return center

    def getStartEnd(self, before, after):
        nframes = self.control.sequence.shape[1]
        onset = self.control.framesBefore
        start = onset - before
        if start < 0:
            start = 0
        end = onset + after
        if end > nframes:
            end = nframes
        self.start = start
        self.end = end
    
    def onDraw(self):
        self.fig.clear()
        self.axes = self.fig.add_subplot(111)
        H = RGB2HSV(self.imgfile)
        img = self.convertScale(H)
        cax = self.axes.imshow(img, vmin=-60, vmax=60)
        self.axes.plot(self.center[1], self.center[0], 'bx')
        self.axes.imshow(self.ROI, cmap='gray', alpha=0.2)
        cbar = self.fig.colorbar(cax, ticks=[-60,0,60])
        cbar.ax.set_yticklabels(['-2.5 cm/s', '0', '2.5 cm/s'])
        self.plotSignal.emit()
        self.canvas.draw()
        
    def onCombo(self, text):
        self.ROItype = str(text)
        self.getROI()
        self.onDraw()
        
    def onBoundsChanged(self):
        start = int(str(self.ROIboundLText.text()))
        end = int(str(self.ROIboundUText.text()))   
        self.getStartEnd(start, end)
        self.getROI()
        self.onDraw()
        
    def onImageChanged(self, filename):
        '''
        Catches the signal from the ControlPanel that the current image has changed
        '''
        self.imgfile = str(filename)
        self.onDraw()

    def onSequenceChanged(self, sequence, onset):
        self.getStartEnd(self.control.framesBefore, self.control.framesAfter)
        self.ROIboundLText.setText(str(self.control.framesBefore))
        self.ROIboundUText.setTest(str(self.control.framesAfter))
        self.convertSequence()
        self.getROI()
        self.onDraw()    
 
    def onRadiusChanged(self, radius):
        '''
        Changes the radius of the ROI from the value in the text box
        '''
        self.radius = radius
        self.getROI()
        self.onDraw()
