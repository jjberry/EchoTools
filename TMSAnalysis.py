'''
Created on Jun 27, 2013

@author: Jeff
'''
from EchoTools.tmsControl import TMSControl
from PyQt4.QtGui import QApplication
import sys

if __name__ == "__main__":    
    app = QApplication(sys.argv)
    win = TMSControl()
    win.show()
    app.exec_()  
