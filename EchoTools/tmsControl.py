'''
Created on Jun 6, 2013

@author: Jeff
'''
import os, sys
import numpy as np
import Image
import operator
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from multiDirectoryFileDialog import MultiDirectoryFileDialog
from imageView import ImageView
from Rgb2Hsv import RGB2HSV
from barPlot import BarPlot
from progressWidget import ProgressWidget

class TMSControl(QMainWindow):
    
    imageChanged = pyqtSignal(str)
    
    def __init__(self, ROIs=None, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('TMS Parameter Control')
        self.imgfile = None
        self.ROInames = []
        if ROIs != None:
            self.ROIs = []
            for i in range(len(ROIs)):
                self.ROIs.append(ROIs[i].ROI)
                self.ROInames.append('ROI_%d'%(i+1))
        else:
            self.ROIs = []
        
        self.createMainFrame()
        self.createImgView()
        self.createMenu()
        
    def createMainFrame(self):
        self.mainFrame = QWidget()
        self.MDI = QMdiArea()
        self.view = QTreeWidget()
        self.view.setColumnCount(2)
        self.view.setHeaderLabels(['Filename', 'Condition'])
        self.view.header().setResizeMode(0, QHeaderView.Stretch)
        listLabel = QLabel('Check frames with stimulation:')
        self.showBarPlot = QPushButton('Show Results')
                     
        self.view.itemDoubleClicked.connect(self.onSelect)
        self.showBarPlot.clicked.connect(self.onPlot)
        
        vbox = QVBoxLayout()
        vbox.addWidget(listLabel)
        vbox.addWidget(self.view)
        vbox.addWidget(self.showBarPlot)
        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.MDI)
                
        self.mainFrame.setLayout(hbox)
        self.setCentralWidget(self.mainFrame)

    def createImgView(self):
        self.imgView = ImageView(self)
        self.MDI.addSubWindow(self.imgView)
        self.imgView.show()
       
    def createMenu(self):
        '''
        Creates the file menu
        '''
        self.file_menu = self.menuBar().addMenu("&File")
        load_action = self.create_action("&Open Images",
            shortcut="Ctrl+O", slot=self.onOpen, 
            tip="Open a set of image directories")
        load_ROI_action = self.create_action("&Load ROI",
            shortcut="Ctrl+L", slot=self.onLoadROI,
            tip="Load ROIs from files")
        export_action = self.create_action("&Export", slot=self.onExport,
            shortcut="Ctrl+S", tip="Export results to file")
        quit_action = self.create_action("&Quit", slot=self.close, 
            shortcut="Ctrl+Q", tip="Close the application")
        
        self.add_actions(self.file_menu, (load_action, load_ROI_action, export_action, None, quit_action))

        
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

    def getResults(self, stim, nostim):
        if self.ROIs == []:
            warn = QMessageBox.warning(self, "No ROI specified", "Warning: No ROI specified")
        else:
            thread = WorkThread(stim, nostim, self.ROIs)
            prog = ProgressWidget(thread)
            prog.show()
            thread.run()
            self.stimval, self.nostimval, self.conditions, self.stimfiles, self.nostimfiles = thread.getVals()
            
    def onLoadROI(self):
        files = QFileDialog.getOpenFileNamesAndFilter(parent=self, caption="Choose ROI files", filter='*.npy')
        self.ROIs = []
        self.ROInames = []
        for f in  list(files[0]):
            ROI = np.load(str(f))
            self.ROIs.append(ROI)
            self.ROInames.append(f[:-4])
        self.imageChanged.emit(self.imgfile)

    def onOpen(self):
        fd = MultiDirectoryFileDialog()
        fd.exec_()
        dirs = fd.filesSelected()
        self.view.clear()
        parent = self.view.invisibleRootItem()
        try:
            self.pngs = []
            self.items = []
            for d in dirs:
                files = sorted(os.listdir(d))
                dname = os.path.basename(d) 
                condition = dname.split('_')[1]
                topitem = QTreeWidgetItem(parent, [dname])
                topitem.setText(0, dname)
                topitem.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                topitem.setExpanded(True)
                for f in files:
                    if f[-3:] == 'png':
                        self.pngs.append(os.path.join(d, f))
                        item = QTreeWidgetItem(topitem, [f, condition])
                        item.setText(0, f)
                        item.setText(1, condition)
                        item.setCheckState(0, Qt.Unchecked)
                        self.items.append(item)
        except TypeError:
            pass
                    
    def onExport(self):
        filename = QFileDialog.getSaveFileName(parent=self, caption="Choose a save file name")
        self.onCalculate()
        f = open(filename, 'w')
        f.write('filename,condition,stim,')
        for i in range(0, self.stimval[0].shape[1], 2):
            f.write('ROI_%d_pos,ROI_%d_neg,'%((i/2)+1,(i/2)+1))
        f.write('\n')
        for n in range(len(self.stimval)):
            for i in range(self.stimval[n].shape[0]):
                f.write('%s,%s,stim,'%(self.stimfiles[n][i], str(self.conditions[n][0])))
                for j in range(0, self.stimval[n].shape[1], 2):
                    f.write('%0.6f,%0.6f,'%(self.stimval[n][i,j], self.stimval[n][i,j+1]))
                f.write('\n')
        for n in range(len(self.nostimval)):
            for i in range(self.nostimval[n].shape[0]):
                f.write('%s,%s,no_stim,'%(self.nostimfiles[n][i], str(self.conditions[n][0])))
                for j in range(0, self.nostimval[n].shape[1], 2):
                    f.write('%0.6f,%0.6f,'%(self.nostimval[n][i,j], self.nostimval[n][i,j+1]))
                f.write('\n')
        f.close()

    def onSelect(self, item):
        idx = self.items.index(item)
        self.imgfile = self.pngs[idx]
        self.imageChanged.emit(str(self.imgfile))
        
    def onCalculate(self):
        stim = []
        nostim = []
        for item in self.items:
            idx = self.items.index(item)
            if item.checkState(0) == Qt.Checked:              
                stim.append([self.pngs[idx], item.text(1)])
            else:
                nostim.append([self.pngs[idx], item.text(1)])
        self.getResults(stim, nostim)

    def onPlot(self):
        self.onCalculate()
        bp = BarPlot(self)
        self.MDI.addSubWindow(bp)
        bp.show()

