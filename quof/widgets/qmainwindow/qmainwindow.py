import sys
import time

import winreg

import win32api
import win32con
import win32gui
import win32print

from .qwindoweffects import QWindowsEffects
from .qwindowresources import getIcons

from win32comext.shell import shellcon

from ctypes import Structure, c_int, POINTER, windll, byref, sizeof, cast
from ctypes.wintypes import DWORD, HWND, UINT, RECT, LPARAM, MSG, LPRECT

from PySide6.QtCore import (QEvent, QObject, QTimer, QPoint, QSize,
                            QSettings, Qt, Signal)
from PySide6.QtGui import (QGuiApplication, QPainter, QIcon,
                           QPixmap, QCursor, QWindow, QPaintEvent,
                           QResizeEvent, QMoveEvent, QMouseEvent,
                           QEnterEvent, QCloseEvent)
from PySide6.QtWidgets import (QWidget, QToolButton, QLabel, QMenuBar,
                               QGraphicsOpacityEffect, QApplication)


class APPBARDATA(Structure):
    _fields_ = [
        ("cbSize",           DWORD),
        ("hWnd",             HWND),
        ("uCallbackMessage", UINT),
        ("uEdge",            UINT),
        ("rc",               RECT),
        ("lParam",           LPARAM)
    ]


class PWINDOWPOS(Structure):
    _fields_ = [
        ("hWnd",            HWND),
        ("hwndInsertAfter", HWND),
        ("x",               c_int),
        ("y",               c_int),
        ("cx",              c_int),
        ("cy",              c_int),
        ("flags",           UINT)
    ]


class NCCALCSIZE_PARAMS(Structure):
    _fields_ = [
        ("rgrc",  RECT * 3),
        ("lppos", POINTER(PWINDOWPOS))
    ]


LPNCCALCSIZE_PARAMS = POINTER(NCCALCSIZE_PARAMS)


def monitorInfo(hwnd: int, flags: int) -> dict:
    """ Returns a dictionary with information about the monitor the application is on. """

    monitor = win32api.MonitorFromWindow(hwnd, flags)
    if monitor:
        return win32api.GetMonitorInfo(monitor)


def findWindow(hwnd: int) -> QWindow | None:
    """ Returns the current window. """

    if not hwnd:
        return

    windows = QGuiApplication.topLevelWindows()
    if not windows:
        return

    for window in windows:
        if window and window.winId() == hwnd:
            return window


def getDpiForWindow(hwnd: int, horizontal: bool = True) -> int:
    if hasattr(windll.user32, "GetDpiForWindow"):
        return windll.user32.GetDpiForWindow(hwnd)

    if not (hdc := win32gui.GetDC(hwnd)):
        return 96

    dpi_x = win32print.GetDeviceCaps(hdc, win32con.LOGPIXELSX)
    dpi_y = win32print.GetDeviceCaps(hdc, win32con.LOGPIXELSY)

    win32gui.ReleaseDC(hwnd, hdc)

    if dpi_x > 0 and horizontal:
        return dpi_x
    elif dpi_y > 0 and not horizontal:
        return dpi_y

    return 96


def getSystemMetrics(hwnd: int, index: int, horizontal: bool) -> int:
    if not hasattr(windll.user32, "GetSystemMetricsForDpi"):
        return win32api.GetSystemMetrics(index)

    return windll.user32.GetSystemMetricsForDpi(
        index,  getDpiForWindow(hwnd, horizontal)
    )


def resizeBorderThickness(hwnd: int) -> int:
    """ Returns the factor for resizing the window. """

    window = findWindow(hwnd)
    if not window:
        return 0

    # frame = win32con.SM_CXSIZEFRAME if horizontal else win32con.SM_CYSIZEFRAME
    # result = getSystemMetrics(hwnd, frame, horizontal) + getSystemMetrics(hwnd, 92, horizontal)
    result = win32api.GetSystemMetrics(win32con.SM_CXSIZEFRAME) + win32api.GetSystemMetrics(92)

    if result > 0:
        return result

    windll.dwmapi.DwmIsCompositionEnabled(byref(c_int(0)))

    return round((8 if bool(c_int(0).value) else 4) * window.devicePixelRatio())


def invertColor(color: str) -> str:
    """ Invert hex color. """

    inverted = ""
    for index in range(0, 5, 2):
        channel = int(color[index:index + 2], base=16)
        inverted += hex(round(channel / 6))[2:].upper().zfill(2)

    inverted += color[-2:]

    return inverted


def isMaximized(hwnd: int) -> bool:
    """ Checks if the window is maximized. """

    placement = win32gui.GetWindowPlacement(hwnd)
    if placement:
        return placement[1] == win32con.SW_MAXIMIZE
    return False


