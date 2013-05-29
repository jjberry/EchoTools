'''
Created on May 29, 2013

@author: Jeff
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

class ColorConfig(QMainWindow):
    plotSignal = pyqtSignal()
    def __init__(self, title, lower=2, upper=50, imgfile=None, control=None, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle(title)
        self.lower = lower
        self.upper = upper
        self.imgfile = imgfile
        self.control = control
        self.radius = 50
        valid = np.load('validinds.npy')
        self.valid = valid.reshape((600,800), order='F')
        self.notvalid = np.logical_not(self.valid)
        self.USEALL = True
        self.createMainFrame()
        self.onDraw()

    def convertImg(self, filename):
        H = RGB2HSV(filename)
        H[self.notvalid] = (np.zeros_like(H))[self.notvalid]       
        return H

    def getFiltered(self, H, lower, upper, invert=False):
        '''defaults for pos: 2-50
                        neg: 59-118
        '''
        pmask = (H>=lower)&(H<=upper)
        imgpos = np.zeros_like(H)
        imgpos[pmask] = H[pmask]
        if invert:
            rmask = imgpos>0
            imgpos[rmask] = (upper+1)-imgpos[rmask]
        
        return imgpos

    def onEdit(self):
        lower = int(self.low_text.text())
        upper = int(self.up_text.text())
        if (self.lower != lower) or (self.upper != upper):
            self.lower = lower
            self.upper = upper
            self.low_slider.setValue(self.lower)
            self.up_slider.setValue(self.upper)
            self.onDraw()

    def onSlider(self):
        self.lower = self.low_slider.value()
        self.upper = self.up_slider.value()
        self.low_text.setText(str(self.lower))
        self.up_text.setText(str(self.upper))
        self.onDraw()

    def getAveCenter(self):
        npix = len(self.valid[self.valid])
        threshold = npix * 0.1
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

    def onDraw(self):
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
        self.imgfile = str(filename)
        self.H = self.convertImg(self.imgfile)
        self.onDraw()
        
    def onRadiusChanged(self, radius):
        self.radius = radius
        self.onDraw()
    
    def onUseAllChecked(self):
        self.USEALL = not self.USEALL
        self.onDraw() 
        
    def createMainFrame(self):
        self.main_frame = QWidget()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.axes = self.fig.add_subplot(111)

        self.H = self.convertImg(self.imgfile)
        self.invert = False

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
        self.connect(self.useAllCB, SIGNAL('stateChanged(int)'), self.onUseAllChecked)

        self.low_text = QLineEdit()
        self.low_text.setMaximumWidth(40)
        self.low_text.setText(str(self.lower))
        
        self.up_text = QLineEdit()
        self.up_text.setMaximumWidth(40)
        self.up_text.setText(str(self.upper))
        
        self.control.imageChanged.connect(self.onImageChanged)
        self.control.radiusChanged.connect(self.onRadiusChanged)
        self.control.closeSignal.connect(self.close)
        self.connect(self.low_slider, SIGNAL('valueChanged(int)'), self.onSlider)
        self.connect(self.up_slider, SIGNAL('valueChanged(int)'), self.onSlider)
        self.connect(self.low_text, SIGNAL('editingFinished()'), self.onEdit)
        self.connect(self.up_text, SIGNAL('editingFinished()'), self.onEdit)

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
        self.setCentralWidget(self.main_frame)
