'''
Created on May 26, 2013

@author: Jeff
'''
import numpy as np
from scipy import ndimage, stats
import sys, os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import collections
import Image

def RGB2HSV(filename):
    i = Image.open(filename).convert('RGB')
    a = np.asarray(i, int)

    R, G, B = a.T

    m = np.min(a,2).T
    M = np.max(a,2).T
    
    C = M-m #chroma
    Cmsk = C!=0
    
    #Hue
    H = np.zeros(R.shape, int)
    mask = (M==R)&Cmsk
    H[mask] = np.mod(60*(G-B)/C, 360)[mask]
    mask = (M==G)&Cmsk
    H[mask] = (60*(B-R)/C + 120)[mask]
    mask = (M==B)&Cmsk
    H[mask] = (60*(R-G)/C + 240)[mask]
    H *= 180 #this controls the range of H
    H /= 360
    
    #Value
    V = M

    #Saturation
    S = np.zeros(R.shape, int)
    S[Cmsk] = ((255*C)/V)[Cmsk]

    return H.T

class ColorConfig(QMainWindow):
    plotSignal = pyqtSignal()
    def __init__(self, title, lower=2, upper=50, imgfile=None, control=None, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle(title)
        self.lower = lower
        self.upper = upper
        self.imgfile = imgfile
        self.control = control
        self.radius = 50
        valid = np.load('validinds.npy')
        self.valid = valid.reshape((600,800), order='F')
        self.notvalid = np.logical_not(self.valid)
        self.USEALL = True
        self.createMainFrame()
        self.onDraw()

    def convertImg(self, filename):
        H = RGB2HSV(filename)
        H[self.notvalid] = (np.zeros_like(H))[self.notvalid]       
        return H

    def getFiltered(self, H, lower, upper, invert=False):
        '''defaults for pos: 2-50
                        neg: 59-118
        '''
        pmask = (H>=lower)&(H<=upper)
        imgpos = np.zeros_like(H)
        imgpos[pmask] = H[pmask]
        if invert:
            rmask = imgpos>0
            imgpos[rmask] = (upper+1)-imgpos[rmask]
        
        return imgpos

    def onEdit(self):
        lower = int(self.low_text.text())
        upper = int(self.up_text.text())
        if (self.lower != lower) or (self.upper != upper):
            self.lower = lower
            self.upper = upper
            self.low_slider.setValue(self.lower)
            self.up_slider.setValue(self.upper)
            self.onDraw()

    def onSlider(self):
        self.lower = self.low_slider.value()
        self.upper = self.up_slider.value()
        self.low_text.setText(str(self.lower))
        self.up_text.setText(str(self.upper))
        self.onDraw()

    def getAveCenter(self):
        npix = len(self.valid[self.valid])
        threshold = npix * 0.1
        centers = []
        for i in range(self.control.sequence.shape[0]):
            for j in range(self.control.sequence.shape[1]):
                img = self.getFiltered(self.control.sequence[i,j,:,:], self.lower, self.upper)
                filt = len(img[img>0])
                if filt > threshold:
                    center = ndimage.measurements.center_of_mass(img)
                    center = np.array([center[0], center[1]])
                    centers.append(center)
        centers = np.array(centers)
        return centers.mean(axis=0)

    def onDraw(self):
        self.axes.clear()
        img = self.getFiltered(self.H, self.lower, self.upper, self.invert)
        if self.USEALL:
            center = self.getAveCenter()
        else:
            center = ndimage.measurements.center_of_mass(img)
        self.axes.imshow(img, cmap='gray')
        self.axes.plot(center[1], center[0], 'bx')
        self.axes.set_xlim(0,799)
        self.axes.set_ylim(0,599)
        self.axes.invert_yaxis()
        xx, yy = np.mgrid[:600, :800]
        circle = (xx-center[0])**2 + (yy-center[1])**2
        self.ROI = circle<(self.radius**2)
        self.axes.imshow(self.ROI, cmap='gray', alpha=0.2)
        self.plotSignal.emit()
        self.canvas.draw()

    def onImageChanged(self, filename):
        self.imgfile = str(filename)
        self.H = self.convertImg(self.imgfile)
        self.onDraw()
        
    def onRadiusChanged(self, radius):
        self.radius = radius
        self.onDraw()
    
    def onUseAllChecked(self):
        self.USEALL = not self.USEALL
        self.onDraw() 
        
    def createMainFrame(self):
        self.main_frame = QWidget()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.axes = self.fig.add_subplot(111)

        self.H = self.convertImg(self.imgfile)
        self.invert = False

        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        lower_label = QLabel('Lower bound:')
        upper_label = QLabel('Upper bound:')
        self.low_slider = QSlider(Qt.Horizontal)
        self.low_slider.setRange(0,179)
        self.low_slider.setValue(self.lower)
        self.low_slider.setTracking(True)
        self.low_slider.setTickPosition(QSlider.TicksBothSides)

        self.up_slider = QSlider(Qt.Horizontal)
        self.up_slider.setRange(0,179)
        self.up_slider.setValue(self.upper)
        self.up_slider.setTracking(True)
        self.up_slider.setTickPosition(QSlider.TicksBothSides)
        
        self.useAllCB = QCheckBox()
        self.useAllCB.setText("Use average over sequences")
        self.useAllCB.setChecked(True)
        self.connect(self.useAllCB, SIGNAL('stateChanged(int)'), self.onUseAllChecked)

        self.low_text = QLineEdit()
        self.low_text.setMaximumWidth(40)
        self.low_text.setText(str(self.lower))
        
        self.up_text = QLineEdit()
        self.up_text.setMaximumWidth(40)
        self.up_text.setText(str(self.upper))
        
        self.control.imageChanged.connect(self.onImageChanged)
        self.control.radiusChanged.connect(self.onRadiusChanged)
        self.control.closeSignal.connect(self.close)
        self.connect(self.low_slider, SIGNAL('valueChanged(int)'), self.onSlider)
        self.connect(self.up_slider, SIGNAL('valueChanged(int)'), self.onSlider)
        self.connect(self.low_text, SIGNAL('editingFinished()'), self.onEdit)
        self.connect(self.up_text, SIGNAL('editingFinished()'), self.onEdit)

        low_hbox = QHBoxLayout()
        low_hbox.addWidget(lower_label)
        low_hbox.addWidget(self.low_text)
        low_hbox.addWidget(self.low_slider)

        up_hbox = QHBoxLayout()
        up_hbox.addWidget(upper_label)
        up_hbox.addWidget(self.up_text)
        up_hbox.addWidget(self.up_slider)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.useAllCB)
        vbox.addLayout(low_hbox)
        vbox.addLayout(up_hbox)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

