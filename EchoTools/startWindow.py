'''
Created on Jun 4, 2013

@author: Jeff
'''
import os, sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class StartUpWindow(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('EchoTools')
        self.datadir = ''
        self.framesBefore = 5
        self.framesAfter = 20
        self.createMainFrame()
        
    def createMainFrame(self):
        datadirLabel = QLabel("&Select data directory")
        self.datadirText = QLineEdit()
        self.datadirText.setMinimumWidth(200)
        datadirLabel.setBuddy(self.datadirText)
        self.datadirBtn = QPushButton("&Browse")
        framesBef = QLabel("Frames before onset:")
        framesAft = QLabel("Frames after onset:")
        self.framesBText = QLineEdit()
        self.framesBText.setText(str(self.framesBefore))
        self.framesAText = QLineEdit()
        self.framesAText.setText(str(self.framesAfter))
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        
        self.connect(self.datadirText, SIGNAL('editingFinished()'), self.onDataDirChanged)
        self.connect(self.datadirBtn, SIGNAL('clicked()'), self.onBrowse)
        self.connect(self.framesBText, SIGNAL('editingFinished()'), self.onFramesChanged)
        self.connect(self.framesAText, SIGNAL('editingFinished()'), self.onFramesChanged)
        self.connect(self.buttons, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttons, SIGNAL('rejected()'), self.reject)
        
        dataHBox = QHBoxLayout()
        dataHBox.addWidget(datadirLabel)
        dataHBox.addWidget(self.datadirText)
        dataHBox.addWidget(self.datadirBtn)
        framesHBox = QHBoxLayout()
        framesHBox.addWidget(framesBef)
        framesHBox.addWidget(self.framesBText)
        framesHBox.addWidget(framesAft)
        framesHBox.addWidget(self.framesAText)
        vbox = QVBoxLayout()
        vbox.addLayout(dataHBox)
        vbox.addLayout(framesHBox)
        vbox.addWidget(self.buttons)
        
        self.setLayout(vbox)
 
    def getArgs(self):
        return [self.datadir, self.framesBefore, self.framesAfter]
                
    def onDataDirChanged(self):
        datadir = self.datadirText.text()
        self.datadir = str(datadir)
        
    def onBrowse(self):
        datadir = QFileDialog.getExistingDirectory(self, caption='Choose a data directory')
        self.datadir = str(datadir)
        self.datadirText.setText(self.datadir)

    def onFramesChanged(self):
        self.framesBefore = int(str(self.framesBText.text()))
        self.framesAfter = int(str(self.framesAText.text()))

