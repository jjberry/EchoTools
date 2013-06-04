'''
Created on May 29, 2013

@author: Jeff Berry
'''
import sys, os
from scipy.sparse.csgraph import _validation #needed for bug in pyinstaller
from PyQt4.QtGui import QApplication, QFileDialog

from startWindow import StartUpWindow
from controlPanel import ControlPanel

def main():
    app = QApplication(sys.argv)
    
    startwin = StartUpWindow()
    if startwin.exec_():    
        args = startwin.getArgs()
        control = ControlPanel(args)
        control.show()

    app.exec_()

if __name__ == "__main__":
    main()
    