# -*- coding: UTF-8 -*-
__author__ = 'zhangruiqing01'

from PyQt4 import QtGui, QtCore
import cPickle
import os
import re
import pdb

UNSELECTED = False
SELECTED = True


class Sentences():
    def __init__(self, fname):
        self.data = []
        self.load_fromfile(fname)

    def load_fromfile(self, fname):
        nlines = 0
        with open(fname) as fin:
            for line in fin:
                if line.startswith("**********"):
                    continue
                else:
                    try:
                        self.data.append(self.split_line(line.strip()))
                        nlines += 1
                    except:
                        pass
            print 'num of lines:', nlines

    def split_line(self, line):
        res =  re.split("。|，|！|？", line)
        return [x.decode('utf-8') for x in res]


class ShinningQlabel(QtCore.QObject):
    def __init__(self, parent, strcontent):
        super(ShinningQlabel, self).__init__(parent)
        self.labelwidget = QtGui.QLabel()
        self.labelwidget.installEventFilter(self)
        self.labelwidget.setMouseTracking(True)
        self.status = UNSELECTED
        self.labelwidget.setText(strcontent)

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.MouseMove:
            self.render_bgcolor('#FFEC8B') # yellow
            return True
        elif event.type() == QtCore.QEvent.Leave: # mouse leave
            if self.status == SELECTED:
                self.render_bgcolor('#ADFF2F') # light green
            else:
                self.render_bgcolor('#EAEAEA')
        if event.type() == QtCore.QEvent.MouseButtonRelease: # mouse click down
            self.status = not self.status
            if self.status:
                self.render_bgcolor('#ADFF2F') # light green
            else:
                self.render_bgcolor('#EAEAEA') # gray
        return False

    def render_fontcolor(self, color):
        self.labelwidget.setStyleSheet('color:' + color)

    def render_bgcolor(self, color):
        self.labelwidget.setStyleSheet('background-color:' + color)

    def initial_render(self):
        if self.status == SELECTED:
            self.render_bgcolor('#ADFF2F') # light green


class OneSentenceLabels(QtGui.QWidget):
    def __init__(self, oneSentence):
        QtGui.QWidget.__init__(self)
        assert type(oneSentence) == list
        self.subsenQlabelList = []
        for str_subsentence in oneSentence:
            subsenQlabel = ShinningQlabel(self, str_subsentence)
            self.subsenQlabelList.append(subsenQlabel.labelwidget)


class Window(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout(self)

        # Load data and initialize QLabels
        self.sentences = Sentences('data/1.1.txt')
        self.sentence_QLabels = []
        self.sentence_QList = QtGui.QListWidget(self)
        for i in xrange(len(self.sentences.data)):
            item = QtGui.QListWidgetItem("item %i" % i)
            self.sentence_QList.addItem(item)
            one_sentence_qlabels = self.build_onesentence_labels(self.sentences.data[i]) # record QLabels of one sample
            self.sentence_QLabels.append(one_sentence_qlabels) # record QLabels of all samples, 2d-array
            for each_sentence_qlabel in one_sentence_qlabels:
                self.layout.addWidget(each_sentence_qlabel.labelwidget)
        self.sentence_QList.itemClicked.connect(self.choose_element)
        self.sentence_QList.itemDoubleClicked.connect(self.clear_annotation)
        self.doubleclick_notclick = False
        self.last_sentence_qlabels = []

        # Initialize window layout
        self.button = QtGui.QPushButton('Save and Next', self)
        self.button.clicked.connect(self.handleButton)

        self.layout.addWidget(self.button)
        self.layout.addWidget(self.sentence_QList)

        self.visited = [False] * len(self.sentences.data)

        # Meta files
        self.annotation = []
        self.data_visited = 'data/visited.pkl'
        self.data_choose = 'data/annotation.pkl'
        self.load_meta()

    def build_onesentence_labels(self, oneSentence):
        assert type(oneSentence) == list
        subsenQlabelList = []
        for str_subsentence in oneSentence:
            subsenQlabel = ShinningQlabel(self, str_subsentence)
            subsenQlabel.labelwidget.setHidden(True)
            subsenQlabelList.append(subsenQlabel)
        return subsenQlabelList

    def handleButton(self):
        currentRow = self.sentence_QList.currentRow()
        self.sentence_QList.setCurrentRow(currentRow + 1)
        self.choose_element(self.sentence_QList.currentItem())

    def choose_element(self, item):
        if self.doubleclick_notclick:
            self.doubleclick_notclick = False
            return
        # remove old QLabels
        for i in xrange(len(self.last_sentence_qlabels)):
            self.last_sentence_qlabels[i].setHidden(True)
            #self.layout.removeWidget(self.last_sentence_qlabels[i])
            #self.last_sentence_qlabels[i].deleteLater()
            #self.last_sentence_qlabels[i] = None
        # load new QLabels
        print self.visited
        current_row = self.sentence_QList.currentRow()
        current_sentence_qlabels =  self.sentence_QLabels[current_row]
        item.setBackgroundColor(QtGui.QColor('#93e7f6')) # blue
        self.last_sentence_qlabels = []
        for i in xrange(len(current_sentence_qlabels)):
            self.last_sentence_qlabels.append(current_sentence_qlabels[i].labelwidget)
            #if current_visited:
            self.last_sentence_qlabels[i].setHidden(False)
            #else:
            #    self.layout.addWidget(self.last_sentence_qlabels[i])
        self.visited[current_row] = True

    def clear_annotation(self):
        currentRow = self.sentence_QList.currentRow()
        print 'double clicked ...' + str(currentRow)
        self.visited[currentRow] = False
        item = self.sentence_QList.currentItem()
        item.setBackgroundColor(QtGui.QColor('#EAEAEA')) #gray
        self.doubleclick_notclick = True # avoid trigger click event again
        print self.visited

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtGui.QMessageBox.question(self, 'Message',
                 quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            event.accept()
            self.save_meta()
        else:
            event.ignore()

    def load_meta(self):
        if os.path.exists(self.data_choose) and \
           os.path.exists(self.data_visited):
            print('Loading from Meta files')
            with open(self.data_choose) as fc:
                self.annotation = cPickle.load(fc)
                for i in xrange(len(self.annotation)):
                    for j in xrange(len(self.annotation[i])):
                        self.sentence_QLabels[i][j].status = self.annotation[i][j]
                        self.sentence_QLabels[i][j].initial_render()
            with open(self.data_visited) as fv:
                self.visited = cPickle.load(fv)
                print self.visited
                for i in xrange(len(self.visited)):
                    item = self.sentence_QList.item(i)
                    if self.visited[i]:
                        item.setBackgroundColor(QtGui.QColor("#93e7f6"))

    def save_meta(self):
        self.annotation = []
        for i in xrange(len(self.sentences.data)):
            self.annotation.append([])
            for j in xrange(len(self.sentences.data[i])):
                self.annotation[i].append(self.sentence_QLabels[i][j].status)
        with open(self.data_visited, 'w') as fv, \
                open(self.data_choose, 'w') as fc:
            print('Saving to Meta files')
            print self.visited
            cPickle.dump(self.visited, fv)
            cPickle.dump(self.annotation, fc)


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
