'''
Created on Jun 25, 2013

@author: Jeff
'''
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Rgb2Hsv import RGB2HSV
from colorConfig import ColorConfig
from ROISelect import ROISelect
from maxMovement import MaxMovement
from progressWidget import ProgressWidget

class TmsROI(QMdiSubWindow):
    imageChanged = pyqtSignal(str)
    radiusChanged = pyqtSignal(int)
    sequenceChanged = pyqtSignal(np.ndarray, int)
    closeSignal = pyqtSignal()
    exportData = pyqtSignal(str)
    ROISignal = pyqtSignal()

    def __init__(self, stimfiles, tmscontrol, parent=None):
        QMdiSubWindow.__init__(self, parent)
        self.setWindowTitle('ROI Parameter control')
        self.radius = 50
        self.ROItype = ''
        self.ROIs = []
        self.stimfiles = stimfiles
        self.tmscontrol = tmscontrol

        self.processImages()
        self.createMainFrame()
        
    def createMainFrame(self):
        self.mainFrame = QWidget()
        radiusLabel = QLabel()
        radiusLabel.setText('Radius of ROI (pixels):')
        self.radiusText = QLineEdit()
        self.radiusText.setMinimumWidth(100)
        self.radiusText.setText('50')
        self.ROItypeCombo = QComboBox()
        self.ROItypeCombo.addItems(['', 'Color Interval', 'Hand Drawn', 'Maximum Movement'])
        ROItypetext = QLabel('Type of ROI:')
        self.nROItext = QLineEdit()
        self.nROItext.setMinimumWidth(50)
        self.nROItext.setText('2')
        nROItextLabel = QLabel('number of ROIs:')
        self.makeSubwins = QPushButton('Show')

        self.connect(self.radiusText, SIGNAL('editingFinished()'), self.onRadiusChanged)
        self.connect(self.ROItypeCombo, SIGNAL('activated(QString)'), self.onCombo)
        self.connect(self.makeSubwins, SIGNAL('clicked()'), self.onShow)
        
        radHBox = QHBoxLayout()
        radHBox.addWidget(radiusLabel)
        radHBox.setAlignment(radHBox, Qt.AlignVCenter)
        radHBox.addWidget(self.radiusText)
        radHBox.setAlignment(self.radiusText, Qt.AlignVCenter)
        roiHBox = QHBoxLayout()
        roiHBox.addWidget(ROItypetext)
        roiHBox.addWidget(self.ROItypeCombo)
        roiHBox.addWidget(nROItextLabel)
        roiHBox.addWidget(self.nROItext)
        vbox = QVBoxLayout()
        vbox.addLayout(radHBox)
        vbox.addLayout(roiHBox)
        vbox.addWidget(self.makeSubwins)
        
        self.mainFrame.setLayout(vbox)
        self.setWidget(self.mainFrame)
 
    def createSubWindows(self):
        #if len(self.ROIs)>0:
        #    for i in range(len(self.ROIs)):
        #        self.ROIs[i].close()
        self.ROIs = []
        for i in range(self.nROI):
            if self.ROItype == 'Color Interval':
                posCC = ColorConfig('ROI %d'%(i+1), 10, 30, self.stimfiles[0], self)
            elif self.ROItype == 'Hand Drawn' :
                posCC = ROISelect('ROI %d'%(i+1), self.stimfiles[0], self)
            elif self.ROItype == 'Maximum Movement':
                posCC = MaxMovement('ROI %d'%(i+1), self.stimfiles[0], self)
            self.ROIs.append(posCC)
            self.tmscontrol.MDI.addSubWindow(posCC)  
            self.ROIs[i].plotSignal.connect(self.onROIchanged)            
        self.tmscontrol.MDI.cascadeSubWindows()
        for i in range(self.nROI):
            self.ROIs[i].show()
        
    def processImages(self):
        thread = WorkThread(self.stimfiles)
        prog = ProgressWidget(thread)
        prog.show()
        thread.run()
        self.sequence, self.onset, self.framesBefore, self.framesAfter = thread.getVals()
        
    def onROIchanged(self):
        self.ROISignal.emit()    
        
    def onCombo(self, text):
        self.ROItype = str(text)

    def onShow(self):
        if self.ROItype != '':
            self.nROI = int(str(self.nROItext.text()))
            self.createSubWindows()
            self.ROISignal.emit()
  
    def onRadiusChanged(self):
        '''
        Changes the radius to the user specified value
        '''
        radius = int(self.radiusText.text())
        if radius != self.radius:
            if radius>0:
                self.radius = radius
                self.radiusChanged.emit(self.radius)


        
class WorkThread(QThread):
    partDone = pyqtSignal(int)
    allDone = pyqtSignal(bool)
    
    def __init__(self, filenames):
        QThread.__init__(self)
        self.filenames = filenames
            
    def run(self):
        '''
        Loads an image sequence from .png files and converts them to HSV
        #--> This is slow <--
        '''
        converted = []
        nframes = len(self.filenames)
        self.total = nframes
        for j in range(nframes):
            #print "Loading frame %d, %d of %d total" %(j, count, nframes)
            self.partDone.emit(j+1)
            H = RGB2HSV(self.filenames[j])
            converted.append(H)
        converted = np.array(converted)
        self.sequence = converted.reshape((1,converted.shape[0],converted.shape[1],converted.shape[2]))
        self.allDone.emit(True)
    
    def getVals(self):
        self.onset = self.sequence.shape[1]/2
        self.framesBefore = self.onset
        self.framesAfter = self.sequence.shape[1] - self.onset
        return self.sequence, self.onset, self.framesBefore, self.framesAfter
    