'''
Created on Jun 10, 2013

@author: Jeff
'''
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class ProgressWidget(QWidget):
    def __init__(self, thread):
        QWidget.__init__(self)
        self.setWindowTitle('Processing')
        self.thread = thread
        
        self.createMainFrame()
    
    def createMainFrame(self):
        self.progress = QProgressBar()
        self.progress.setMinimum(1)
        self.progress.setMaximum(100)
        
        self.thread.partDone.connect(self.onUpdate)
        self.thread.allDone.connect(self.onFinished)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.progress)
        
        self.setLayout(vbox)
        
    def onUpdate(self, n):
        percent = float(n)/self.thread.total * 100
        self.progress.setValue(percent)
        
    def onFinished(self, done):
        if done:
            self.close()
