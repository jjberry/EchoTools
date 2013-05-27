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
from PIL import Image

class ROISelect(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('ROI Select')

        self.create_main_frame()

    def create_main_frame(self):
        self.main_frame = QWidget()

        self.dpi = 100
        self.fig = Figure(dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)

        self.axes = self.fig.add_subplot(111)

        img = Image.open('c:/Users/Jeff/Desktop/shared/ALE_02/test.jpg')
        img = np.asarray(img)
        self.axes.imshow(img)

        self.xys = []
        for i in range(img.shape[1]):
            for j in range(img.shape[0]):
                self.xys.append((i,j))

        self.cid = self.canvas.mpl_connect('button_press_event', self.onpress)

        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

    def callback(self, verts):
        ind = points_inside_poly(self.xys, verts)
        self.canvas.draw_idle()
        self.canvas.widgetlock.release(self.lasso)
        del self.lasso
        self.ind = ind
        np.save('c:/Users/Jeff/Desktop/shared/ALE_02/TEST_ROI.npy', self.ind)
        self.ind = self.ind.reshape((600,800), order='F')
        self.axes.imshow(self.ind, alpha=0.1, cmap='gray')

    def onpress(self, event):
        if self.canvas.widgetlock.locked(): return
        if event.inaxes is None: return
        self.lasso = Lasso(event.inaxes, (event.xdata, event.ydata), self.callback)
        self.canvas.widgetlock(self.lasso)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = ROISelect()
    form.show()
    app.exec_()

