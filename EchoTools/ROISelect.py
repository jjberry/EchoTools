'''
Created on May 22, 2013

@author: Jeff
'''
import sys, os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.widgets import Lasso
from matplotlib.nxutils import points_inside_poly

import numpy as np
import Image

class ROISelect(QMdiSubWindow):
    ###########
    # Signals #
    ###########
    plotSignal = pyqtSignal()

    ########################
    # Initializing Methods #
    ########################
    def __init__(self, title, imgfile, control, parent=None):
        '''
        Initializes internal variables
        '''
        QMdiSubWindow.__init__(self, parent)
        self.setWindowTitle(title)
        self.imgfile = imgfile
        self.control = control
        self.xys = []
        self.ROI = np.zeros((600,800)).astype(np.bool)
        for i in range(800):
            for j in range(600):
                self.xys.append((i,j))
        self.create_main_frame()
        self.onDraw()

    def create_main_frame(self):
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
        self.reset = QPushButton('&Reset')
        
        # Connections
        self.cid = self.canvas.mpl_connect('button_press_event', self.onpress)
        self.control.imageChanged.connect(self.onImageChanged)
        self.control.closeSignal.connect(self.close)
        self.connect(self.reset, SIGNAL('clicked()'), self.onReset)

        # Layouts
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.reset)

        self.main_frame.setLayout(vbox)
        self.setWidget(self.main_frame)

    #########
    # Slots #
    #########
    def onReset(self):
        self.ROI = np.zeros((600,800)).astype(np.bool)
        self.cid = self.canvas.mpl_connect('button_press_event', self.onpress)
        self.onDraw()

    def onDraw(self):
        self.axes.clear()
        img = Image.open(self.imgfile)
        img = np.asarray(img)
        self.axes.imshow(img)  
        self.axes.imshow(self.ROI, alpha=0.1, cmap='gray')
        self.plotSignal.emit()
        self.canvas.draw()
      
    def getROI(self, verts):
        ind = points_inside_poly(self.xys, verts)
        self.canvas.draw_idle()
        self.canvas.widgetlock.release(self.lasso)
        del self.lasso
        self.ROI = ind
        self.ROI = self.ROI.reshape((600,800), order='F')
        self.canvas.mpl_disconnect(self.cid)
        self.onDraw()

    def onpress(self, event):
        if self.canvas.widgetlock.locked(): return
        if event.inaxes is None: return
        self.lasso = Lasso(event.inaxes, (event.xdata, event.ydata), self.getROI)
        self.canvas.widgetlock(self.lasso)
        
    def onImageChanged(self, filename):
        '''
        Catches the signal from the ControlPanel that the current image has changed
        '''
        self.imgfile = str(filename)
        self.onDraw()
