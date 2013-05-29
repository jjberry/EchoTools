'''
Created on May 29, 2013

@author: Jeff
'''
import sys, os
from scipy.sparse.csgraph import _validation #needed for bug in pyinstaller
from PyQt4.QtGui import QApplication

from controlPanel import ControlPanel
from colorConfig import ColorConfig
from plotSignals import PlotSignals

def main():
    app = QApplication(sys.argv)
    datadir = 'c:/Users/Jeff/Desktop/shared/ALE_00/ALE_PR00-png/'
    control = ControlPanel(datadir)
    posCC = ColorConfig('Positive color filter', 10, 30, 
                        os.path.join(control.datadir, control.pngs[control.onsets[0]]),
                        control)
    negCC = ColorConfig('Negative color filter', 60, 80, 
                        os.path.join(control.datadir, control.pngs[control.onsets[0]]),
                        control)
    plotWin = PlotSignals(posCC, negCC, control)

    control.show()
    posCC.show()
    negCC.show()
    plotWin.show()

    app.exec_()

if __name__ == "__main__":
    main()
    