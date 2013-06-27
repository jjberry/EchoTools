'''
Created on Jun 6, 2013

@author: Jeff
'''
import os, sys
import numpy as np
import operator
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from scipy import ndimage

from multiDirectoryFileDialog import MultiDirectoryFileDialog
from imageView import ImageView
from Rgb2Hsv import RGB2HSV
from barPlot import BarPlot
from progressWidget import ProgressWidget
from tmsROI import TmsROI
from activationView import ActivationView

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
        self.view.setColumnCount(4)
        self.view.setHeaderLabels(['Filename', 'Condition', 'TMS', 'Baseline'])
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
        save_ROI_action = self.create_action("&Save ROIs", slot=self.onSaveROIs,
            shortcut="Ctrl+R", tip="Save each ROI to a .npy file")
        load_ROI_action = self.create_action("&Load ROI",
            shortcut="Ctrl+L", slot=self.onLoadROI,
            tip="Load ROIs from files")
        export_action = self.create_action("&Export Results", slot=self.onExport,
            shortcut="Ctrl+S", tip="Export results to file")
        colormap_action = self.create_action("Export &Activations", slot=self.onExportActivations,
            shortcut="Ctrl+C", tip="Export activation images to csv files")
        quit_action = self.create_action("&Quit", slot=self.close, 
            shortcut="Ctrl+Q", tip="Close the application")
        roi_from_img_action = self.create_action("&ROI from images", slot=self.onROIfromImg,
            tip="Use TMS images to define an ROI")
        
        self.settings_menu = self.menuBar().addMenu("&Settings")
        save_settings_action = self.create_action("Save Se&ttings",
            slot=self.onSaveSettings, tip="Save check settings")
        load_settings_action = self.create_action("&Load Settings",
            slot=self.onLoadSettings, tip="Load a settings file")
        
        self.add_actions(self.file_menu, (load_action, save_ROI_action, load_ROI_action, roi_from_img_action, 
                                          None, export_action, colormap_action, None, quit_action))
        self.add_actions(self.settings_menu, (save_settings_action, load_settings_action))
        
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
            self.stimval, self.nostimval, self.conditions, self.stimfiles, self.nostimfiles, \
                self.stimpx, self.nostimpx, self.stimcenter, self.nostimcenter = thread.getVals()

    def onExportActivations(self):
        dirname = QFileDialog.getExistingDirectory(parent=self, caption="Choose a directory for export")
        dirname = str(dirname)
        if dirname != '':
            self.onCalculate()
            for n in range(len(self.stimfiles)):
                for i in range(len(self.stimfiles[n])):
                    filename = (os.path.basename(self.stimfiles[n][i]))[:-3] + 'csv'
                    np.savetxt(os.path.join(dirname, filename), self.stimpx[n][i], fmt='%d', delimiter=',')

    def onROIfromImg(self):
        stim = []
        for item in self.items:
            idx = self.items.index(item)
            if item.checkState(2) == Qt.Checked:              
                stim.append(self.pngs[idx])
        self.control = TmsROI(stim, self)
        self.MDI.addSubWindow(self.control)
        self.control.ROISignal.connect(self.onROIchanged)
        self.control.show()
    
    def onROIchanged(self):
        self.ROIs = []
        for i in range(len(self.control.ROIs)):
            self.ROIs.append(self.control.ROIs[i].ROI)
            self.ROInames.append('ROI_%d'%(i+1))
        self.imageChanged.emit(self.imgfile)
    
    def onSaveSettings(self):
        filename = QFileDialog.getSaveFileName(parent=self, caption="Choose a settings filename", filter='*.txt')
        f = open(filename, 'w')
        for item in self.items:
            idx = self.items.index(item)
            if item.checkState(2) == Qt.Checked:    
                f.write('%s,True,'%self.pngs[idx])          
            else:
                f.write('%s,False,'%self.pngs[idx])
            if item.checkState(3) == Qt.Checked:
                f.write('True\n')
            else:
                f.write('False\n')
        f.close()
    
    def onLoadSettings(self):
        filename = QFileDialog.getOpenFileName(parent=self, caption="Open a settings file", filter='*.txt')
        f = open(filename, 'r').readlines()
        basepngs = []
        for i in range(len(self.pngs)):
            basepngs.append(os.path.basename(self.pngs[i]))
        for i in range(len(f)):   
            l = f[i][:-1].split(',')
            png = l[0]
            TMS = l[1]
            try:
                baseline = l[2]
            except IndexError:
                baseline = 'False'
            if TMS == 'True':
                try:
                    idx = basepngs.index(os.path.basename(png))
                    self.items[idx].setCheckState(2, Qt.Checked)
                except ValueError:
                    pass
            if baseline == 'True':
                try:
                    idx = basepngs.index(os.path.basename(png))
                    self.items[idx].setCheckState(3, Qt.Checked)
                except ValueError:
                    pass
            
    def onLoadROI(self):
        files = QFileDialog.getOpenFileNamesAndFilter(parent=self, caption="Choose ROI files", filter='*.npy')
        self.ROIs = []
        self.ROInames = []
        for f in  list(files[0]):
            ROI = np.load(str(f))
            self.ROIs.append(ROI)
            self.ROInames.append(f[:-4])
        self.imageChanged.emit(self.imgfile)

    def onSaveROIs(self):
        for roiSel in self.ROIs:
            filename = QFileDialog.getSaveFileNameAndFilter(parent=self, caption="Choose a save file name",
                                                            filter="*.npy")
            np.save(str(filename[0]), roiSel.ROI)

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
                        item.setCheckState(2, Qt.Unchecked)
                        item.setCheckState(3, Qt.Unchecked)
                        self.items.append(item)
            self.view.setColumnWidth(0, 200)
            self.view.setColumnWidth(1, 75)
            self.view.setColumnWidth(2, 50)
            self.view.setColumnWidth(3, 50)
        except TypeError:
            pass
                    
    def onExport(self):
        filename = QFileDialog.getSaveFileName(parent=self, caption="Choose a save file name")
        self.onCalculate()
        f = open(filename, 'w')
        f.write('filename,condition,stim,center_x,center_y,')
        for i in range(0, self.stimval[0].shape[1], 2):
            f.write('ROI_%d_pos,ROI_%d_neg,'%((i/2)+1,(i/2)+1))
        f.write('\n')
        for n in range(len(self.stimval)):
            for i in range(self.stimval[n].shape[0]):
                f.write('%s,%s,stim,%0.6f,%0.6f,'%(self.stimfiles[n][i], str(self.conditions[n][0]),
                                             self.stimcenter[n][i][0],self.stimcenter[n][i][1]))
                for j in range(0, self.stimval[n].shape[1], 2):
                    f.write('%0.6f,%0.6f,'%(self.stimval[n][i,j], self.stimval[n][i,j+1]))
                f.write('\n')
        for n in range(len(self.nostimval)):
            for i in range(self.nostimval[n].shape[0]):
                f.write('%s,%s,no_stim,%0.6f,%0.6f,'%(self.nostimfiles[n][i], str(self.conditions[n][0]),
                                                self.nostimcenter[n][i][0],self.nostimcenter[n][i][1]))
                for j in range(0, self.nostimval[n].shape[1], 2):
                    f.write('%0.6f,%0.6f,'%(self.nostimval[n][i,j], self.nostimval[n][i,j+1]))
                f.write('\n')
        f.close()

    def onSelect(self, item):
        try:
            idx = self.items.index(item)
            self.imgfile = self.pngs[idx]
            self.imageChanged.emit(str(self.imgfile))
        except ValueError:
            pass
        
    def onCalculate(self):
        stim = []
        nostim = []
        for item in self.items:
            idx = self.items.index(item)
            if item.checkState(2) == Qt.Checked:              
                stim.append([self.pngs[idx], item.text(1)])
            if item.checkState(3) == Qt.Checked:
                nostim.append([self.pngs[idx], item.text(1)])
        self.getResults(stim, nostim)

    def onPlot(self):
        self.onCalculate()
        bp = BarPlot(self)
        self.MDI.addSubWindow(bp)
        bp.show()
        av = ActivationView(control=self)
        self.MDI.addSubWindow(av)
        av.show()