def isFullscreen(hwnd: int) -> bool:
    """ Checks if the window is fullscreen. """

    if not hwnd:
        return False

    win_rect = win32gui.GetWindowRect(hwnd)
    if not win_rect:
        return False

    monitor_info = monitorInfo(hwnd, win32con.MONITOR_DEFAULTTOPRIMARY)
    if not monitor_info:
        return False

    monitor_rect = monitor_info["Monitor"]

    return all(win_coord == monitor_cord for win_coord, monitor_cord in zip(win_rect, monitor_rect))


def isSystemDarkTheme() -> bool:
    """ Returns the system theme. """

    with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    ) as registry:

        value, regtype = winreg.QueryValueEx(registry, r"AppsUseLightTheme")

    return not value


class QTaskbar(object):
    """ Base class for interacting with the Windows taskbar. """

    TOP = 1
    RIGHT = 2
    BOTTOM = 3
    LEFT = 0

    NO_POSITION = 4

    AUTO_HIDE_THICKNESS = 2

    @staticmethod
    def isAutoHide() -> bool:
        """ Gets information about auto-hiding of the taskbar. """

        appbar_data = APPBARDATA(
            sizeof(APPBARDATA), 0, 0, 0, RECT(0, 0, 0, 0), 0
        )
        taskbar_state = windll.shell32.SHAppBarMessage(
            shellcon.ABM_GETSTATE, byref(appbar_data)
        )

        return taskbar_state == shellcon.ABS_AUTOHIDE

    @classmethod
    def getPosition(cls, hwnd: int) -> int:
        """ Gets information about the position of the taskbar on the screen. """

        monitor_info = monitorInfo(
            hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        if not monitor_info:
            return cls.NO_POSITION

        monitor = RECT(*monitor_info["Monitor"])
        appbar = APPBARDATA(sizeof(APPBARDATA), 0, 0, 0, monitor, 0)
        for position in (cls.LEFT, cls.TOP, cls.RIGHT, cls.BOTTOM):
            appbar.uEdge = position

            if windll.shell32.SHAppBarMessage(11, byref(appbar)):
                return position

        return cls.NO_POSITION


class QCustomWindowError(Exception):
    """ Base class of exceptions that can be thrown due to incorrectly specified values. """

    MicaAvailableError = "The current system does not support the mica effect!"
    UndefinedStyleError = "Failed to determine the selected style!"
    UndefinedThemeError = "Failed to determine the selected theme!"


class QCustomBase(QWidget):
    """ Base class that creates a bare window with no system frame. """

    sizeChanged = Signal(QSize)
    posChanged = Signal(QPoint)

    class Theme(object):
        """ Supported Themes. """

        System: None = 0x0001
        Light: None = 0x0002
        Dark: None = 0x0003

    class Style(object):
        """ Supported Styles. """

        NoStyle: None = 0x0004
        UseMica: None = 0x0005
        UseMicaIfAvailable: None = 0x0006
        UseAcrylic: None = 0x0007

    def __init__(self, theme: int = 0x0001, style: int = 0x0004, *, flags: int = None) -> None:
        """ Window initialization """

        super().__init__(parent=None)

        self._fix_acrylic = False

        self._mica_available = sys.getwindowsversion().build >= 22000  # mica only supported on Windows 11
        self._acrylic_available = sys.getwindowsversion().build >= 19042  # acrylic only supported on Windows 10
        if style == QCustomBase.Style.UseAcrylic and not self._mica_available:
            raise QCustomWindowError(QCustomWindowError.MicaAvailableError)

        if style not in [QCustomBase.Style.NoStyle, QCustomBase.Style.UseMica,
                         QCustomBase.Style.UseMicaIfAvailable, QCustomBase.Style.UseAcrylic]:
            raise QCustomWindowError(QCustomWindowError.UndefinedStyleError)

        if theme not in [QCustomBase.Theme.System, QCustomBase.Theme.Light, QCustomBase.Theme.Dark]:
            raise QCustomWindowError(QCustomWindowError.UndefinedThemeError)

        if style == QCustomBase.Style.NoStyle:
            self._mica_effect = False
            self._acrylic_effect = False
        elif style == QCustomBase.Style.UseMica:
            self._mica_effect = True
            self._acrylic_effect = False
        elif style == QCustomBase.Style.UseMicaIfAvailable:
            self._mica_effect = self._mica_available
            self._acrylic_effect = False
        elif style == QCustomBase.Style.UseAcrylic:
            self._mica_effect = False
            self._acrylic_effect = True

        if theme == QCustomBase.Theme.System:
            self._is_dark = isSystemDarkTheme()
        elif theme == QCustomBase.Theme.Light:
            self._is_dark = False
        elif theme == QCustomBase.Theme.Dark:
            self._is_dark = True

        self._color = "282828A0" if self._is_dark else "F0F0F0A0"

        self._effects_enabled = False
        self._effects = QWindowsEffects()
        self._effects.addWindowAnimation(int(self.winId()))

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | flags if flags is not None else Qt.WindowType.FramelessWindowHint
        )

        self._effects.addWindowAnimation(int(self.winId()))

        self.setEffects()
        if self._mica_available:
            self._effects.addBlurBehindWindow(int(self.winId()))
            self._effects.addShadowEffect(int(self.winId()))

        self.setStyleSheet("QCustomBase { background: transparent; }")

        self._effects_timer = QTimer(self)
        self._effects_timer.setInterval(100)
        self._effects_timer.setSingleShot(True)
        self._effects_timer.timeout.connect(self.setEffects)

    def isDarkTheme(self) -> bool:
        return self._is_dark

    def isWindows11(self) -> bool:
        """ Is the version of Windows it 11. """

        return self._mica_available

    def isWindows10(self) -> bool:
        """ Is the version of Windows it 10. """

        return self._acrylic_effect

    def setEffects(self, enabled: bool = True) -> None:
        """ Function that specifies the selected effect. """

        if enabled == self._effects_enabled:
            return

        self._effects_enabled = enabled
        if enabled and self._mica_effect:
            self._effects.addMicaEffect(int(self.winId()), self._is_dark)
        elif enabled and self._acrylic_effect:
            self._effects.addAcrylicEffect(int(self.winId()), self._color)
        else:
            self._effects.removeBackgroundEffect(int(self.winId()))

        self.update()

    def setAcrylicFixerEnabled(self, state: bool) -> None:
        """ Suspends the program process when the window is resized
            (Acrylic effect has a bug where the window does not keep up with the cursor). """

        self._fix_acrylic = state

    def temporaryDisableEffect(self) -> None:
        """ Temporarily disable and then enable window effects. """

        if self._acrylic_effect:
            if self._fix_acrylic:
                self.setEffects(False)

                self._effects_timer.stop()
                self._effects_timer.start()
            else:
                time.sleep(0.001)

    def setDarkMode(self, state: bool) -> None:
        """ Sets the window theme """

        self._is_dark = state
        self._color = invertColor(self._color)

        self.temporaryDisableEffect()

    def paintEvent(self, event: QPaintEvent) -> None:
        """ Window paint event. """

        # Basic frame rendering.
        if self._effects_enabled:
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setOpacity(0.75)

        if self._is_dark:
            painter.setBrush(Qt.GlobalColor.black)
        else:
            painter.setBrush(Qt.GlobalColor.white)

        painter.drawRect(self.rect())

    def resizeEvent(self, event: QResizeEvent) -> None:
        """ Window resize event. """

        super().resizeEvent(event)

        self.sizeChanged.emit(self.size())

    def moveEvent(self, event: QMoveEvent) -> None:
        """ Window move event. """

        if self._mica_available or not self._effects_timer:
            return super().moveEvent(event)

        self.temporaryDisableEffect()
        self.posChanged.emit(self.pos())

    def nativeEvent(self, event: bytes, message: int) -> object:
        """ Window native event. """

        # Native event for window resizing via win32api.
        msg = MSG.from_address(int(message))

        if not msg.hWnd:
            return False, 0

        if msg.message == win32con.WM_NCCALCSIZE:
            if msg.wParam:
                rect = cast(msg.lParam, LPNCCALCSIZE_PARAMS).contents.rgrc[0]
            else:
                rect = cast(msg.lParam, LPRECT).contents

            is_max = isMaximized(msg.hWnd)  # noqa
            is_full = isFullscreen(msg.hWnd)  # noqa

            if is_max and not is_full:
                thickness = resizeBorderThickness(msg.hWnd)  # noqa

                rect.top += thickness
                rect.left += thickness
                rect.right -= thickness
                rect.bottom -= thickness

            if (is_max or is_full) and QTaskbar.isAutoHide():
                position = QTaskbar.getPosition(msg.hWnd)  # noqa

                if position == QTaskbar.TOP:
                    rect.top += QTaskbar.AUTO_HIDE_THICKNESS
                elif position == QTaskbar.BOTTOM:
                    rect.bottom -= QTaskbar.AUTO_HIDE_THICKNESS
                elif position == QTaskbar.LEFT:
                    rect.left += QTaskbar.AUTO_HIDE_THICKNESS
                elif position == QTaskbar.RIGHT:
                    rect.right -= QTaskbar.AUTO_HIDE_THICKNESS

            return True, (0 if not msg.wParam else win32con.WVR_REDRAW)

        return False, 0


