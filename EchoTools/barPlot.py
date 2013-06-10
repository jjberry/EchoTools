'''
Created on Jun 10, 2013

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

class BarPlot(QMdiSubWindow):

    def __init__(self, control, parent=None):
        QMdiSubWindow.__init__(self, None)
        self.setWindowTitle('TMS Results')
        self.control = control
        
        self.createMainFrame()
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


    def onDraw(self):
        self.axes.clear()
        stmean = self.control.stimval.mean(axis=0)
        ststd = self.control.stimval.std(axis=0)
        nstmean = self.control.nostimval.mean(axis=0)
        nststd = self.control.nostimval.std(axis=0)
        for i in range(0, stmean.shape[0], 2):
            posrects = self.axes.bar(np.arange(2), np.array([stmean[i],nstmean[i]]), 0.35, 
                                  color='red', yerr=np.array([ststd[i], nststd[i]]), bottom=(i/2))
            negrects = self.axes.bar(np.arange(2)+0.35, np.array([stmean[i+1],nstmean[i+1]]), 0.35, 
                                  color='blue', yerr=np.array([ststd[i+1], nststd[i+1]]), bottom=(i/2))
            self.axes.set_xticks(np.arange(2)+0.35)
            self.axes.set_xticklabels(['Stim', 'No stim'])
        self.axes.hlines(np.arange(0, stmean.shape[0], 2)/2, -0.3 , 2, color="black")
        self.axes.legend((posrects, negrects), ('Pos', 'Neg'))
        self.canvas.draw()
        