'''
Created on Jun 6, 2013

@author: Jeff
'''
import os, sys
import numpy as np
import Image
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from multiDirectoryFileDialog import MultiDirectoryFileDialog
from imageView import ImageView

class TMSControl(QMainWindow):
    
    imageChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('TMS Parameter Control')
        self.imgfile = None
        
        self.createMainFrame()
        self.createImgView()
        self.createMenu()
        
    def createMainFrame(self):
        self.mainFrame = QWidget()
        self.MDI = QMdiArea()
        self.view = QListWidget()
                     
        self.view.itemDoubleClicked.connect(self.onSelect)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.view)
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
        load_action = self.create_action("&Open",
            shortcut="Ctrl+O", slot=self.onOpen, 
            tip="Open a sequence of images")
        export_action = self.create_action("&Export", slot=self.onExport,
            shortcut="Ctrl+S", tip="Export results to file")
        quit_action = self.create_action("&Quit", slot=self.close, 
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

    def onOpen(self):
        fd = MultiDirectoryFileDialog()
        fd.exec_()
        dirs = fd.filesSelected()
        self.pngs = []
        self.items = []
        for d in dirs:
            files = sorted(os.listdir(d))
            dname = os.path.basename(d) 
            for f in files:
                if f[-3:] == 'png':
                    self.pngs.append(os.path.join(d, f))
                    item = QListWidgetItem(os.path.join(dname,f))
                    item.setCheckState(Qt.Unchecked)
                    self.items.append(item)
                    self.view.addItem(item)
                
    def onExport(self):
        pass

    def onSelect(self, item):
        idx = self.items.index(item)
        self.imgfile = self.pngs[idx]
        self.imageChanged.emit(str(self.imgfile))
        
    def onAnalyze(self):
        for item in self.items:
            if bool(item.checkState()):
                print item.text()
            


        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TMSControl()
    win.show()
    app.exec_()  