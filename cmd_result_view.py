#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import shlex
import subprocess
from PyQt4 import QtGui, QtCore, uic

APP_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(APP_DIR, 'submodules', 'track'))
from desktop_usage_info import applicationinfo

log = logging.getLogger('grepview')

class grepview_ui(QtGui.QMainWindow):

    def __init__(self):
        super(grepview_ui, self).__init__()
        _file_dir = os.path.dirname(os.path.realpath(__file__))
        uic.loadUi(os.path.join(_file_dir, 'grepview.ui'), self)

        self.lst_selection.selectionModel().selectionChanged.connect(
            self.on_lst_selection_selectionChanged)
        self.lst_selection.setVisible(False)
        self.set_cwd(os.getcwd())

        _previous = self.txt_command.keyPressEvent

        self.txt_command.keyPressEvent = (
            lambda event: grepview_ui.on_txt_command_keyPressEvent(
                self, event, _previous))

        self.setWindowTitle("command result view")

        self.txt_command.setText(' '.join(sys.argv[1:]))

        QtGui.QApplication.clipboard().dataChanged.connect(
            self.on_clipboard_dataChanged)
        QtGui.QApplication.clipboard().selectionChanged.connect(
            self.on_clipboard_selectionChanged)

        self._sys_icon = QtGui.QSystemTrayIcon()
        self._sys_icon.setIcon(QtGui.QIcon.fromTheme("document-save"))
        self._sys_icon.setVisible(True)
        self._sys_icon.messageClicked.connect(self.on_sys_icon_messageClicked)
        self._sys_icon.activated.connect(self.on_sys_icon_messageClicked)

    def on_sys_icon_messageClicked(self):
        print("on_sys_icon_messageClicked")
        self.setWindowState(self.windowState() &
                            ~QtCore.Qt.WindowMinimized |
                            QtCore.Qt.WindowActive)
        self.activateWindow()

    def on_clipboard_dataChanged(self):
        print("on_clipboard_dataChanged")

    def on_clipboard_selectionChanged(self):
        print("on_clipboard_selectionChanged")
        app_title = applicationinfo.get_active_window_information()['TITLE']
        if ':' not in app_title:
            return
        app_cwd = os.path.expanduser(app_title[app_title.find(':') + 1:].strip())
        log.info("got CWD: '%s'", app_cwd)

        if not QtGui.QApplication.clipboard().mimeData(mode=QtGui.QClipboard.Selection).hasText():
            return

        selection = str(QtGui.QApplication.clipboard().text(
            mode=QtGui.QClipboard.Selection))

        _filenames = []
        for line in [e.strip() for e in selection.split('\n')]:
            filename = os.path.realpath(os.path.join(app_cwd, line))
            if os.path.isfile(filename):
                _filenames.append(filename)

        if len(_filenames) == 0:
            return

        # self._sys_icon.showMessage('CRV', '\n'.join(_filenames))

        self.display(_filenames[0])

    def encode(self, item):
        try:
            return item.decode()
        except UnicodeDecodeError:
            log.error('could not decode item "%s"', item)
            return item.decode(errors='ignore')

    def set_cwd(self, path):
        os.chdir(path)
        self.lbl_cwd.setText(path)

    def on_txt_command_keyPressEvent(self, event, previous):
        if event.key() == QtCore.Qt.Key_Return:
            _command = [os.path.expanduser(e)
                        for e in shlex.split(str(self.txt_command.text()))]
            if _command == []:
                self.lst_selection.setVisible(False)
                return
            if _command[0] == 'cd':
                if len(_command) == 1:
                    self.set_cwd(os.path.expanduser('~'))
                else:
                    self.set_cwd(_command[1])
                self.txt_command.setText('')
                self.lst_selection.setVisible(False)

            log.info("run cmd %s", _command)
            proc = subprocess.Popen(
                args=_command,
                stdout=subprocess.PIPE,
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

            self.lst_selection.setVisible(self.lst_selection.count())
            return

        return previous(event)

    def on_lst_selection_selectionChanged(self):
        _items = self.lst_selection.selectedItems()
        if len(_items) == 1:
            _filename = _items[0].text()
            self.display(_filename)
        else:
            print(len(_items))

    def display(self, filename):
        myPixmap = QtGui.QPixmap(filename)
        myScaledPixmap = myPixmap.scaled(self.lbl_image.size(), QtCore.Qt.KeepAspectRatio)
        self.lbl_image.setPixmap(myScaledPixmap)


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

