import enum
import sys

import win32con
import win32gui

from ctypes import Structure, POINTER, c_int, sizeof, pointer, cdll, c_bool, byref
from ctypes.wintypes import DWORD, ULONG, BOOL, HRGN, LPCVOID, LONG


class WINDOWCOMPOSITIONATTRIB(enum.Enum):
    WCA_ACCENT_POLICY = 19
    WCA_USEDARKMODECOLORS = 26


class ACCENT_STATE(enum.Enum):
    ACCENT_DISABLED = 0
    ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
    ACCENT_ENABLE_HOSTBACKDROP = 5


class DWMWINDOWATTRIBUTE(enum.Enum):
    DWMWA_NCRENDERING_POLICY = 2


class DWMNCRENDERINGPOLICY(enum.Enum):
    DWMNCRP_DISABLED = 1


class ACCENT_POLICY(Structure):
    _fields_ = [
        ("AccentState",   DWORD),
        ("AccentFlags",   DWORD),
        ("GradientColor", DWORD),
        ("AnimationId",   DWORD)
    ]


class WINDOWCOMPOSITIONATTRIBDATA(Structure):
    _fields_ = [
        ("Attribute",  DWORD),
        ("Data",       POINTER(ACCENT_POLICY)),
        ("SizeOfData", ULONG)
    ]


class MARGINS(Structure):
    _fields_ = [
        ("cxLeftWidth",    c_int),
        ("cxRightWidth",   c_int),
        ("cyTopHeight",    c_int),
        ("cyBottomHeight", c_int)
    ]


class DWM_BLURBEHIND(Structure):
    _fields_ = [
        ("dwFlags",                DWORD),
        ("fEnable",                BOOL),
        ("hRgnBlur",               HRGN),
        ("fTransitionOnMaximized", BOOL)
    ]


class QWindowsEffects:
    """ Class for applying Windows effects """

    def __init__(self, hwnd: int = None) -> None:

        self._hwnd = hwnd

        self._accent_policy = ACCENT_POLICY()

        self._win_attr_data = WINDOWCOMPOSITIONATTRIBDATA()

        self._win_attr_data.Attribute = WINDOWCOMPOSITIONATTRIB.WCA_ACCENT_POLICY.value
        self._win_attr_data.SizeOfData = sizeof(self._accent_policy)
        self._win_attr_data.Data = pointer(self._accent_policy)

        self._user_32 = cdll.LoadLibrary("user32")
        self._dwm_api = cdll.LoadLibrary("dwmapi")

        self.setWinCompositionAttribute = self._user_32.SetWindowCompositionAttribute
        self.setWinCompositionAttribute.argtypes = [c_int, POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
        self.setWinCompositionAttribute.restype = c_bool

        self.dwmExtendFrameIntoClientArea = self._dwm_api.DwmExtendFrameIntoClientArea
        self.dwmExtendFrameIntoClientArea.argtypes = [c_int, POINTER(MARGINS)]
        self.dwmExtendFrameIntoClientArea.restype = LONG

        self.dwmEnableBlurBehindWindow = self._dwm_api.DwmEnableBlurBehindWindow
        self.dwmEnableBlurBehindWindow.argtypes = [c_int, POINTER(DWM_BLURBEHIND)]
        self.dwmEnableBlurBehindWindow.restype = LONG

        self.dwmSetWindowAttribute = self._dwm_api.DwmSetWindowAttribute
        self.dwmSetWindowAttribute.argtypes = [c_int, DWORD, LPCVOID, DWORD]
        self.dwmSetWindowAttribute.restype = LONG

    def addAcrylicEffect(self, hwnd: int, color: str, shadows: bool = True, animation: int = 0) -> None:
        color = DWORD(
            int("".join(color[index:index + 2] for index in range(6, -1, -2)), base=16)
        )

        accent_flags = DWORD(0x20 | 0x40 | 0x80 | 0x100) if shadows else DWORD(0)
        animation = DWORD(animation)

        self._accent_policy.AccentState = ACCENT_STATE.ACCENT_ENABLE_ACRYLICBLURBEHIND.value
        self._accent_policy.AccentFlags = accent_flags
        self._accent_policy.GradientColor = color
        self._accent_policy.AnimationId = animation

        self.setWinCompositionAttribute(int(hwnd), pointer(self._win_attr_data))

    def addMicaEffect(self, hwnd: int, dark_mode: bool = False, alt: bool = True) -> None:
        self._accent_policy.AccentState = ACCENT_STATE.ACCENT_ENABLE_HOSTBACKDROP.value

        self.setWinCompositionAttribute(hwnd, pointer(self._win_attr_data))

        if dark_mode:
            self._win_attr_data.Attribute = WINDOWCOMPOSITIONATTRIB.WCA_USEDARKMODECOLORS.value
            self.setWinCompositionAttribute(hwnd, pointer(self._win_attr_data))
            self._win_attr_data.Attribute = WINDOWCOMPOSITIONATTRIB.WCA_ACCENT_POLICY.value

        if sys.getwindowsversion().build >= 22523:
            self.dwmSetWindowAttribute(hwnd, 38, byref(c_int(4 if alt else 2)), 4)
        else:
            self.dwmSetWindowAttribute(hwnd, 1029, byref(c_int(1)), 4)

    def removeBackgroundEffect(self, hwnd: int) -> None:
        self._accent_policy.AccentState = ACCENT_STATE.ACCENT_DISABLED.value

        self.setWinCompositionAttribute(int(hwnd), pointer(self._win_attr_data))

    def addShadowEffect(self, hwnd: int) -> None:
        self.dwmExtendFrameIntoClientArea(int(hwnd), byref(MARGINS(-1, -1, -1, -1)))

    def removeShadowEffect(self, hwnd: int) -> None:
        self.dwmSetWindowAttribute(
            int(hwnd),
            DWMWINDOWATTRIBUTE.DWMWA_NCRENDERING_POLICY.value,
            byref(c_int(DWMNCRENDERINGPOLICY.DWMNCRP_DISABLED.value)),
            4
        )

    def addBlurBehindWindow(self, hwnd: int) -> None:
        self.dwmEnableBlurBehindWindow(int(hwnd), byref(DWM_BLURBEHIND(1, True, 0, False)))

    @staticmethod
    def addWindowAnimation(hwnd: int) -> None:
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

        win32gui.SetWindowLong(
            hwnd, win32con.GWL_STYLE, style
            | win32con.WS_MINIMIZEBOX
            | win32con.WS_MAXIMIZEBOX
            | win32con.WS_CAPTION
            | win32con.WS_THICKFRAME
        )
