'''
Created on May 29, 2013

This widget displays an image that is converted to the HSV color space (Hue, Saturation, 
Value). The image is filtered by Hue value (0-179), with parameters controlled by the user.
The centroid of the pixels within the user parameters is used to calculate the Region of Interest
for plotting results in the PlotSignals widget.

@author: Jeff Berry
'''
import numpy as np
from scipy import ndimage
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from Rgb2Hsv import RGB2HSV

class ColorConfig(QMdiSubWindow):
    '''
    A widget for defining HSV color boundaries used in calculating the functional ROI
    '''
    ###########
    # Signals #
    ###########
    plotSignal = pyqtSignal()

    ########################
    # Initializing Methods #
    ########################
    def __init__(self, title, lower=2, upper=50, imgfile=None, control=None, parent=None):
        '''
        Initializes internal variables
        '''
        QMdiSubWindow.__init__(self, parent)
        self.setWindowTitle(title)
        self.lower = lower
        self.upper = upper
        self.imgfile = imgfile
        self.control = control
        self.radius = 50
        self.invert = False
        valid = np.load('validinds.npy')
        self.valid = valid.reshape((600,800), order='F')
        self.notvalid = np.logical_not(self.valid)
        self.USEALL = True 
        self.H = self.convertImg(self.imgfile)

        self.createMainFrame()
        self.onDraw()

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
        lower_label = QLabel('Lower bound:')
        upper_label = QLabel('Upper bound:')
        self.low_slider = QSlider(Qt.Horizontal)
        self.low_slider.setRange(0,179)
        self.low_slider.setValue(self.lower)
        self.low_slider.setTracking(True)
        self.low_slider.setTickPosition(QSlider.TicksBothSides)
        self.up_slider = QSlider(Qt.Horizontal)
        self.up_slider.setRange(0,179)
        self.up_slider.setValue(self.upper)
        self.up_slider.setTracking(True)
        self.up_slider.setTickPosition(QSlider.TicksBothSides)
        self.useAllCB = QCheckBox()
        self.useAllCB.setText("Use average over sequences")
        self.useAllCB.setChecked(True)
        self.low_text = QLineEdit()
        self.low_text.setMaximumWidth(40)
        self.low_text.setText(str(self.lower))
        self.up_text = QLineEdit()
        self.up_text.setMaximumWidth(40)
        self.up_text.setText(str(self.upper))
        
        # Connections 
        self.control.imageChanged.connect(self.onImageChanged)
        self.control.radiusChanged.connect(self.onRadiusChanged)
        self.control.closeSignal.connect(self.close)
        self.control.sequenceChanged.connect(self.onSequenceChanged)
        self.connect(self.low_slider, SIGNAL('valueChanged(int)'), self.onSlider)
        self.connect(self.up_slider, SIGNAL('valueChanged(int)'), self.onSlider)
        self.connect(self.low_text, SIGNAL('editingFinished()'), self.onEdit)
        self.connect(self.up_text, SIGNAL('editingFinished()'), self.onEdit)
        self.connect(self.useAllCB, SIGNAL('stateChanged(int)'), self.onUseAllChecked)

        # Layouts 
        low_hbox = QHBoxLayout()
        low_hbox.addWidget(lower_label)
        low_hbox.addWidget(self.low_text)
        low_hbox.addWidget(self.low_slider)
        up_hbox = QHBoxLayout()
        up_hbox.addWidget(upper_label)
        up_hbox.addWidget(self.up_text)
        up_hbox.addWidget(self.up_slider)
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.useAllCB)
        vbox.addLayout(low_hbox)
        vbox.addLayout(up_hbox)

        self.main_frame.setLayout(vbox)
        self.setWidget(self.main_frame)

    #####################
    #  Internal Methods #
    #####################
    def convertImg(self, filename):
        '''
        Helper function that filters out pixels not part of the ultrasound data
        '''
        H = RGB2HSV(filename)
        H[self.notvalid] = (np.zeros_like(H))[self.notvalid]       
        return H

    def getFiltered(self, H, lower, upper, invert=False):
        '''
        Helper function to filter an image according to the HSV color boundaries
        set by the user. 
        defaults for pos: 2-50
                        neg: 59-118
        '''
        pmask = (H>=lower)&(H<=upper)
        imgpos = np.zeros_like(H)
        imgpos[pmask] = H[pmask]
        if invert:
            rmask = imgpos>0
            imgpos[rmask] = (upper+1)-imgpos[rmask]
        
        return imgpos

    def getAveCenter(self):
        '''
        Helper function to calculate the average centroid over the sequence.
        Images with less than 10% of pixels within the color boundaries are not used
        to calculate the average.
        '''
        npix = len(self.valid[self.valid])
        threshold = 0 #npix * 0.01 #large threshold causes nans 
        centers = []
        for i in range(self.control.sequence.shape[0]):
            for j in range(self.control.sequence.shape[1]):
                img = self.getFiltered(self.control.sequence[i,j,:,:], self.lower, self.upper)
                filt = len(img[img>0])
                if filt > threshold:
                    center = ndimage.measurements.center_of_mass(img)
                    center = np.array([center[0], center[1]])
                    centers.append(center)
        centers = np.array(centers)
        return centers.mean(axis=0)

    #########
    # Slots #
    #########
    def onEdit(self):
        '''
        Catches changes to the color boundaries from the text boxes
        '''
        lower = int(self.low_text.text())
        upper = int(self.up_text.text())
        if (self.lower != lower) or (self.upper != upper):
            self.lower = lower
            self.upper = upper
            self.low_slider.setValue(self.lower)
            self.up_slider.setValue(self.upper)
            self.onDraw()

    def onSlider(self):
        '''
        Catches changes to the color boundaries from the sliders
        '''
        self.lower = self.low_slider.value()
        self.upper = self.up_slider.value()
        self.low_text.setText(str(self.lower))
        self.up_text.setText(str(self.upper))
        self.onDraw()

    def onDraw(self):
        '''
        Draws the filtered image and ROI onto the MPL canvas widget
        '''
        self.axes.clear()
        img = self.getFiltered(self.H, self.lower, self.upper, self.invert)
        if self.USEALL:
            center = self.getAveCenter()
        else:
            center = ndimage.measurements.center_of_mass(img)
        self.axes.imshow(img, cmap='gray')
        self.axes.plot(center[1], center[0], 'bx')
        self.axes.set_xlim(0,799)
        self.axes.set_ylim(0,599)
        self.axes.invert_yaxis()
        xx, yy = np.mgrid[:600, :800]
        circle = (xx-center[0])**2 + (yy-center[1])**2
        self.ROI = circle<(self.radius**2)
        self.axes.imshow(self.ROI, cmap='gray', alpha=0.2)
        self.plotSignal.emit()
        self.canvas.draw()

    def onImageChanged(self, filename):
        '''
        Catches the signal from the ControlPanel that the current image has changed
        '''
        self.imgfile = str(filename)
        self.H = self.convertImg(self.imgfile)
        self.onDraw()
        
    def onRadiusChanged(self, radius):
        '''
        Changes the radius of the ROI from the value in the text box
        '''
        self.radius = radius
        self.onDraw()
    
    def onUseAllChecked(self):
        '''
        Changes whether to calculate the ROI using all images of the sequence or the 
        current image only.
        '''
        self.USEALL = not self.USEALL
        self.onDraw() 
        
    def onSequenceChanged(self, sequence, onset):
        self.onDraw()    
    