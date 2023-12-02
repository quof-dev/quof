import os

from application.fileeditor import FileEditor

from quof.core import QText, QBaseAction
from quof.widgets import QBaseMenu, QBaseTabWidget, QBaseApplication

from PySide6.QtWidgets import QFileDialog
from PySide6.QtPrintSupport import QPrintDialog, QPrinter


class FileMenu(QBaseMenu):
    def __init__(self, tabs: QBaseTabWidget) -> None:
        super().__init__(QText("menubar.file"))

        self._app = QBaseApplication.instance()
        self._tabs = tabs

        self._new = QBaseAction(QText("menubar.file.new"), "Ctrl+N", self._new_func)
        self._open = QBaseAction(QText("menubar.file.open"), "Ctrl+O", self._open_func)
        self._save = QBaseAction(QText("menubar.file.save"), "Ctrl+S", self._save_func)
        self._save_as = QBaseAction(QText("menubar.file.save_as"), "Ctrl+Shift+S", self._save_as_func)

        self._print = QBaseAction(QText("menubar.file.print"), None, self._print_func)
        self._settings = QBaseAction(QText("menubar.file.settings"), None, self._settings_func)

        self._exit = QBaseAction(QText("menubar.file.exit"), "Ctrl+E", self._exit_func)

        self.addAction(self._new)
        self.addAction(self._open)
        self.addAction(self._save)
        self.addAction(self._save_as)

        self.addSeparator()

        self.addAction(self._print)
        self.addAction(self._settings)

        self.addSeparator()

        self.addAction(self._exit)

    def _new_func(self) -> None:
        self._tabs.addTab(QText("tabwidget.untitled"), FileEditor())

    def _open_func(self) -> None:
        path = QFileDialog.getOpenFileName(
            self, QText.get("dialog.open_file"), "", QText.get("dialog.open_file.files")
        )[0]
        if path:
            editor = FileEditor()
            editor.loadFromFile(path)

            self._tabs.addTab(os.path.split(path)[-1], editor)

    def _save_func(self) -> None:
        tab = self._tabs.currentWidget()
        if isinstance(tab, FileEditor):
            if not (path := tab.path()):
                path = QFileDialog.getSaveFileName(
                    self, QText.get("menubar.file.save"), QText.get("tabwidget.untitled"),
                    QText.get("dialog.open_file.files")
                )[0]

            if path:
                tab.saveAs(path)

                self._tabs.setTabText(
                    self._tabs.indexOf(tab), os.path.split(path)[-1]
                )

    def _save_as_func(self) -> None:
        tab = self._tabs.currentWidget()
        if isinstance(tab, FileEditor):
            path = QFileDialog.getSaveFileName(
                self, QText.get("menubar.file.save"), QText.get("tabwidget.untitled"),
                QText.get("dialog.open_file.files")
            )[0]

            if path:
                tab.saveAs(path)

                self._tabs.setTabText(
                    self._tabs.indexOf(tab), os.path.split(path)[-1]
                )

    def _print_func(self) -> None:
        tab = self._tabs.currentWidget()
        if isinstance(tab, FileEditor):
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            if not QPrintDialog(printer, self).exec():
                return

            tab.editor().print_(printer)

    def _settings_func(self) -> None:
        ...

    def _exit_func(self) -> None:
        self._app.exit()
