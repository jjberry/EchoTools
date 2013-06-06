'''
Created on Jun 6, 2013

@author: Jeff
'''
import os, sys
import numpy as np
import Image
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

class ImageView(QMdiSubWindow):

    def __init__(self, control, parent=None):
        QMdiSubWindow.__init__(self, None)
        self.setWindowTitle('Selected image')
        self.control = control
        self.imgfile = self.control.imgfile
        self.createMainFrame()
                
    def createMainFrame(self):
        self.mainFrame = QWidget()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.mainFrame)
        self.axes = self.fig.add_subplot(111)   
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.mainFrame)  
        
        self.control.imageChanged.connect(self.onImageChanged)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
                
        self.mainFrame.setLayout(vbox)
        self.setWidget(self.mainFrame)
     
    def onDraw(self):
        '''
        Shows the current RGB image
        '''
        self.axes.clear()
        if self.imgfile != None:
            img = Image.open(str(self.imgfile))
            img = np.asarray(img)
            self.axes.imshow(img)
        self.canvas.draw()

    def onImageChanged(self, imgname):
        self.imgfile = imgname
        self.onDraw()
        
        