class QTitleBarButton(QToolButton):
    """ Base class for creating a window title bar button. """

    class State(object):
        Normal: None = 0x0008
        Hovered: None = 0x0009
        Pressed: None = 0x0010

    def __init__(self, parent: QWidget, is_dark: bool = False, btn_enabled: bool = True) -> None:
        """ Button initialization. """

        super().__init__(parent=parent)

        self._state = QTitleBarButton.State.Normal

        self._is_dark = is_dark
        self._btn_enabled = btn_enabled

        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(1.0)

        self._color = "FFFFFF" if self._is_dark else "000000"
        self._colors = {
            0x0008: f"transparent",
            0x0009: f"#20{self._color}",
            0x0010: f"#40{self._color}"
        }

        self._style = """
        QTitleBarButton {{
            background: {};
            border: none;
            border-radius: 0px;
            margin: 0px;
        }}
        """

        self.setFixedSize(QSize(46, 32))
        self.setState(QTitleBarButton.State.Normal)
        self.setGraphicsEffect(self._effect)

        self.isEnabled()

    def state(self) -> int:
        """ Button state. """

        return self._state

    def buttonEnabled(self) -> bool:
        """ Button is enabled. """

        return self._btn_enabled

    def setColors(self, hovered: str, pressed: str) -> None:
        """ Sets the button colors. """

        self._colors[0x0009] = hovered
        self._colors[0x0010] = pressed

    def setState(self, state: int) -> None:
        """ Set the button state. """

        self._state = state

        self.setStyleSheet(
            self._style.format(self._colors[state])
        )

    def setButtonEnabled(self, state: bool) -> None:
        """ Sets the button state. """

        self._btn_enabled = state

        self.setEnabled(self._btn_enabled)
        if not state:
            self._effect.setOpacity(0.35)
        else:
            self._effect.setOpacity(1.0)

    def setActiveMode(self, state: bool) -> None:
        """ Sets the button active mode. """

        if not state:
            self._effect.setOpacity(0.65 if self._btn_enabled else 0.35)
        else:
            self._effect.setOpacity(1.0)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.setState(QTitleBarButton.State.Hovered)

        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.setState(QTitleBarButton.State.Normal)

        return super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setState(QTitleBarButton.State.Pressed)

        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.setState(QTitleBarButton.State.Hovered)

        return super().mouseReleaseEvent(event)


