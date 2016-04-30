#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import shlex
import subprocess
from PyQt4 import QtGui, QtCore, uic

log = logging.getLogger('grepview')

class grepview_ui(QtGui.QMainWindow):

    def __init__(self):
        super(grepview_ui, self).__init__()
        _file_dir = os.path.dirname(os.path.realpath(__file__))
        uic.loadUi(os.path.join(_file_dir, 'grepview.ui'), self)

        self.lst_selection.selectionModel().selectionChanged.connect(
            self.on_lst_selection_selectionChanged)

        _previous = self.txt_command.keyPressEvent

        self.txt_command.keyPressEvent = (
            lambda event: grepview_ui.on_txt_command_keyPressEvent(
                self, event, _previous))

        self.setWindowTitle("command result view")

    def encode(self, item):
        try:
            return item.decode()
        except UnicodeDecodeError:
            log.error('could not decode item "%s"', item)
            return item.decode(errors='ignore')

    def on_txt_command_keyPressEvent(self, event, previous):
        if event.key() == QtCore.Qt.Key_Return:
            _command = [os.path.expanduser(e)
                        for e in shlex.split(self.txt_command.toPlainText())]
            log.info("run cmd %s" % _command)
            proc = subprocess.Popen(
                args=_command, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            _stdout, _stderr = proc.communicate()
            _result_stdout = [self.encode(e) for e in _stdout.split(b'\n')]
            _result_stderr = [self.encode(e) for e in _stderr.split(b'\n')]

            for e in _result_stderr:
                if e.strip() == '':
                    continue
                log.error(e)

            self.lst_selection.clear()
            for e in _result_stdout:
                if os.path.isfile(e):
                    self.lst_selection.addItem(e)
            return
        return previous(event)

    def on_lst_selection_selectionChanged(self):
        _items = self.lst_selection.selectedItems()
        if len(_items) == 1:
            _filename = _items[0].text()
            myPixmap = QtGui.QPixmap(_filename)
            myScaledPixmap = myPixmap.scaled(self.lbl_image.size(), QtCore.Qt.KeepAspectRatio)
            self.lbl_image.setPixmap(myScaledPixmap)
        else:
            print(len(_items))

    def on_clicked_pb_quick_play(self):
        log.debug("on_clicked_pb_quick_play")


def main():
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s:  %(message)s",
        datefmt="%y%m%d-%H%M%S",
        level=logging.INFO)
    log.info("%s %s",
             '.'.join((str(e) for e in sys.version_info)),
             sys.executable)

    app = QtGui.QApplication(sys.argv)

    ex = grepview_ui()
    ex.show()

#    for s in (signal.SIGABRT, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
#        signal.signal(s, lambda signal, frame: sigint_handler(signal, ex))

    # catch the interpreter every now and then to be able to catch signals
    timer = QtCore.QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    log.info('run Qt application')
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

