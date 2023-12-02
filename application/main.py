import sys

from quof.widgets import QBaseMainWindow, QBaseApplication, QBaseMenuBar, QBaseTabWidget
from quof.utils import exception, override

from application.menubar import FileMenu

from PySide6.QtGui import QResizeEvent


class Main(QBaseMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._menu_bar = QBaseMenuBar()
        self._tabs = QBaseTabWidget(self)

        self._file = FileMenu(self._tabs)

        self._menu_bar.addMenu(self._file)

        self.setWindowIcon("resources/quof-dark.png")
        self.setMenuBar(self._menu_bar)
        self.setBackground("#202020")

    def resizeEvent(self, event: QResizeEvent) -> None:
        try:
            self._tabs.resize(self.width(), self.height() - self._menu_bar.height())
            self._tabs.move(0, self._menu_bar.height() - 2)
        except AttributeError:
            ...

        super().resizeEvent(event)


if __name__ == "__main__":
    app = QBaseApplication(sys.argv, "resources/styles/root.style", "locale")
    app.localeLoader().setLocale("ru")

    main = Main()
    main.show()

    sys.exit(app.exec())
