'''
Created on Jun 4, 2013
Taken from Stack Overflow
http://stackoverflow.com/questions/6484793/multiple-files-and-folder-selection-in-a-qfiledialog/6585855#6585855

@author: Jeff
'''
import os, sys
from PyQt4.QtGui import *

class MultiDirectoryFileDialog(QFileDialog):
    def __init__(self, *args):
        QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.ExistingFiles)
        btns = self.findChildren(QPushButton)
        self.openBtn = [x for x in btns if 'open' in str(x.text()).lower()][0]
        self.openBtn.clicked.disconnect()
        self.openBtn.clicked.connect(self.openClicked)
        self.tree = self.findChild(QTreeView)
        
    def openClicked(self):
        inds = self.tree.selectionModel().selectedIndexes()
        files = []
        for i in inds:
            if i.column() == 0:
                files.append(os.path.join(str(self.directory().absolutePath()), str(i.data().toString())))
        self.selectedFiles = files
        self.hide()
        
    def filesSelected(self):
        return self.selectedFiles

if __name__ == '__main__':
    app = QApplication(sys.argv)
    fd = MultiDirectoryFileDialog()
    fd.exec_()
    dirs = fd.filesSelected()
    for i in dirs:
        print i
    app.exec_()
