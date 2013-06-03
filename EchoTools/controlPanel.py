'''
Created on May 29, 2013

This widget controls the other widgets and allows new sequences to be loaded.

@author: Jeff Berry
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
from colorConfig import ColorConfig
from plotSignals import PlotSignals
from ROISelect import ROISelect

class ControlPanel(QMainWindow):
    '''
    A widget for controlling the ColorConfig and PlotSignal widgets.
    '''
    ###########
    # Signals #
    ###########    
    imageChanged = pyqtSignal(str)
    radiusChanged = pyqtSignal(int)
    sequenceChanged = pyqtSignal(np.ndarray, int)
    closeSignal = pyqtSignal()
    exportData = pyqtSignal(str)
    
    ########################
    # Initializing Methods #
    ########################    
    def __init__(self, datadir, parent=None):
        '''
        Initializes internal variables
        '''
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Parameter control') 
        self.datadir = datadir
        self.framesBefore = 6
        self.framesAfter = 10
        self.radius = 50
        self.getSequence()
        self.current = self.onsets[0] 
        self.ROItype = ''
        
        self.createMenu()
        self.createMainFrame()
        self.onDraw()        
        #self.createSubWindows()

    def createSubWindows(self):
        ROIs = []
        if self.ROItype == 'Functional':
            for i in range(self.nROI):
                posCC = ColorConfig('ROI %d'%(i+1), 10, 30, os.path.join(self.datadir, self.pngs[self.onsets[0]]), self)
                ROIs.append(posCC)
                self.MDI.addSubWindow(posCC)               
        elif self.ROItype == 'Anatomical' :
            for i in range(self.nROI):
                posCC = ROISelect('ROI %d'%(i+1), os.path.join(self.datadir, self.pngs[self.onsets[0]]), self)
                ROIs.append(posCC)
        plotWin = PlotSignals(ROIs, self)
        self.MDI.addSubWindow(plotWin)
        self.MDI.cascadeSubWindows()
        for i in range(self.nROI):
            ROIs[i].show()
        plotWin.show()
        
    def createMainFrame(self):
        '''
        Creates the main window
        '''
        # Widgets 
        self.main_frame = QWidget()
        self.MDI = QMdiArea()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.axes = self.fig.add_subplot(111)        
        self.fileInfo = QLabel()
        self.fileInfo.setText(os.path.join(self.datadir, self.pngs[self.current]))
        self.prevButton = QPushButton('&Previous image')
        self.nextButton = QPushButton('&Next image')
        gotoLabel = QLabel()
        gotoLabel.setText('Go to image:')
        self.gotoFile = QLineEdit()
        self.gotoFile.setMinimumWidth(100)
        self.gotoFile.setText(str(self.onsets[0]+1))
        radiusLabel = QLabel()
        radiusLabel.setText('Radius of ROI (pixels):')
        self.radiusText = QLineEdit()
        self.radiusText.setMinimumWidth(100)
        self.radiusText.setText('50')
        beforeLabel = QLabel()
        beforeLabel.setText('Frames before onset:')
        self.before = QLineEdit()
        self.before.setMinimumWidth(100)
        self.before.setText('6')
        afterLabel = QLabel()
        afterLabel.setText('Frames after onset:')
        self.after = QLineEdit()
        self.after.setMinimumWidth(100)
        self.after.setText('10')
        onsetLabel = QLabel()
        onsetLabel.setText('Onsets:')
        self.onsetText = QLineEdit()
        self.onsetText.setMinimumWidth(100)
        self.onsetText.setText(str(' '.join(map(str, list(self.onsets+1))))) 
        self.calculate = QPushButton('&Recalculate Sequence')
        self.ROItypeCombo = QComboBox()
        self.ROItypeCombo.addItems(['', 'Anatomical', 'Functional'])
        ROItypetext = QLabel('Type of ROI:')
        self.nROItext = QLineEdit()
        self.nROItext.setMinimumWidth(50)
        self.nROItext.setText('2')
        nROItextLabel = QLabel('number of ROIs:')
        self.makeSubwins = QPushButton('Show')
        
        # Connections
        self.connect(self.prevButton, SIGNAL('clicked()'), self.onPrevClicked)
        self.connect(self.nextButton, SIGNAL('clicked()'), self.onNextClicked)
        self.connect(self.gotoFile, SIGNAL('editingFinished()'), self.onGotoFile)
        self.connect(self.radiusText, SIGNAL('editingFinished()'), self.onRadiusChanged)
        self.connect(self.onsetText, SIGNAL('editingFinished()'), self.onOnsetsChanged)
        self.connect(self.calculate, SIGNAL('clicked()'), self.onSequenceChanged)
        self.connect(self.ROItypeCombo, SIGNAL('activated(QString)'), self.onCombo)
        self.connect(self.makeSubwins, SIGNAL('clicked()'), self.onShow)

        # Layouts        
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
        roiHBox = QHBoxLayout()
        roiHBox.addWidget(ROItypetext)
        roiHBox.addWidget(self.ROItypeCombo)
        roiHBox.addWidget(nROItextLabel)
        roiHBox.addWidget(self.nROItext)
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.fileInfo)
        vbox.setAlignment(self.fileInfo, Qt.AlignVCenter)
        vbox.addLayout(hbox)
        vbox.addLayout(gotoHBox)
        vbox.addLayout(onsetHBox)
        vbox.addLayout(radHBox)
        vbox.addLayout(limHBox)
        vbox.addWidget(self.calculate)
        vbox.addLayout(roiHBox)
        vbox.addWidget(self.makeSubwins)
        mainHBox = QHBoxLayout()
        mainHBox.addLayout(vbox)
        mainHBox.addWidget(self.MDI)

        self.main_frame.setLayout(mainHBox)
        self.setCentralWidget(self.main_frame)

    def createMenu(self):
        '''
        Creates the file menu
        '''
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
        '''
        Adds the actions to the file menu
        '''
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        '''
        Creates actions for the file menu
        '''
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

    #####################
    #  Internal Methods #
    #####################
    def parseOnsetFile(self, fname):
        '''
        Parses the plaintext file containing onset definitions
        '''
        f = open(fname, 'r').readlines()
        onsets = []
        for i in f:
            if i.strip() != '':
                onsets.append(int(i.strip()))
        return np.array(onsets)
    
    def getSequence(self):
        '''
        Loads an image sequence from .png files and converts them to HSV
        #--> This is slow <--
        '''
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

    #########
    # Slots #
    #########    
    def onShow(self):
        if self.ROItype != '':
            self.nROI = int(str(self.nROItext.text()))
            self.createSubWindows()
        
    def onCombo(self, text):
        self.ROItype = str(text)
    
    def onDraw(self):
        '''
        Shows the current RGB image
        '''
        self.axes.clear()
        img = Image.open(os.path.join(self.datadir, self.pngs[self.current]))
        img = np.asarray(img)
        self.axes.imshow(img)
        self.imageChanged.emit(os.path.join(self.datadir, self.pngs[self.current]))
        self.canvas.draw()

    def onPrevClicked(self):
        '''
        Changes the image to the previous in the sequence
        '''
        if self.current>0:
            self.current -= 1
            self.fileInfo.setText(os.path.join(self.datadir, self.pngs[self.current]))
            self.onDraw()

    def onNextClicked(self):
        '''
        Changes the image to the next in the sequence
        '''
        if self.current<(len(self.pngs)-1):
            self.current += 1
            self.fileInfo.setText(os.path.join(self.datadir, self.pngs[self.current]))
            self.onDraw()
            
    def onRadiusChanged(self):
        '''
        Changes the radius to the user specified value
        '''
        radius = int(self.radiusText.text())
        if radius != self.radius:
            if radius>0:
                self.radius = radius
                self.radiusChanged.emit(self.radius)

    def onSequenceChanged(self):
        '''
        Loads the new sequence and emits the sequenceChanged signal to the other widgets
        to recalculate
        '''
        before = int(self.before.text())
        after = int(self.after.text())
        if (self.framesBefore != before) or (self.framesAfter != after):
            self.framesBefore = before
            self.framesAfter = after
            self.onset = self.framesBefore
            self.getSequence()
            self.sequenceChanged.emit(self.sequence, self.onset)

    def onGotoFile(self):
        '''
        Changes the image to the one specified by the user
        '''
        newCurrent = int(self.gotoFile.text())-1
        if newCurrent != self.current:
            self.current = newCurrent
            self.fileInfo.setText(os.path.join(self.datadir, self.pngs[self.current]))
            self.onDraw()
       
    def onOnsetsChanged(self):
        '''
        Recalculates the sequence using user specified onsets
        '''
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
        '''
        Closes the application
        '''
        self.closeSignal.emit()
        self.close()

    def closeEvent(self, event):
        '''
        Closes the application when the user clicks the 'X'
        '''
        super(ControlPanel, self).closeEvent(event)
        self.onClose()

    def onExport(self):
        '''
        Shows the file dialog to get the filename for data export
        '''
        fname = QFileDialog.getSaveFileName(self, 'Choose file for export')
        if fname != '':
            self.exportData.emit(fname)
         
    def onOpenSequence(self):
        '''
        Shows the file dialog to get the directory for a new sequence
        '''
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