class QMinimizeButton(QTitleBarButton):
    """ Base class for creating a window minimize title bar button. """

    def __init__(self, parent: QWidget, is_dark: bool = False) -> None:
        """ Button initialization. """

        super().__init__(parent=parent, is_dark=is_dark)

        self._minimize_pixmap = QPixmap()
        self._minimize_pixmap.loadFromData(
            getIcons(self._is_dark)["minimize"]
        )

        self.setIcon(QIcon(self._minimize_pixmap))
        self.setIconSize(QSize(45, 19))

    def setDarkMode(self, state: bool) -> None:
        """ Sets the button dark/light theme. """

        self._is_dark = state

        self._minimize_pixmap = QPixmap()
        self._minimize_pixmap.loadFromData(
            getIcons(self._is_dark)["minimize"]
        )

        self.setIcon(QIcon(self._minimize_pixmap))
        self.setIconSize(QSize(45, 19))


class QMaximizeButton(QTitleBarButton):
    """ Base class for creating a window maximize/restore title bar button. """

    def __init__(self, parent: QWidget, is_dark: bool = False) -> None:
        """ Button initialization. """

        super().__init__(parent=parent, is_dark=is_dark)

        self._maximize_pixmap = QPixmap()
        self._maximize_pixmap.loadFromData(
            getIcons(self._is_dark)["maximize"]
        )
        self._restore_pixmap = QPixmap()
        self._restore_pixmap.loadFromData(
            getIcons(self._is_dark)["restore"]
        )

        self.setIcon(QIcon(self._maximize_pixmap))
        self.setIconSize(QSize(45, 19))

    def restate(self) -> None:
        """ Changes the button icon depending on the state of the window. """

        if self.window().isMaximized():
            self.setIcon(QIcon(self._restore_pixmap))
        else:
            self.setIcon(QIcon(self._maximize_pixmap))

        self.setIconSize(QSize(45, 19))

    def setDarkMode(self, state: bool) -> None:
        """ Sets the button dark/light theme. """

        self._is_dark = state

        self._maximize_pixmap = QPixmap()
        self._maximize_pixmap.loadFromData(
            getIcons(self._is_dark)["maximize"]
        )
        self._restore_pixmap = QPixmap()
        self._restore_pixmap.loadFromData(
            getIcons(self._is_dark)["restore"]
        )

        self.restate()
        self.setIconSize(QSize(45, 19))


