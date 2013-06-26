'''
Created on Jun 26, 2013

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

class ActivationView(QMdiSubWindow):
    def __init__(self, control, parent=None):
        QMdiSubWindow.__init__(self, parent)
        self.setWindowTitle("Activation Viewer")
        self.control = control
        self.colors = 'bgrcmy'
        self.showCenters = True
        self.showGroupCenters = False
        self.showLegend = True
        self.background = 'Grand Average'
        self.conditions = []
        for i in self.control.conditions:
            self.conditions.append(i[0])
        self.createMainFrame()
        self.processImgs()
        self.onDraw()
        
    def createMainFrame(self):
        self.mainFrame = QWidget()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.mainFrame)
        self.axes = self.fig.add_subplot(111)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.mainFrame)
        self.centersCB = QCheckBox("Show individual centers")
        self.centersCB.setCheckState(Qt.Checked)
        self.groupCentersCB = QCheckBox("Show condition centers")
        self.groupCentersCB.setCheckState(Qt.Unchecked)
        self.legendCB = QCheckBox("Show legend")
        self.legendCB.setCheckState(Qt.Checked)
        comboLabel = QLabel('View activation:')
        self.backgroundCombo = QComboBox()
        self.backgroundCombo.addItems(['Grand Average'])

        
        self.connect(self.centersCB, SIGNAL('stateChanged(int)'), self.onCentersChecked)
        self.connect(self.groupCentersCB, SIGNAL('stateChanged(int)'), self.onGroupCentersChecked)
        self.connect(self.legendCB, SIGNAL('stateChanged(int)'), self.onLegendChecked)
        self.connect(self.backgroundCombo, SIGNAL('activated(QString)'), self.onCombo)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        centersHBox = QHBoxLayout()
        centersHBox.addWidget(self.centersCB)
        centersHBox.addWidget(self.groupCentersCB)
        centersHBox.addWidget(self.legendCB)
        actHBox = QHBoxLayout()
        actHBox.addWidget(comboLabel)
        actHBox.addWidget(self.backgroundCombo)
        vbox.addLayout(centersHBox)
        vbox.addLayout(actHBox)

        self.mainFrame.setLayout(vbox)
        self.setWidget(self.mainFrame)
    
    def onCombo(self, text):
        self.background = str(text)
        self.onDraw()

    def processImgs(self):
        self.groupPxMeans = []
        for n in range(len(self.control.stimcenter)):
            self.groupPxMeans.append((np.array(self.control.stimpx[n])).mean(axis=0))
        self.grandAve = (np.array(self.groupPxMeans)).mean(axis=0)
        self.scale = np.max([self.grandAve.max(), np.abs(self.grandAve.min())])
        self.normPxMeans = []
        for n in range(len(self.control.stimcenter)):
            self.normPxMeans.append(self.groupPxMeans[n] - self.grandAve)
        items = []
        for i in range(len(self.control.conditions)):
            items.append(self.control.conditions[i][0])
            items.append(self.control.conditions[i][0]+'_Norm')
        self.backgroundCombo.addItems(items)

    def onDraw(self):
        self.axes.clear()
        self.axes.imshow(self.grandAve, vmin=-self.scale, vmax=self.scale)
        if self.showCenters:
            handlers = []
            labels = []
            for n in range(len(self.control.stimcenter)):
                color = self.colors[n%len(self.colors)]
                vals = np.array(self.control.stimcenter[n])
                hand, = self.axes.plot(vals[:,1], vals[:,0], color+'x')
                handlers.append(hand)
                labels.append(self.control.conditions[n][0])
            if self.showLegend:
                self.axes.legend(handlers, labels)
        if self.showGroupCenters:
            handlers = []
            labels = []
            for n in range(len(self.control.stimcenter)):
                color = self.colors[n%len(self.colors)]
                vals = (np.array(self.control.stimcenter[n])).mean(axis=0)
                hand, = self.axes.plot(vals[1], vals[0], color+'o')
                handlers.append(hand)
                labels.append(self.control.conditions[n][0])
            if self.showLegend:
                self.axes.legend(handlers, labels)
        self.axes.set_xlim(0,799)
        self.axes.set_ylim(0,599)
        self.axes.invert_yaxis()
        self.canvas.draw()
            

    def onCentersChecked(self):
        self.showCenters = not self.showCenters
        self.onDraw()
        
    def onGroupCentersChecked(self):
        self.showGroupCenters = not self.showGroupCenters
        self.onDraw()

    def onLegendChecked(self):
        self.showLegend = not self.showLegend
        self.onDraw()