class WorkThread(QThread):
    partDone = pyqtSignal(int)
    allDone = pyqtSignal(bool)
    
    def __init__(self, stim, nostim, ROIs):
        QThread.__init__(self)
        self.stim = stim
        self.nostim = nostim
        self.total = len(stim)+len(nostim)
        self.ROIs = ROIs

    def convertScale(self, H):
        '''
        This takes the relevant colors on the HSV scale (determined by looking at the
        positive and negative color bars in the images) and converts them to a more
        meaningful scale, i.e. blues & greens (negative) are now in about (-1, -60) and 
        oranges & yellows (positive) in (1, 60). Other colors are zeros
        '''
        pos = (2,30)
        neg = (60,118)
        converted = np.zeros(H.shape)
        nmask = (H>=neg[0])&(H<=neg[1])
        pmask = (H>=pos[0])&(H<=pos[1])
        converted[nmask] = -(119 - H[nmask])
        converted[pmask] = H[pmask] * 2
        
        return converted

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
        stimpx = []
        stimcenter = []
        nostimval = []
        nostimfiles = []
        nostimpx = []
        nostimcenter = []    
        pos = (2, 50)
        neg = (59, 118)
        count = 0
        valid = np.load('validinds.npy')
        self.valid = valid.reshape((600,800), order='F')
        self.notvalid = np.logical_not(self.valid)        
        conditions = self.getConditions()
        for i in range(len(conditions.keys())):
            stimval.append([])
            stimfiles.append([])
            stimpx.append([])
            stimcenter.append([])
            nostimval.append([])
            nostimfiles.append([])
            nostimpx.append([])
            nostimcenter.append([])
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
            H[self.notvalid] = (np.zeros_like(H))[self.notvalid]
            center = ndimage.measurements.center_of_mass(H)
            stimcenter[conditions[f[1]]].append(center)
            converted = self.convertScale(H)
            stimpx[conditions[f[1]]].append(converted)
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
            H[self.notvalid] = (np.zeros_like(H))[self.notvalid]
            center = ndimage.measurements.center_of_mass(H)
            nostimcenter[conditions[f[1]]].append(center)
            converted = self.convertScale(H)
            nostimpx[conditions[f[1]]].append(converted)

        for i in range(len(nostimval)):
            nostimval[i] = np.array(nostimval[i])
        self.stimval = stimval 
        self.nostimval = nostimval
        self.conditions = conditions
        self.stimfiles = stimfiles
        self.nostimfiles = nostimfiles
        self.stimpx = stimpx
        self.nostimpx = nostimpx
        self.stimcenter = stimcenter
        self.nostimcenter = nostimcenter
        self.allDone.emit(True)

    def sortDict(self, dic):
        return sorted(dic.iteritems(), key=operator.itemgetter(1))
    
    def getVals(self):
        return self.stimval, self.nostimval, self.sortDict(self.conditions), self.stimfiles, self.nostimfiles, \
            self.stimpx, self.nostimpx, self.stimcenter, self.nostimcenter
                       
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TMSControl()
    win.show()
    app.exec_()  