class QCloseButton(QTitleBarButton):
    """ Base class for creating a window close title bar button. """

    def __init__(self, parent: QWidget, is_dark: bool = False) -> None:
        """ Button initialization. """

        super().__init__(parent=parent, is_dark=is_dark)

        self._close_light_pixmap = QPixmap()
        self._close_light_pixmap.loadFromData(
            getIcons(False)["close"]
        )
        self._close_dark_pixmap = QPixmap()
        self._close_dark_pixmap.loadFromData(
            getIcons(True)["close"]
        )

        self.setIcon(QIcon(
            self._close_dark_pixmap if self._is_dark else self._close_light_pixmap
        ))
        self.setIconSize(QSize(45, 19))
        self.setColors(
            hovered="#C42B1C", pressed="#C83C30"
        )

    def setDarkMode(self, state: bool) -> None:
        """ Sets the button dark/light theme. """

        self._is_dark = state

        self.setIcon(QIcon(
            self._close_dark_pixmap if self._is_dark else self._close_light_pixmap
        ))

    def enterEvent(self, event: QEnterEvent) -> None:
        """ Close button enter event. """

        # Changes icon color on hover.
        if self._is_dark:
            return super().enterEvent(event)

        self.setIcon(QIcon(self._close_dark_pixmap))

        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """ Close button leave event. """

        # Changes icon color on leave.
        if self._is_dark:
            return super().leaveEvent(event)

        self.setIcon(QIcon(self._close_light_pixmap))

        return super().leaveEvent(event)


class QBackground(QWidget):
    """ Base class for creating a window background. """

    def __init__(self, parent: QWidget) -> None:
        """ Frame initialization. """

        super().__init__(parent=parent)