class WorkThread(QThread):
    partDone = pyqtSignal(int)
    allDone = pyqtSignal(bool)
    
    def __init__(self, stim, nostim, ROIs):
        QThread.__init__(self)
        self.stim = stim
        self.nostim = nostim
        self.total = len(stim)+len(nostim)
        self.ROIs = ROIs

    def getConditions(self):
        conditions = {}
        for i in range(len(self.stim)):
            if conditions.has_key(self.stim[i][1]):
                conditions[self.stim[i][1]] += 1
            else:
                conditions[self.stim[i][1]] = 1
        keys = sorted(conditions.keys())
        for i in range(len(keys)):
            conditions[keys[i]] = i
        return conditions        
    
    def run(self):
        stimval = []   
        stimfiles = [] 
        nostimval = []
        nostimfiles = []    
        pos = (2, 50)
        neg = (59, 118)
        count = 0
        conditions = self.getConditions()
        for i in range(len(conditions.keys())):
            stimval.append([])
            stimfiles.append([])
            nostimval.append([])
            nostimfiles.append([])
        for f in self.stim:
            count += 1
            self.partDone.emit(count)
            current = []
            H = RGB2HSV(f[0])
            for roi in self.ROIs:
                maxval = len(roi[roi])
                posMask = (H>=pos[0])&(H<=pos[1])&roi
                negMask = (H>=neg[0])&(H<=neg[1])&roi
                current.extend([float(len(posMask[posMask]))/maxval, float(len(negMask[negMask]))/maxval])
            stimval[conditions[f[1]]].append(current)
            stimfiles[conditions[f[1]]].append(f[0])
        for i in range(len(stimval)):
            stimval[i] = np.array(stimval[i])
        for f in self.nostim:
            count += 1
            self.partDone.emit(count)
            current = []
            H = RGB2HSV(f[0])
            for roi in self.ROIs:
                maxval = len(roi[roi])
                posMask = (H>=pos[0])&(H<=pos[1])&roi
                negMask = (H>=neg[0])&(H<=neg[1])&roi
                current.extend([float(len(posMask[posMask]))/maxval, float(len(negMask[negMask]))/maxval])
            nostimval[conditions[f[1]]].append(current)
            nostimfiles[conditions[f[1]]].append(f[0])
        for i in range(len(nostimval)):
            nostimval[i] = np.array(nostimval[i])
        self.stimval = stimval 
        self.nostimval = nostimval
        self.conditions = conditions
        self.stimfiles = stimfiles
        self.nostimfiles = nostimfiles
        self.allDone.emit(True)

    def sortDict(self, dic):
        return sorted(dic.iteritems(), key=operator.itemgetter(1))
    
    def getVals(self):
        return self.stimval, self.nostimval, self.sortDict(self.conditions), self.stimfiles, self.nostimfiles
                       
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TMSControl()
    win.show()
    app.exec_()  