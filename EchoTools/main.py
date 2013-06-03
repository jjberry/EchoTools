'''
Created on May 29, 2013

@author: Jeff Berry
'''
import sys, os
from scipy.sparse.csgraph import _validation #needed for bug in pyinstaller
from PyQt4.QtGui import QApplication, QFileDialog

from controlPanel import ControlPanel
from colorConfig import ColorConfig
from plotSignals import PlotSignals
from ROISelect import ROISelect

def main():
    app = QApplication(sys.argv)
    
    datadir = QFileDialog.getExistingDirectory(None, caption='Choose a data directory')
    datadir = str(datadir)
    control = ControlPanel(datadir)

    control.show()

    app.exec_()

if __name__ == "__main__":
    main()
    