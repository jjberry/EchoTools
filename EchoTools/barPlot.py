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
        nROI = (self.control.stimval[0].shape[1])/2
        for i in range(nROI):
            stmean = []
            ststd = []
            for n in range(len(self.control.stimval)):
                stmean.extend((list(self.control.stimval[n].mean(axis=0)))[(i*2):(i*2)+2])
                ststd.extend((list(self.control.stimval[n].std(axis=0)))[(i*2):(i*2)+2])
            stmean = np.array(stmean)
            ststd = np.array(stmean)
            pos = np.arange(0, stmean.shape[0], 2)
            neg = np.arange(1, stmean.shape[0], 2)
            posrects = self.axes.bar(np.arange(pos.shape[0]), stmean[pos], 0.35, 
                                color='red', yerr=ststd[pos], bottom=i)
            negrects = self.axes.bar(np.arange(pos.shape[0])+0.35, stmean[neg], 0.35, 
                                color='blue', yerr=ststd[neg], bottom=i)
        self.axes.set_xticks(np.arange(pos.shape[0])+0.35)
        labels = []
        for i in range(len(self.control.conditions)):
            labels.append(str(self.control.conditions[i][0]))
        self.axes.set_xticklabels(labels)
        self.axes.hlines(range(nROI+1), -0.3 , stmean.shape[0]/2, color="black")
        self.axes.legend((posrects, negrects), ('Pos', 'Neg'))
        self.canvas.draw()
        