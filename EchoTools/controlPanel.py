'''
Created on May 29, 2013

@author: Jeff
'''
import os
import numpy as np
import Image

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from Rgb2Hsv import RGB2HSV


class ControlPanel(QMainWindow):
    imageChanged = pyqtSignal(str)
    radiusChanged = pyqtSignal(int)
    sequenceChanged = pyqtSignal(np.ndarray, int)
    closeSignal = pyqtSignal()
    exportData = pyqtSignal(str)
    
    def __init__(self, datadir, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Parameter control') 
        self.datadir = datadir
        self.framesBefore = 6
        self.framesAfter = 10
        self.radius = 50
        self.getSequence()
        self.current = self.onsets[0] 
        
        self.createMenu()
        self.createMainFrame()
        self.onDraw()

    def parseOnsetFile(self, fname):
        f = open(fname, 'r').readlines()
        onsets = []
        for i in f:
            if i.strip() != '':
                onsets.append(int(i.strip()))
        return np.array(onsets)
    
    def getSequence(self):
        files = sorted(os.listdir(self.datadir))
        self.pngs = []
        for i in files:
            if i[-3:] == 'png':
                self.pngs.append(i)
        if os.path.isfile(os.path.join(self.datadir, 'onsets.txt')):
            self.onsets = self.parseOnsetFile(os.path.join(self.datadir, 'onsets.txt'))
        else:
            self.onsets = np.array([117, 247, 382])
        self.onset = self.framesBefore
        converted = []
        nframes = self.onsets.shape[0]*(self.framesBefore+self.framesAfter+1)
        count = 1
        for i in self.onsets:
            currentToken = []
            start = i-self.framesBefore
            end = i+self.framesAfter+1
            for j in range(start, end):
                print "Loading frame %d, %d of %d total" %(j, count, nframes)
                H = RGB2HSV(os.path.join(self.datadir, self.pngs[j]))
                currentToken.append(H)
                count += 1
            converted.append(np.array(currentToken))
        self.sequence = np.array(converted)

    def onDraw(self):
        self.axes.clear()
        img = Image.open(os.path.join(self.datadir, self.pngs[self.current]))
        img = np.asarray(img)
        self.axes.imshow(img)
        self.imageChanged.emit(os.path.join(self.datadir, self.pngs[self.current]))
        self.canvas.draw()

    def onPrevClicked(self):
        if self.current>0:
            self.current -= 1
            self.fileInfo.setText(os.path.join(self.datadir, self.pngs[self.current]))
            self.onDraw()

    def onNextClicked(self):
        if self.current<(len(self.pngs)-1):
            self.current += 1
            self.fileInfo.setText(os.path.join(self.datadir, self.pngs[self.current]))
            self.onDraw()
            
    def onRadiusChanged(self):
        radius = int(self.radiusText.text())
        if radius != self.radius:
            if radius>0:
                self.radius = radius
                self.radiusChanged.emit(self.radius)

    def onSequenceChanged(self):
        before = int(self.before.text())
        after = int(self.after.text())
        if (self.framesBefore != before) or (self.framesAfter != after):
            self.framesBefore = before
            self.framesAfter = after
            self.onset = self.framesBefore
            self.getSequence()
            self.sequenceChanged.emit(self.sequence, self.onset)

    def onGotoFile(self):
        newCurrent = int(self.gotoFile.text())-1
        if newCurrent != self.current:
            self.current = newCurrent
            self.fileInfo.setText(os.path.join(self.datadir, self.pngs[self.current]))
            self.onDraw()
       
    def onOnsetsChanged(self):
        newOnsets = np.array(map(int, str(self.onsetText.text()).split()))-1
        change = False
        for i in range(len(newOnsets)):
            if newOnsets[i] != self.onsets[i]:
                change = True
        if change:
            self.onsets = newOnsets        
            self.getSequence()
            self.sequenceChanged.emit(self.sequence, self.onset)

    def onClose(self):
        self.closeSignal.emit()
        self.close()

    def closeEvent(self, event):
        super(ControlPanel, self).closeEvent(event)
        self.onClose()

    def onExport(self):
        fname = QFileDialog.getSaveFileName(self, 'Choose file for export')
        if fname != '':
            self.exportData.emit(fname)
         
    def onOpenSequence(self):
        datadir = QFileDialog.getExistingDirectory(self, caption='Choose a data directory')
        datadir = str(datadir)
        if (datadir != '') and (datadir != self.datadir):
            self.datadir = datadir
            self.getSequence()
            self.current = self.onsets[0]
            self.fileInfo.setText(os.path.join(self.datadir, self.pngs[self.current]))
            self.onsetText.setText(str(' '.join(map(str, list(self.onsets+1)))))
            self.gotoFile.setText(str(self.onsets[0]+1))
            self.onDraw()
            self.sequenceChanged.emit(self.sequence, self.onset)
                   
    def createMenu(self):
        self.file_menu = self.menuBar().addMenu("&File")
        load_action = self.create_action("&Open",
            shortcut="Ctrl+O", slot=self.onOpenSequence, 
            tip="Open a sequence of images")
        export_action = self.create_action("&Export", slot=self.onExport,
            shortcut="Ctrl+S", tip="Export results to file")
        quit_action = self.create_action("&Quit", slot=self.onClose, 
            shortcut="Ctrl+Q", tip="Close the application")
        
        self.add_actions(self.file_menu, (load_action, export_action, None, quit_action))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def createMainFrame(self):
        self.main_frame = QWidget()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.axes = self.fig.add_subplot(111)
        
        self.fileInfo = QLabel()
        self.fileInfo.setText(os.path.join(self.datadir, self.pngs[self.current]))
        self.prevButton = QPushButton('&Previous image')
        self.connect(self.prevButton, SIGNAL('clicked()'), self.onPrevClicked)
        self.nextButton = QPushButton('&Next image')
        self.connect(self.nextButton, SIGNAL('clicked()'), self.onNextClicked)

        gotoLabel = QLabel()
        gotoLabel.setText('Go to image:')
        self.gotoFile = QLineEdit()
        self.gotoFile.setMinimumWidth(100)
        self.gotoFile.setText(str(self.onsets[0]+1))
        self.connect(self.gotoFile, SIGNAL('editingFinished()'), self.onGotoFile)
        
        radiusLabel = QLabel()
        radiusLabel.setText('Radius of ROI (pixels):')
        self.radiusText = QLineEdit()
        self.radiusText.setMinimumWidth(100)
        self.radiusText.setText('50')
        self.connect(self.radiusText, SIGNAL('editingFinished()'), self.onRadiusChanged)

        beforeLabel = QLabel()
        beforeLabel.setText('Frames before onset:')
        self.before = QLineEdit()
        self.before.setMinimumWidth(100)
        self.before.setText('6')
        self.connect(self.before, SIGNAL('editingFinished()'), self.onSequenceChanged)
        
        afterLabel = QLabel()
        afterLabel.setText('Frames after onset:')
        self.after = QLineEdit()
        self.after.setMinimumWidth(100)
        self.after.setText('10')
        self.connect(self.after, SIGNAL('editingFinished()'), self.onSequenceChanged)
        
        onsetLabel = QLabel()
        onsetLabel.setText('Onsets:')
        self.onsetText = QLineEdit()
        self.onsetText.setMinimumWidth(100)
        self.onsetText.setText(str(' '.join(map(str, list(self.onsets+1))))) 
        self.connect(self.onsetText, SIGNAL('editingFinished()'), self.onOnsetsChanged)
                
        hbox = QHBoxLayout()
        hbox.addWidget(self.prevButton)
        hbox.setAlignment(self.prevButton, Qt.AlignVCenter)
        hbox.addWidget(self.nextButton)
        hbox.setAlignment(self.nextButton, Qt.AlignVCenter)
        
        onsetHBox = QHBoxLayout()
        onsetHBox.addWidget(onsetLabel)
        onsetHBox.setAlignment(onsetLabel, Qt.AlignVCenter)
        onsetHBox.addWidget(self.onsetText)
        onsetHBox.setAlignment(self.onsetText, Qt.AlignVCenter)
        
        radHBox = QHBoxLayout()
        radHBox.addWidget(radiusLabel)
        radHBox.setAlignment(radHBox, Qt.AlignVCenter)
        radHBox.addWidget(self.radiusText)
        radHBox.setAlignment(self.radiusText, Qt.AlignVCenter)
        
        limHBox = QHBoxLayout()
        for w in [beforeLabel, self.before, afterLabel, self.after]:
            limHBox.addWidget(w)
            limHBox.setAlignment(w, Qt.AlignVCenter)
         
        gotoHBox = QHBoxLayout()
        gotoHBox.addWidget(gotoLabel)
        gotoHBox.setAlignment(gotoLabel, Qt.AlignVCenter)  
        gotoHBox.addWidget(self.gotoFile)  
        gotoHBox.setAlignment(self.gotoFile, Qt.AlignVCenter)  
   
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.fileInfo)
        vbox.setAlignment(self.fileInfo, Qt.AlignVCenter)
        vbox.addLayout(hbox)
        vbox.addLayout(gotoHBox)
        vbox.addLayout(onsetHBox)
        vbox.addLayout(radHBox)
        vbox.addLayout(limHBox)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