class PlotSignals(QMainWindow):
    def __init__(self, posCC, negCC, control, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Results') 
        self.posCC = posCC
        self.negCC = negCC
        self.sequence = control.sequence
        self.onset = control.onset
        self.control = control
        self.STD = True
        self.TTEST = True
        self.createMainFrame()

    def getResults(self):
        maxval = len(self.posCC.ROI[self.posCC.ROI])
        posRange = (2, 50)
        negRange = (59, 118)
        posVal1 = []
        negVal1 = []
        posVal2 = []
        negVal2 = []
        for j in range(self.sequence.shape[0]):
            cpVal1 = []
            cnVal1 = []
            cpVal2 = []
            cnVal2 = []
            for i in range(self.sequence.shape[1]):
                pmask = (self.sequence[j,i,:,:]>=posRange[0])&(self.sequence[j,i,:,:]<=posRange[1])&self.posCC.ROI
                nmask = (self.sequence[j,i,:,:]>=negRange[0])&(self.sequence[j,i,:,:]<=negRange[1])&self.posCC.ROI
                cpVal1.append(float(len(self.sequence[j,i,:,:][pmask]))/maxval)
                cnVal1.append(float(len(self.sequence[j,i,:,:][nmask]))/maxval)
                pmask = (self.sequence[j,i,:,:]>=posRange[0])&(self.sequence[j,i,:,:]<=posRange[1])&self.negCC.ROI
                nmask = (self.sequence[j,i,:,:]>=negRange[0])&(self.sequence[j,i,:,:]<=negRange[1])&self.negCC.ROI
                cpVal2.append(float(len(self.sequence[j,i,:,:][pmask]))/maxval)
                cnVal2.append(float(len(self.sequence[j,i,:,:][nmask]))/maxval)    
            posVal1.append(np.array(cpVal1))
            negVal1.append(np.array(cnVal1))
            posVal2.append(np.array(cpVal2))
            negVal2.append(np.array(cnVal2))
        posVal1 = np.array(posVal1)
        negVal1 = np.array(negVal1)
        posVal2 = np.array(posVal2)
        negVal2 = np.array(negVal2)
        
        return posVal1, negVal1, posVal2, negVal2
    
    def onDraw(self):
        self.axes.clear()
        fs = 83.0
        step = 1.0 / fs
        xt = np.arange(0, self.sequence.shape[1]*step, step)
        xt -= xt[self.onset]

        posVal1, negVal1, posVal2, negVal2 = self.getResults()
        
        self.axes.plot(xt[:posVal1.shape[1]], (posVal1.mean(axis=0))+1, 'r-')
        self.axes.plot(xt[:posVal1.shape[1]], (negVal1.mean(axis=0))+1, 'b-')
        self.axes.plot(xt[:posVal1.shape[1]], posVal2.mean(axis=0), 'r-')
        self.axes.plot(xt[:posVal1.shape[1]], negVal2.mean(axis=0), 'b-')

        if self.STD:
            self.axes.plot(xt[:posVal1.shape[1]], (posVal1.mean(axis=0))+(posVal1.std(axis=0))+1, 'r--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (posVal1.mean(axis=0))-(posVal1.std(axis=0))+1, 'r--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (negVal1.mean(axis=0))+(negVal1.std(axis=0))+1, 'b--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (negVal1.mean(axis=0))-(negVal1.std(axis=0))+1, 'b--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (posVal2.mean(axis=0))+(posVal2.std(axis=0)), 'r--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (posVal2.mean(axis=0))-(posVal2.std(axis=0)), 'r--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (negVal2.mean(axis=0))+(negVal2.std(axis=0)), 'b--', alpha=0.5)
            self.axes.plot(xt[:posVal1.shape[1]], (negVal2.mean(axis=0))-(negVal2.std(axis=0)), 'b--', alpha=0.5)

        if self.TTEST:
            t1, p1 = stats.ttest_ind(posVal1, negVal1, axis=0)
            t2, p2 = stats.ttest_ind(posVal2, negVal2, axis=0)
            collection1 = collections.BrokenBarHCollection.span_where(xt, ymin=1, ymax=2, where=p1<0.05,
                                                                  facecolor='0.5', alpha=0.25)
            self.axes.add_collection(collection1)
            collection2 = collections.BrokenBarHCollection.span_where(xt, ymin=0, ymax=1, where=p2<0.05,
                                                                  facecolor='0.5', alpha=0.25)
            self.axes.add_collection(collection2)
        
        self.axes.hlines([0,1,2], xt[0], xt[posVal1.shape[1]-1], color='black')
        self.axes.vlines(xt[self.onset], 0, 2, color='black', linewidth=2)
        self.axes.set_xlim(xt[0], xt[posVal1.shape[1]-1])    
        self.axes.set_yticks([0.5, 1.5])
        self.axes.set_yticklabels(['Neg ROI', 'Pos ROI'])
        self.axes.set_ylim(-0.25, 2.25)

        self.canvas.draw()

    def onExport(self, fname):
        posVal1, negVal1, posVal2, negVal2 = self.getResults()
        out = open(fname, 'w')
        out.write('signalName,posNeg,')
        for i in range(posVal1.shape[1]):
            out.write('v%02d,'%(i+1))
        out.write('\n')
        for sig, name in zip([posVal1, negVal1, posVal2, negVal2],
                            ['posROI_pos', 'posROI_neg', 'negROI_pos', 'negROI_neg']):
            for i in range(sig.shape[0]):
                out.write('%s,%s,'%(name, name[-3:]))
                for j in range(sig.shape[1]):
                    out.write('%0.6f,'%sig[i,j])
                out.write('\n')
        out.close()

    def onSequenceChanged(self, sequence, onset):
        self.sequence = sequence
        self.onset = onset
        self.onDraw()
    
    def onStdChecked(self):
        self.STD = not self.STD
        self.onDraw()
    
    def onTtestChecked(self):
        self.TTEST = not self.TTEST
        self.onDraw()
        
    def createMainFrame(self):
        self.main_frame = QWidget()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.axes = self.fig.add_subplot(111)

        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        self.stdCB = QCheckBox("Show standard deviation")
        self.stdCB.setChecked(True)        
        self.ttestCB = QCheckBox("Show significant difference")
        self.ttestCB.setChecked(True)

        self.posCC.plotSignal.connect(self.onDraw)
        self.negCC.plotSignal.connect(self.onDraw)
        self.control.sequenceChanged.connect(self.onSequenceChanged)
        self.control.closeSignal.connect(self.close)
        self.control.exportData.connect(self.onExport)
        self.connect(self.stdCB, SIGNAL('stateChanged(int)'), self.onStdChecked)
        self.connect(self.ttestCB, SIGNAL('stateChanged(int)'), self.onTtestChecked)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.stdCB)
        vbox.addWidget(self.ttestCB)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

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

if __name__ == "__main__":
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