class QTitleBar(QWidget):
    """ Base class for creating a window custom title bar. """

    def __init__(self, parent: QWidget, is_dark: bool = False) -> None:
        """ Title bar initialization. """

        super().__init__(parent=parent)

        self._icon = QLabel(self)
        self._icon.resize(QSize(16, 16))

        self._title = QLabel(self)

        self._min_button = QMinimizeButton(self)
        self._max_button = QMaximizeButton(self)
        self._close_button = QCloseButton(self)

        self._min_button.clicked.connect(self.window().showMinimized)
        self._max_button.clicked.connect(self.toggleMaxState)
        self._close_button.clicked.connect(self.window().close)

        self._menu_bar = None
        self._title_frame = QWidget(self)

        self.setFixedHeight(32)
        self.setDarkMode(is_dark)

    def minimizeButton(self) -> QMinimizeButton:
        return self._min_button

    def maximizeButton(self) -> QMaximizeButton:
        return self._max_button

    def closeButton(self) -> QCloseButton:
        return self._close_button

    def toTop(self) -> None:
        """ Brings the main window title bar widgets on top of other widgets. """

        self._icon.raise_()
        self._title.raise_()

        self._min_button.raise_()
        self._max_button.raise_()
        self._close_button.raise_()

    def toggleMaxState(self) -> None:
        """ Changes the state of the window to the opposite of the current one. """

        if not self._max_button.buttonEnabled():
            return

        if self.window().isMaximized():
            self.window().showNormal()
        else:
            self.window().showMaximized()

        self._max_button.restate()

    def updateMaxButton(self) -> None:
        """ Update the maximize/restore button depending on the state of the window. """

        self._max_button.restate()

    def setIcon(self, icon: QIcon) -> None:
        """ Sets an icon for a window. """

        self._icon.resize(QSize(16, 16))
        self._icon.setPixmap(icon.pixmap(QSize(16, 16)))

    def setTitle(self, title: str) -> None:
        """ Sets a title for a window """

        self._title.setText(title)

    def setIconVisibility(self, state: bool) -> None:
        """ Hides/shows the icon. """

        if state:
            self._icon.show()
        else:
            self._icon.hide()

    def setTitleVisibility(self, state: bool) -> None:
        """ Hides/shows the title. """

        if state:
            self._title.show()
        else:
            self._title.hide()

    def setDarkMode(self, state: bool) -> None:
        """ Sets the title bar dark/light theme. """

        if state:
            self._title.setStyleSheet("color: white;")
        else:
            self._title.setStyleSheet("color: black;")

        self._min_button.setDarkMode(state)
        self._max_button.setDarkMode(state)
        self._close_button.setDarkMode(state)

    def setTitleBarHeight(self, height: int) -> None:
        """ __doc__. """

        self.setFixedHeight(height)

        self._min_button.setFixedHeight(height)
        self._max_button.setFixedHeight(height)
        self._close_button.setFixedHeight(height)

    def setMenuBar(self, menubar: QMenuBar) -> None:
        self._menu_bar = menubar
        self._menu_bar.setParent(self)

        self._title_frame.raise_()

    def setSystemMenuButtonAvailable(self, menu: int, button: int, state: bool) -> None:
        """ Makes an item available/unavailable in the system menu. """

        if state:
            if button == win32con.SC_MINIMIZE and not self._min_button.buttonEnabled():
                return
            elif button == win32con.SC_MAXIMIZE and not self._max_button.buttonEnabled():
                return
            elif button == win32con.SC_CLOSE and not self._close_button.buttonEnabled():
                return

            win32gui.EnableMenuItem(
                menu, button, win32con.MF_BYCOMMAND | win32con.MF_ENABLED
            )
        else:
            win32gui.EnableMenuItem(
                menu, button, win32con.MF_BYCOMMAND | win32con.MF_DISABLED | win32con.MF_GRAYED
            )

    def setMinimizeEnabled(self, state: bool) -> None:
        """ Disables the ability to minimize the window. """

        self._min_button.setButtonEnabled(state)
        if state:
            self.setSystemMenuButtonAvailable(
                win32gui.GetSystemMenu(self.window().winId(), False), win32con.SC_MINIMIZE, True
            )
        else:
            self.setSystemMenuButtonAvailable(
                win32gui.GetSystemMenu(self.window().winId(), False), win32con.SC_MINIMIZE, False
            )

    def setMaximizeEnabled(self, state: bool) -> None:
        """ Disables the ability to maximize/restore the window. """

        self._max_button.setButtonEnabled(state)
        if state:
            self.setSystemMenuButtonAvailable(
                win32gui.GetSystemMenu(self.window().winId(), False), win32con.SC_RESTORE, True
            )
            self.setSystemMenuButtonAvailable(
                win32gui.GetSystemMenu(self.window().winId(), False), win32con.SC_MAXIMIZE, True
            )
        else:
            self.setSystemMenuButtonAvailable(
                win32gui.GetSystemMenu(self.window().winId(), False), win32con.SC_RESTORE, False
            )
            self.setSystemMenuButtonAvailable(
                win32gui.GetSystemMenu(self.window().winId(), False), win32con.SC_MAXIMIZE, False
            )

    def setCloseEnabled(self, state: bool) -> None:
        """ Disables the ability to close the window. """

        self._close_button.setButtonEnabled(state)
        if state:
            self.setSystemMenuButtonAvailable(
                win32gui.GetSystemMenu(self.window().winId(), False), win32con.SC_CLOSE, True
            )
        else:
            self.setSystemMenuButtonAvailable(
                win32gui.GetSystemMenu(self.window().winId(), False), win32con.SC_CLOSE, False
            )

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """ Title bar mouse double click event. """

        # Maximize/restore the window by double-clicking the left mouse button
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggleMaxState()

        return super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """ Title bar mouse press event. """

        # Opens the system context menu on the right mouse click
        if event.button() == Qt.MouseButton.RightButton:
            menu = win32gui.GetSystemMenu(self.window().winId(), False)

            if self.window().isMaximized():
                self.setSystemMenuButtonAvailable(menu, win32con.SC_MOVE, False)
                self.setSystemMenuButtonAvailable(menu, win32con.SC_SIZE, False)
                self.setSystemMenuButtonAvailable(menu, win32con.SC_MAXIMIZE, False)

                self.setSystemMenuButtonAvailable(menu, win32con.SC_RESTORE, True)
            else:
                self.setSystemMenuButtonAvailable(menu, win32con.SC_MOVE, True)
                self.setSystemMenuButtonAvailable(menu, win32con.SC_SIZE, True)
                self.setSystemMenuButtonAvailable(menu, win32con.SC_MAXIMIZE, True)

                self.setSystemMenuButtonAvailable(menu, win32con.SC_RESTORE, False)

            selected = win32gui.TrackPopupMenu(
                menu, win32con.TPM_RIGHTBUTTON | win32con.TPM_RETURNCMD,
                *win32gui.GetCursorPos(), 0, self.window().winId(), None
            )

            if selected:
                win32gui.ReleaseCapture()
                win32gui.SendMessage(
                    self.window().winId(), win32con.WM_SYSCOMMAND, selected, 0
                )

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """ Title bar mouse press event. """

        # Moves the window while holding down the left mouse button
        if not event.position().x() < self.width() - 138:
            return

        win32gui.ReleaseCapture()
        win32gui.SendMessage(
            self.window().winId(), win32con.WM_SYSCOMMAND, win32con.SC_MOVE | win32con.HTCAPTION, 0
        )

        return super().mouseMoveEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """ Title bar mouse press event. """

        # Positions window title bar widgets
        self._icon.move(QPoint(
            (self.height() // 2) - (self._icon.height() // 2),
            (self.height() // 2) - (self._icon.height() // 2)
        ))

        self._title.adjustSize()
        self._title.move(QPoint(
            self.height(), (self.height() // 2) - (self._icon.height() // 2)
        ))

        self._min_button.move(QPoint(self.size().width() - 138, 0))
        self._max_button.move(QPoint(self.size().width() - 92, 0))
        self._close_button.move(QPoint(self.size().width() - 46, 0))

        if self._menu_bar:
            adjusted = self._menu_bar.sizeHint()

            height = 0
            if self._title.text():
                height = self._title.height() + self._title.x() + self._icon.x()

            self._title_frame.move(self.height() + height + adjusted.width(), 0)
            self._title_frame.resize(
                self.width() - self.height() - height - adjusted.width() - 138, self.height()
            )

            self._menu_bar.move(self.height() + height, 0)
            self._menu_bar.resize(
                self.width() - self.height() - height - 138, self.height()
            )

        return super().resizeEvent(event)


class QBaseMainWindow(QCustomBase):
    """ Base class for creating a frameless window. """

    def __init__(self, theme: int = 0x0001, style: int = 0x0004, *, flags: int = None) -> None:
        """ Frameless window initialization. """

        self._is_min_button_hovered = False
        self._is_max_button_hovered = False
        self._is_cls_button_hovered = False

        self._title_bar = None

        super().__init__(theme=theme, style=style, flags=flags)

        self._background = QWidget(self)
        self._title_bar = QTitleBar(self, self._is_dark)

        self.installEventFilter(self)
        self.restoreGeometry(
            QSettings(QApplication.applicationName()).value("geometry")
        )

    def titleBar(self) -> QTitleBar:
        return self._title_bar

    def setDarkMode(self, state: bool) -> None:
        """ Sets the title bar dark/light theme. """

        self._title_bar.setDarkMode(state)

        super().setDarkMode(state)

    def setWindowIcon(self, icon: QIcon | str) -> None:
        """ Sets an icon for a window. """

        if isinstance(icon, str):
            icon = QIcon(icon)

        self._title_bar.setIcon(icon)

        super().setWindowIcon(icon)

    def setWindowTitle(self, title: str) -> None:
        """ Sets a title for a window. """

        self._title_bar.setTitle(title)

        super().setWindowTitle(title)

    def setIconVisibility(self, state: bool) -> None:
        """ Hides/shows the icon. """

        self._title_bar.setIconVisibility(state)

    def setTitleVisibility(self, state: bool) -> None:
        """ Hides/shows the title. """

        self._title_bar.setTitleVisibility(state)

    def setBackground(self, color: str) -> None:
        """ Sets a background color for a window. """

        self._background.setStyleSheet(f"background: {color};")

    def setMenuBar(self, menubar: QMenuBar) -> None:
        self._title_bar.setMenuBar(menubar)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """ Window resize event."""

        # Positions window widgets
        try:
            self._background.resize(self.size())
            self._title_bar.setFixedWidth(self.width())

            if not self._mica_effect:
                self.temporaryDisableEffect()
        except AttributeError:
            ...

        return super().resizeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """ Window close event."""

        # Saving window geometry
        QSettings(QApplication.applicationName()).setValue("geometry", self.saveGeometry())

        super().closeEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """ Window event filter. """

        # Update the maximize/restore button depending on the state of the window
        if event.type() == QEvent.Type.ActivationChange:
            self._title_bar.minimizeButton().setActiveMode(self.isActiveWindow())
            self._title_bar.maximizeButton().setActiveMode(self.isActiveWindow())
            self._title_bar.closeButton().setActiveMode(self.isActiveWindow())

        if event.type() == QEvent.Type.WindowStateChange:
            self._title_bar.updateMaxButton()

        return super().eventFilter(watched, event)

    def nativeEvent(self, event: bytes, message: int) -> tuple[bool, int] | object:
        """ Window native event."""

        # Native event for window resizing via win32api.
        msg = MSG.from_address(int(message))

        if not msg.hWnd:
            return False, 0

        if msg.message == win32con.WM_NCHITTEST:
            position = QCursor.pos()

            x = position.x() - self.x()
            y = position.y() - self.y()

            # Button tooltip in title bar on mouse hover [Bug]

            """if self._title_bar.childAt(
                    position - self.geometry().topLeft()
            ) is self._title_bar.minimizeButton():
                self._is_min_button_hovered = True
                self._title_bar.minimizeButton().setState(
                    QTitleBarButton.State.Hovered
                )

                return True, win32con.HTMINBUTTON

            if self._title_bar.childAt(
                    position - self.geometry().topLeft()
            ) is self._title_bar.maximizeButton():
                self._is_max_button_hovered = True
                self._title_bar.maximizeButton().setState(
                    QTitleBarButton.State.Hovered
                )

                return True, win32con.HTMAXBUTTON

            if self._title_bar.childAt(
                    position - self.geometry().topLeft()
            ) is self._title_bar.closeButton():
                self._is_cls_button_hovered = True
                self._title_bar.closeButton().setState(
                    QTitleBarButton.State.Hovered
                )

                return True, win32con.HTCLOSE"""

            border_width = 4

            left_x = x < border_width
            right_x = x > self.width() - border_width - 10
            top_y = y < border_width
            bottom_y = y > self.height() - border_width

            if right_x and bottom_y:
                return True, win32con.HTBOTTOMRIGHT
            elif right_x and top_y:
                return True, win32con.HTTOPRIGHT
            elif left_x and bottom_y:
                return True, win32con.HTBOTTOMLEFT
            elif left_x and top_y:
                return True, win32con.HTTOPLEFT
            elif right_x:
                return True, win32con.HTRIGHT
            elif bottom_y:
                return True, win32con.HTBOTTOM
            elif left_x:
                return True, win32con.HTLEFT
            elif top_y:
                return True, win32con.HTTOP

        # Button tooltip in title bar on mouse hover [Bug]

        """if self._is_min_button_hovered:
            if msg.message == win32con.WM_NCLBUTTONDOWN:
                self._title_bar.minimizeButton().setState(
                    QTitleBarButton.State.Pressed
                )

                return True, 0
            elif msg.message in [win32con.WM_NCLBUTTONUP, win32con.WM_NCRBUTTONUP]:
                self._title_bar.minimizeButton().click()
            elif msg.message in [0x2A2, win32con.WM_MOUSELEAVE] and self._title_bar.minimizeButton().state() != 0x0008:
                self._is_min_button_hovered = False
                self._title_bar.minimizeButton().setState(
                    QTitleBarButton.State.Normal
                )

        if self.isWindows11() and self._is_max_button_hovered:
            if msg.message == win32con.WM_NCLBUTTONDOWN:
                self._title_bar.maximizeButton().setState(
                    QTitleBarButton.State.Pressed
                )

                return True, 0
            elif msg.message in [win32con.WM_NCLBUTTONUP, win32con.WM_NCRBUTTONUP]:
                self._title_bar.maximizeButton().click()
            elif msg.message in [0x2A2, win32con.WM_MOUSELEAVE] and self._title_bar.maximizeButton().state() != 0x0008:
                self._is_max_button_hovered = False
                self._title_bar.maximizeButton().setState(
                    QTitleBarButton.State.Normal
                )

        if self._is_cls_button_hovered:
            if msg.message == win32con.WM_NCLBUTTONDOWN:
                self._title_bar.closeButton().setState(
                    QTitleBarButton.State.Pressed
                )

                return True, 0
            elif msg.message in [win32con.WM_NCLBUTTONUP, win32con.WM_NCRBUTTONUP]:
                self._title_bar.closeButton().click()
            elif msg.message in [0x2A2, win32con.WM_MOUSELEAVE] and self._title_bar.closeButton().state() != 0x0008:
                self._is_cls_button_hovered = False
                self._title_bar.closeButton().setState(
                    QTitleBarButton.State.Normal
                )"""

        return super().nativeEvent(event, message)


class QBaseDialog(QBaseMainWindow):
    def __init__(self, parent: QWidget = None,  theme: int = 0x0001, style: int = 0x0004) -> None:
        super().__init__(theme=theme, style=style)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.Tool |
            Qt.WindowType.CustomizeWindowHint
        )

        self.titleBar().minimizeButton().hide()
        self.titleBar().maximizeButton().hide()

        self.titleBar().setMinimizeEnabled(False)
        self.titleBar().setMaximizeEnabled(False)
        self.titleBar().setCloseEnabled(True)

        if icon := parent.windowIcon():
            self.setWindowIcon(icon)

    def exec(self) -> None:
        self.show()
