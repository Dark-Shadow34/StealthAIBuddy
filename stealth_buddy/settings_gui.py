import sys
import os
import ctypes
from typing import Optional, Dict, Any, List

from PySide6.QtCore import (
    Qt, Signal, QTimer, QPoint, QSize, QRectF, Property,
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QThread, QObject
)
from PySide6.QtGui import (
    QColor, QFont, QMouseEvent, QPainter, QPainterPath,
    QBrush, QPen, QLinearGradient, QRadialGradient
)
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QSlider, QPushButton, QStackedWidget, QWidget, QFrame, QApplication,
    QScrollArea, QSizePolicy, QGraphicsDropShadowEffect, QTextEdit,
    QGridLayout, QSpacerItem
)

if sys.platform == "win32":
    import winreg

from .config import ConfigManager, PROMPT_PRESETS, HUD_THEMES, auto_detect_provider
from .ai_engine import AIEngine

# ── Color Palette Tokens ─────────────────────────────────────────
VOID     = "#05060a"
BASE     = "#090c14"
CARD     = "#0e1220"
ELEVATED = "#13182a"
BORDER   = "#1b2235"
BORDER_H = "#2d3a52"
MUTED    = "#3e4d68"
SUBTLE   = "#7a8aaa"
BODY     = "#b8c6de"
BRIGHT   = "#e8f0fc"
WHITE    = "#ffffff"
INDIGO   = "#6366f1"
INDIGO_H = "#818cf8"
EMERALD  = "#10e599"
CRIMSON  = "#ff4d4d"
AMBER    = "#f59e0b"
CYAN     = "#38bdf8"
ROSE     = "#f43f5e"
VIOLET   = "#a855f7"

SETTINGS_QSS = f"""
/* ── Main Dialog Window ── */
QDialog {{
    background-color: transparent;
}}
QFrame#MainFrame {{
    background-color: {BASE};
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 9.5pt;
    color: {BODY};
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.07);
}}

/* ── Custom Titlebar ── */
QFrame#TitleBar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(99, 102, 241, 0.08),
        stop:0.5 rgba(255, 255, 255, 0.02),
        stop:1 rgba(168, 85, 247, 0.06));
    border-bottom: 1px solid {BORDER};
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
}}
QLabel#TitleLabel {{
    font-size: 11pt;
    font-weight: 700;
    color: {BRIGHT};
    letter-spacing: 0.3px;
}}
QLabel#TitleSub {{
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 7pt;
    color: {MUTED};
    font-weight: 600;
    letter-spacing: 2px;
}}

/* ── Navigation Rail ── */
QFrame#Rail {{
    background: {VOID};
    border-right: 1px solid {BORDER};
    border-bottom-left-radius: 16px;
}}
QPushButton#RailBtn {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    color: {MUTED};
    font-size: 7.5pt;
    font-weight: 700;
    text-align: center;
    padding: 6px 4px;
}}
QPushButton#RailBtn:hover {{
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.08);
    color: {BODY};
}}
QPushButton#RailBtn:pressed {{
    background: rgba(99, 102, 241, 0.1);
}}
QPushButton#RailBtnActive {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(99, 102, 241, 0.28),
        stop:1 rgba(99, 102, 241, 0.06));
    border: 1px solid rgba(99, 102, 241, 0.5);
    border-left: 3px solid {INDIGO};
    border-radius: 10px;
    color: {INDIGO_H};
    font-size: 7.5pt;
    font-weight: 700;
    text-align: center;
    padding: 6px 4px;
}}

/* ── Scroll Areas ── */
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: rgba(255, 255, 255, 0.02);
    width: 4px;
    border-radius: 2px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.10);
    border-radius: 2px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(99, 102, 241, 0.5);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── Section Titles ── */
QLabel#SecTitle {{
    font-size: 7.5pt;
    font-weight: 700;
    letter-spacing: 2px;
    color: {MUTED};
    padding-bottom: 1px;
}}
QFrame#SectionDivider {{
    background: {BORDER};
    max-height: 1px;
}}

/* ── Setting Cards ── */
QFrame#SettingCard {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QFrame#SettingCard:hover {{
    border-color: {BORDER_H};
    background: rgba(14, 18, 32, 0.9);
}}
QFrame#SimpleModeCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(16, 229, 153, 0.10),
        stop:1 rgba(99, 102, 241, 0.04));
    border: 1px solid rgba(16, 229, 153, 0.30);
    border-radius: 12px;
}}
QFrame#SimpleModeCard:hover {{
    border-color: rgba(16, 229, 153, 0.60);
}}
QFrame#SmartKeyCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(99, 102, 241, 0.14),
        stop:1 rgba(56, 189, 248, 0.04));
    border: 1px solid rgba(99, 102, 241, 0.36);
    border-radius: 12px;
}}
QFrame#SmartKeyCard:hover {{
    border-color: rgba(99, 102, 241, 0.6);
}}
QFrame#StealthCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(239, 68, 68, 0.08),
        stop:1 rgba(18, 6, 6, 0.0));
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 12px;
}}
QFrame#StealthCard:hover {{
    border-color: rgba(239, 68, 68, 0.55);
}}

QLabel#RowLabel {{
    font-size: 9.5pt;
    font-weight: 600;
    color: {BRIGHT};
}}
QLabel#RowDesc {{
    font-size: 8pt;
    color: {SUBTLE};
}}

/* ── Text Inputs ── */
QLineEdit, QTextEdit {{
    background: rgba(0, 0, 0, 0.40);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 9pt;
    color: {BRIGHT};
    font-family: 'JetBrains Mono', 'Consolas', monospace;
}}
QLineEdit:hover, QTextEdit:hover {{
    border-color: rgba(255, 255, 255, 0.18);
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {INDIGO};
    background: rgba(99, 102, 241, 0.05);
}}

/* ── Dropdown Combobox ── */
QComboBox {{
    background: {ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 5px 10px;
    font-size: 9pt;
    color: {BRIGHT};
    min-width: 140px;
}}
QComboBox:hover {{
    border-color: {BORDER_H};
    background: rgba(255, 255, 255, 0.05);
}}
QComboBox:focus {{
    border-color: {INDIGO};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background: {ELEVATED};
    border: 1px solid {BORDER_H};
    color: {BRIGHT};
    selection-background-color: rgba(99, 102, 241, 0.35);
    border-radius: 7px;
    padding: 4px;
}}

/* ── Sliders ── */
QSlider::groove:horizontal {{
    height: 4px;
    background: {ELEVATED};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {INDIGO}, stop:1 {INDIGO_H});
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {WHITE};
    border: 2px solid {INDIGO};
    width: 14px;
    height: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: {INDIGO_H};
    border-color: {WHITE};
}}

/* ── Action Buttons ── */
QPushButton#BtnSave {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {INDIGO}, stop:1 #4f46e5);
    color: #ffffff;
    font-weight: 700;
    border: 1px solid rgba(255, 255, 255, 0.20);
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 9pt;
}}
QPushButton#BtnSave:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {INDIGO_H}, stop:1 {INDIGO});
    border-color: rgba(255, 255, 255, 0.40);
}}
QPushButton#BtnSave:pressed {{
    padding-top: 9px;
    padding-bottom: 7px;
}}
QPushButton#BtnCancel {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid {BORDER};
    color: {BODY};
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 9pt;
}}
QPushButton#BtnCancel:hover {{
    background: rgba(255, 255, 255, 0.07);
    border-color: {BORDER_H};
    color: {BRIGHT};
}}
QPushButton#BtnAction {{
    background: rgba(99, 102, 241, 0.10);
    border: 1px solid rgba(99, 102, 241, 0.28);
    color: {INDIGO_H};
    font-weight: 600;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 8.5pt;
}}
QPushButton#BtnAction:hover {{
    background: rgba(99, 102, 241, 0.22);
    border-color: rgba(99, 102, 241, 0.6);
    color: #ffffff;
}}
QPushButton#BtnAction:pressed {{
    background: rgba(99, 102, 241, 0.35);
}}
QPushButton#BtnAutoConfig {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {INDIGO}, stop:1 #4f46e5);
    color: #ffffff;
    font-weight: 700;
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 8.5pt;
}}
QPushButton#BtnAutoConfig:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {INDIGO_H}, stop:1 {INDIGO});
    border-color: rgba(255, 255, 255, 0.40);
}}
QPushButton#BtnAutoConfig:disabled {{
    background: rgba(99, 102, 241, 0.25);
    color: rgba(255,255,255,0.45);
}}
QPushButton#BtnDanger {{
    background: rgba(239, 68, 68, 0.10);
    border: 1px solid rgba(239, 68, 68, 0.30);
    color: #f87171;
    font-weight: 600;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 8.5pt;
}}
QPushButton#BtnDanger:hover {{
    background: rgba(239, 68, 68, 0.22);
    border-color: rgba(239, 68, 68, 0.6);
    color: #ffffff;
}}

/* ── Theme Card ── */
QFrame#ThemeCardWidget {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 6px;
}}
QFrame#ThemeCardWidget:hover {{
    border-color: {BORDER_H};
    background: rgba(255, 255, 255, 0.025);
}}
QFrame#ThemeCardWidgetActive {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(99, 102, 241, 0.16), stop:1 rgba(16, 229, 153, 0.04));
    border: 1px solid {INDIGO_H};
    border-radius: 10px;
    padding: 6px;
}}

/* ── Hotkey Pill ── */
QFrame#HotkeyRow {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QFrame#HotkeyRow:hover {{
    border-color: {BORDER_H};
}}
"""


# ─────────────────────────────────────────────────────────────────
# Auto-Configure Worker Thread
# ─────────────────────────────────────────────────────────────────
class AutoConfigWorker(QObject):
    finished = Signal(bool, str, str, str)  # success, prov, model, msg

    def __init__(self, ai_engine: AIEngine, api_key: str):
        super().__init__()
        self.ai_engine = ai_engine
        self.api_key = api_key

    def run(self):
        try:
            success, prov, best_model, msg = self.ai_engine.test_smart_key(self.api_key)
            self.finished.emit(success, prov, best_model, msg)
        except Exception as e:
            self.finished.emit(False, "", "", f"Unexpected error: {e}")


# ─────────────────────────────────────────────────────────────────
# Modern Toggle Switch
# ─────────────────────────────────────────────────────────────────
class ModernSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked: bool = False, active_color: str = INDIGO, parent=None):
        super().__init__(parent)
        self.setFixedSize(46, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = checked
        self._thumb_pos = 1.0 if checked else 0.0
        self._active_color = QColor(active_color)

        self._anim = QPropertyAnimation(self, b"thumb_pos", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def get_thumb_pos(self) -> float:
        return self._thumb_pos

    def set_thumb_pos(self, pos: float):
        self._thumb_pos = pos
        self.update()

    thumb_pos = Property(float, get_thumb_pos, set_thumb_pos)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool, animate: bool = True):
        if self._checked == checked:
            return
        self._checked = checked
        if animate and self.isVisible():
            self._anim.stop()
            self._anim.setStartValue(self._thumb_pos)
            self._anim.setEndValue(1.0 if checked else 0.0)
            self._anim.start()
        else:
            self._thumb_pos = 1.0 if checked else 0.0
            self.update()
        self.toggled.emit(self._checked)

    def toggle(self):
        self.setChecked(not self._checked)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
            event.accept()

    def set_active_color(self, hex_color: str):
        self._active_color = QColor(hex_color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        radius = h / 2.0

        # Interpolate track background color
        off_bg = QColor(19, 24, 42, 240)
        on_bg = self._active_color
        r = int(off_bg.red()   + (on_bg.red()   - off_bg.red())   * self._thumb_pos)
        g = int(off_bg.green() + (on_bg.green() - off_bg.green()) * self._thumb_pos)
        b = int(off_bg.blue()  + (on_bg.blue()  - off_bg.blue())  * self._thumb_pos)
        curr_bg = QColor(r, g, b, 240)

        # Track border
        ba = int(20 + 70 * self._thumb_pos)
        curr_border = QColor(255, 255, 255, ba)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        painter.fillPath(path, QBrush(curr_bg))
        painter.setPen(QPen(curr_border, 1.0))
        painter.drawPath(path)

        # Thumb
        thumb_dia = h - 6.0
        min_x = 3.0
        max_x = w - thumb_dia - 3.0
        curr_x = min_x + (max_x - min_x) * self._thumb_pos
        thumb_rect = QRectF(curr_x, 3.0, thumb_dia, thumb_dia)

        # Shadow
        shadow_path = QPainterPath()
        shadow_path.addEllipse(thumb_rect.translated(0, 1.2))
        painter.fillPath(shadow_path, QBrush(QColor(0, 0, 0, 80)))

        # White knob
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 252)))
        painter.drawEllipse(thumb_rect)


# ─────────────────────────────────────────────────────────────────
# Sliding Stacked Widget
# ─────────────────────────────────────────────────────────────────
class SlidingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._anim_group: Optional[QParallelAnimationGroup] = None
        self._is_animating = False

    def slide_to_index(self, new_index: int, duration: int = 220):
        if self._is_animating or new_index == self.currentIndex():
            self.setCurrentIndex(new_index)
            return
        current_index = self.currentIndex()
        if new_index < 0 or new_index >= self.count():
            return

        curr_widget = self.widget(current_index)
        next_widget = self.widget(new_index)

        w = self.width()
        h = self.height()
        direction = 1 if new_index > current_index else -1

        next_widget.setGeometry(direction * w, 0, w, h)
        next_widget.show()
        next_widget.raise_()

        self._anim_group = QParallelAnimationGroup(self)

        anim_curr = QPropertyAnimation(curr_widget, b"pos", self)
        anim_curr.setDuration(duration)
        anim_curr.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_curr.setStartValue(QPoint(0, 0))
        anim_curr.setEndValue(QPoint(-direction * w, 0))

        anim_next = QPropertyAnimation(next_widget, b"pos", self)
        anim_next.setDuration(duration)
        anim_next.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_next.setStartValue(QPoint(direction * w, 0))
        anim_next.setEndValue(QPoint(0, 0))

        self._anim_group.addAnimation(anim_curr)
        self._anim_group.addAnimation(anim_next)
        self._is_animating = True

        def on_finished():
            self.setCurrentIndex(new_index)
            curr_widget.hide()
            curr_widget.move(0, 0)
            next_widget.move(0, 0)
            self._is_animating = False

        self._anim_group.finished.connect(on_finished)
        self._anim_group.start()


# ─────────────────────────────────────────────────────────────────
# Drag Handle (for frameless titlebar)
# ─────────────────────────────────────────────────────────────────
class DragHandle(QFrame):
    def __init__(self, dialog, parent=None):
        super().__init__(parent)
        self._dialog = dialog
        self._dragging = False
        self._drag_pos = QPoint()

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = e.globalPosition().toPoint() - self._dialog.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._dragging and e.buttons() == Qt.MouseButton.LeftButton:
            self._dialog.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._dragging = False


# ─────────────────────────────────────────────────────────────────
# Virtual Keyboard Widget
# ─────────────────────────────────────────────────────────────────
class VirtualKeyboardWidget(QWidget):
    """
    Interactive rendered keyboard widget. Modifier keys toggle on click.
    Normal key click builds a combo string and calls the provided callback.
    """
    key_selected = Signal(str)  # emits the full combo string e.g. "ctrl+alt+f9"

    # Layout: list of rows, each row is list of (label, width_units, vk_name)
    KEYBOARD_ROWS = [
        # Function row
        [("Esc",1.2,"esc"),("F1",1,"f1"),("F2",1,"f2"),("F3",1,"f3"),("F4",1,"f4"),
         ("F5",1,"f5"),("F6",1,"f6"),("F7",1,"f7"),("F8",1,"f8"),
         ("F9",1,"f9"),("F10",1,"f10"),("F11",1,"f11"),("F12",1,"f12")],
        # Number row
        [("~",1,"`"),("1",1,"1"),("2",1,"2"),("3",1,"3"),("4",1,"4"),("5",1,"5"),
         ("6",1,"6"),("7",1,"7"),("8",1,"8"),("9",1,"9"),("0",1,"0"),
         ("-",1,"minus"),("=",1,"equal"),("⌫",1.8,"backspace")],
        # QWERTY row
        [("Tab",1.5,"tab"),("Q",1,"q"),("W",1,"w"),("E",1,"e"),("R",1,"r"),("T",1,"t"),
         ("Y",1,"y"),("U",1,"u"),("I",1,"i"),("O",1,"o"),("P",1,"p"),
         ("[",1,"lbracket"),("]",1,"rbracket"),("\\",1.3,"backslash")],
        # ASDF row
        [("Caps",1.7,"capslock"),("A",1,"a"),("S",1,"s"),("D",1,"d"),("F",1,"f"),
         ("G",1,"g"),("H",1,"h"),("J",1,"j"),("K",1,"k"),("L",1,"l"),
         (";",1,"semicolon"),("'",1,"quote"),("Enter",2.0,"enter")],
        # ZXCV row
        [("Shift",2.2,"shift"),("Z",1,"z"),("X",1,"x"),("C",1,"c"),("V",1,"v"),
         ("B",1,"b"),("N",1,"n"),("M",1,"m"),(",",1,"comma"),(".",1,"period"),
         ("/",1,"slash"),("⇧",1.8,"shift")],
        # Space row
        [("Ctrl",1.5,"ctrl"),("Win",1.2,"win"),("Alt",1.2,"alt"),
         ("Space",5.5,"space"),
         ("Alt",1.2,"alt"),("Fn",1,"fn"),("Ctrl",1.5,"ctrl")],
    ]

    MODIFIER_KEYS = {"ctrl", "alt", "shift", "win"}
    IGNORE_KEYS   = {"fn"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modifiers: Dict[str, bool] = {"ctrl": False, "alt": False, "shift": False, "win": False}
        self._hovered_key: Optional[str] = None
        self._hover_anim: Dict[str, float] = {}  # key_id → glow amount 0..1
        self._key_rects: Dict[str, tuple] = {}   # key_id → (label, rect, vk_name)

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Animation timer for smooth hover glow
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)  # ~60fps
        self._anim_timer.timeout.connect(self._animate_hover)
        self._anim_timer.start()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(160)

    def sizeHint(self):
        return QSize(680, 175)

    def _get_key_id(self, row: int, col: int, vk: str) -> str:
        return f"{row}_{col}_{vk}"

    def _build_key_rects(self):
        """Calculate pixel rectangles for all keys based on current widget width."""
        self._key_rects.clear()
        w = self.width()
        h = self.height()

        # Total width units per row (approx)
        BASE_UNITS = 14.7
        unit = w / BASE_UNITS
        gap = 3
        row_h = (h - gap * 6) / 6

        y = 0
        for row_idx, row in enumerate(self.KEYBOARD_ROWS):
            x = 0
            for col_idx, (label, width_units, vk_name) in enumerate(row):
                key_w = int(unit * width_units) - gap
                key_h = int(row_h) - gap
                rect = (int(x), int(y), key_w, key_h)
                kid = self._get_key_id(row_idx, col_idx, vk_name)
                self._key_rects[kid] = (label, rect, vk_name)
                x += key_w + gap
            y += row_h + gap

    def paintEvent(self, event):
        self._build_key_rects()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        for kid, (label, rect, vk_name) in self._key_rects.items():
            x, y, w, h = rect
            is_modifier = vk_name in self.MODIFIER_KEYS
            is_active_mod = is_modifier and self._modifiers.get(vk_name, False)
            is_hovered = kid == self._hovered_key
            glow = self._hover_anim.get(kid, 0.0)
            is_ignored = vk_name in self.IGNORE_KEYS

            # Base key color
            if is_active_mod:
                base_color = QColor(99, 102, 241, 220)
                border_color = QColor(129, 140, 248, 255)
                text_color = QColor(255, 255, 255, 255)
            elif is_modifier:
                base_color = QColor(25, 30, 50, 220)
                border_color = QColor(60, 72, 100, int(80 + glow * 120))
                text_color = QColor(180, 190, 220, int(180 + glow * 75))
            elif is_hovered:
                base_color = QColor(99, 102, 241, int(60 + glow * 100))
                border_color = QColor(129, 140, 248, int(150 + glow * 105))
                text_color = QColor(255, 255, 255, int(200 + glow * 55))
            elif is_ignored:
                base_color = QColor(12, 15, 25, 120)
                border_color = QColor(30, 36, 58, 80)
                text_color = QColor(60, 75, 100, 120)
            else:
                base_color = QColor(14, 18, 32, 220)
                border_color = QColor(30, 37, 58, int(80 + glow * 80))
                text_color = QColor(140, 160, 200, int(160 + glow * 95))

            key_path = QPainterPath()
            key_path.addRoundedRect(QRectF(x, y, w, h), 4, 4)

            # Glow effect for hovered/active keys
            if glow > 0.05 or is_active_mod:
                glow_color = QColor(99, 102, 241, int((glow if not is_active_mod else 0.6) * 60))
                glow_path = QPainterPath()
                glow_path.addRoundedRect(QRectF(x - 1, y - 1, w + 2, h + 2), 5, 5)
                painter.fillPath(glow_path, QBrush(glow_color))

            painter.fillPath(key_path, QBrush(base_color))
            painter.setPen(QPen(border_color, 1.0))
            painter.drawPath(key_path)

            # Label
            painter.setPen(text_color)
            font = QFont("JetBrains Mono", 7 if len(label) > 3 else 8)
            font.setWeight(QFont.Weight.Bold if is_active_mod or is_modifier else QFont.Weight.Medium)
            painter.setFont(font)
            painter.drawText(QRectF(x, y, w, h), Qt.AlignmentFlag.AlignCenter, label)

    def _get_key_at(self, pos: QPoint) -> Optional[str]:
        for kid, (label, rect, vk_name) in self._key_rects.items():
            x, y, w, h = rect
            if x <= pos.x() <= x + w and y <= pos.y() <= y + h:
                return kid
        return None

    def mouseMoveEvent(self, event):
        kid = self._get_key_at(event.pos())
        if kid != self._hovered_key:
            self._hovered_key = kid
            self.update()

    def leaveEvent(self, event):
        self._hovered_key = None
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        kid = self._get_key_at(event.pos())
        if not kid:
            return
        _, rect, vk_name = self._key_rects[kid]
        if vk_name in self.IGNORE_KEYS:
            return

        if vk_name in self.MODIFIER_KEYS:
            # Toggle modifier
            self._modifiers[vk_name] = not self._modifiers.get(vk_name, False)
            self.update()
        else:
            # Assemble combo and emit
            combo_parts = []
            if self._modifiers.get("ctrl"):
                combo_parts.append("ctrl")
            if self._modifiers.get("alt"):
                combo_parts.append("alt")
            if self._modifiers.get("shift"):
                combo_parts.append("shift")
            if self._modifiers.get("win"):
                combo_parts.append("win")
            combo_parts.append(vk_name)
            combo = "+".join(combo_parts)
            self.key_selected.emit(combo)
            # Clear modifiers after selection
            for k in self._modifiers:
                self._modifiers[k] = False
            self.update()

    def _animate_hover(self):
        changed = False
        for kid in list(self._key_rects.keys()):
            current = self._hover_anim.get(kid, 0.0)
            target = 1.0 if kid == self._hovered_key else 0.0
            step = 0.12
            new_val = current + (target - current) * step
            if abs(new_val - current) > 0.005:
                self._hover_anim[kid] = new_val
                changed = True
        if changed:
            self.update()

    def reset_modifiers(self):
        for k in self._modifiers:
            self._modifiers[k] = False
        self.update()


# ─────────────────────────────────────────────────────────────────
# Hotkey Bind Row Widget
# ─────────────────────────────────────────────────────────────────
class HotkeyBindRow(QWidget):
    """
    A single hotkey row: shows the label, the current binding as a styled pill,
    and a "Bind" button that opens an inline virtual keyboard.
    """
    binding_changed = Signal(str, str)  # (config_key, new_combo)

    def __init__(self, name: str, desc: str, config_key: str, current_value: str, keyboard_widget, parent=None):
        super().__init__(parent)
        self.config_key = config_key
        self.keyboard_widget = keyboard_widget
        self._current_combo = current_value

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Label
        label_w = QWidget()
        ll = QVBoxLayout(label_w)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(1)
        lb = QLabel(name)
        lb.setObjectName("RowLabel")
        db = QLabel(desc)
        db.setObjectName("RowDesc")
        ll.addWidget(lb)
        ll.addWidget(db)
        layout.addWidget(label_w, 1)

        # Current binding display
        self.combo_lbl = QLabel(self._format_pill(current_value))
        self.combo_lbl.setStyleSheet(
            f"font-family:'JetBrains Mono',monospace;font-size:8.5pt;font-weight:700;"
            f"background:{ELEVATED};border:1px solid {BORDER_H};border-bottom:2px solid rgba(0,0,0,0.6);"
            f"border-radius:6px;padding:3px 10px;color:{BRIGHT};"
        )
        self.combo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.combo_lbl.setMinimumWidth(110)
        layout.addWidget(self.combo_lbl)

        # Bind button
        self.bind_btn = QPushButton("Bind")
        self.bind_btn.setObjectName("BtnAction")
        self.bind_btn.setFixedSize(54, 26)
        self.bind_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bind_btn.clicked.connect(self._on_bind_clicked)
        layout.addWidget(self.bind_btn)

        # Wire keyboard signal when this row is active
        self._kb_connected = False

    def _format_pill(self, combo: str) -> str:
        if not combo:
            return "—"
        parts = combo.split("+")
        return " + ".join(p.upper() for p in parts)

    def set_combo(self, combo: str):
        self._current_combo = combo
        self.combo_lbl.setText(self._format_pill(combo))

    def get_combo(self) -> str:
        return self._current_combo

    def _on_bind_clicked(self):
        """Activates the shared keyboard, connects it to this row temporarily."""
        # Disconnect from any previous row
        try:
            self.keyboard_widget.key_selected.disconnect()
        except RuntimeError:
            pass

        self.keyboard_widget.reset_modifiers()
        self.bind_btn.setText("→ Press key")
        self.bind_btn.setStyleSheet(
            f"background:rgba(99,102,241,0.22);border:1px solid {INDIGO_H};"
            f"border-radius:8px;color:#ffffff;font-weight:700;"
        )
        self.keyboard_widget.key_selected.connect(self._on_key_selected)

    def _on_key_selected(self, combo: str):
        try:
            self.keyboard_widget.key_selected.disconnect()
        except RuntimeError:
            pass
        self._current_combo = combo
        self.combo_lbl.setText(self._format_pill(combo))
        self.bind_btn.setText("Bind")
        self.bind_btn.setStyleSheet("")
        self.binding_changed.emit(self.config_key, combo)


# ─────────────────────────────────────────────────────────────────
# Main Settings Dialog
# ─────────────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    config_updated    = Signal()
    trigger_test_scan = Signal()
    toggle_preview    = Signal()

    def __init__(self, config_mgr: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config_mgr
        self.ai_engine = AIEngine(self.config)
        self.resize(900, 580)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(SETTINGS_QSS)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._current_tab = 0
        self._rail_btns   = []
        self._theme_cards = {}
        self._hk_rows: Dict[str, HotkeyBindRow] = {}
        self._auto_config_thread: Optional[QThread] = None

        # Shared virtual keyboard
        self._vkb = VirtualKeyboardWidget()

        self._init_ui()
        self.load_from_config()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 10)
        self.main_frame.setGraphicsEffect(shadow)

        root = QVBoxLayout(self.main_frame)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_titlebar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_rail())

        self.stack = SlidingStackedWidget()
        self.stack.addWidget(self._build_ai_page())      # 0
        self.stack.addWidget(self._build_hotkeys_page()) # 1
        self.stack.addWidget(self._build_visuals_page()) # 2
        self.stack.addWidget(self._build_stealth_page()) # 3
        self.stack.addWidget(self._build_system_page())  # 4
        body.addWidget(self.stack, 1)

        body_frame = QFrame()
        body_frame.setLayout(body)
        root.addWidget(body_frame, 1)

        root.addWidget(self._build_action_bar())
        main_layout.addWidget(self.main_frame)

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_win32_attributes()

    def _apply_win32_attributes(self):
        if sys.platform != "win32":
            return
        hwnd = int(self.winId())
        if not hwnd:
            return
        try:
            WDA_EXCLUDEFROMCAPTURE = 0x00000011
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception:
            pass

    # ── Titlebar ─────────────────────────────────────────────────
    def _build_titlebar(self) -> QFrame:
        tb = DragHandle(self)
        tb.setObjectName("TitleBar")
        tb.setFixedHeight(44)
        tl = QHBoxLayout(tb)
        tl.setContentsMargins(14, 0, 14, 0)
        tl.setSpacing(8)

        self.wc_close = QPushButton("✕", tb)
        self.wc_close.setFixedSize(18, 18)
        self.wc_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.wc_close.setStyleSheet(
            "QPushButton{background:transparent;color:#ff5f57;font-size:11px;border:none;border-radius:9px;}"
            "QPushButton:hover{background:rgba(255,95,87,0.22);color:#ffffff;}"
        )
        self.wc_close.clicked.connect(self.hide)

        self.wc_min = QPushButton("−", tb)
        self.wc_min.setFixedSize(18, 18)
        self.wc_min.setCursor(Qt.CursorShape.PointingHandCursor)
        self.wc_min.setStyleSheet(
            "QPushButton{background:transparent;color:#febc2e;font-size:14px;border:none;border-radius:9px;}"
            "QPushButton:hover{background:rgba(254,188,46,0.22);color:#ffffff;}"
        )
        self.wc_min.clicked.connect(self.showMinimized)

        tl.addWidget(self.wc_close)
        tl.addWidget(self.wc_min)
        tl.addSpacing(10)

        ico = QLabel("⚡", tb)
        ico.setStyleSheet(f"font-size:13pt;color:{INDIGO_H};")
        tl.addWidget(ico)

        lbl = QLabel("StealthAI Buddy", tb)
        lbl.setObjectName("TitleLabel")
        tl.addWidget(lbl)

        sub = QLabel("CONTROL CENTER", tb)
        sub.setObjectName("TitleSub")
        tl.addWidget(sub)
        tl.addStretch()

        self.page_title = QLabel("AI & API Key", tb)
        self.page_title.setStyleSheet(f"font-size:9pt;color:{INDIGO_H};font-weight:600;padding-right:4px;")
        tl.addWidget(self.page_title)

        return tb

    # ── Rail ─────────────────────────────────────────────────────
    def _build_rail(self) -> QFrame:
        rail = QFrame()
        rail.setObjectName("Rail")
        rail.setFixedWidth(74)
        rl = QVBoxLayout(rail)
        rl.setContentsMargins(7, 12, 7, 12)
        rl.setSpacing(5)

        tabs = [
            ("🤖", "AI"),
            ("⌨️", "Keys"),
            ("👁", "HUD"),
            ("🛡", "Stealth"),
            ("⚙️", "System"),
        ]
        self.page_titles = [
            "AI & API Key",
            "Hotkeys & Triggers",
            "HUD & Themes",
            "Stealth & Invisibility",
            "System & Prefs",
        ]

        for i, (ico, lbl) in enumerate(tabs):
            btn = QPushButton(f"{ico}\n{lbl}", rail)
            btn.setObjectName("RailBtnActive" if i == 0 else "RailBtn")
            btn.setFixedSize(60, 50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, idx=i: self._switch_tab(idx))
            self._rail_btns.append(btn)
            rl.addWidget(btn)

        rl.addStretch()
        return rail

    def _switch_tab(self, idx: int):
        if self._current_tab == idx:
            return
        self._current_tab = idx
        self.stack.slide_to_index(idx)
        self.page_title.setText(self.page_titles[idx])
        for i, btn in enumerate(self._rail_btns):
            btn.setObjectName("RailBtnActive" if i == idx else "RailBtn")
            btn.setStyleSheet("")
            self.style().unpolish(btn)
            self.style().polish(btn)

    # ── Helpers ───────────────────────────────────────────────────
    def _scrollable(self, inner: QWidget) -> QScrollArea:
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.Shape.NoFrame)
        sa.setWidget(inner)
        return sa

    def _section_label(self, text: str) -> QWidget:
        w = QWidget()
        wl = QHBoxLayout(w)
        wl.setContentsMargins(0, 6, 0, 2)
        wl.setSpacing(8)
        lbl = QLabel(text.upper())
        lbl.setObjectName("SecTitle")
        line = QFrame()
        line.setObjectName("SectionDivider")
        line.setFixedHeight(1)
        wl.addWidget(lbl)
        wl.addWidget(line, 1)
        return w

    def _card(self, obj_name: str = "SettingCard") -> QFrame:
        f = QFrame()
        f.setObjectName(obj_name)
        return f

    def _make_rlabel(self, label: str, desc: str) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(1)
        lb = QLabel(label)
        lb.setObjectName("RowLabel")
        db = QLabel(desc)
        db.setObjectName("RowDesc")
        l.addWidget(lb)
        l.addWidget(db)
        return w

    def _build_setting_row(self, title: str, desc: str, control_widget: QWidget) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.addWidget(self._make_rlabel(title, desc), 1)
        layout.addWidget(control_widget)
        return w

    # ── AI Page ──────────────────────────────────────────────────
    def _build_ai_page(self) -> QWidget:
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(10)

        # Universal Key Card
        sk = QFrame()
        sk.setObjectName("SmartKeyCard")
        skl = QVBoxLayout(sk)
        skl.setContentsMargins(14, 12, 14, 12)
        skl.setSpacing(8)

        title_lbl = QLabel("✦  UNIVERSAL API KEY", sk)
        title_lbl.setStyleSheet(f"font-size:9pt;font-weight:700;color:{INDIGO_H};letter-spacing:1px;")
        desc_lbl = QLabel("Paste any Gemini, OpenAI, or Claude key — auto-detected & encrypted with Windows DPAPI.", sk)
        desc_lbl.setStyleSheet(f"font-size:8pt;color:{SUBTLE};")
        desc_lbl.setWordWrap(True)
        skl.addWidget(title_lbl)
        skl.addWidget(desc_lbl)

        key_row = QHBoxLayout()
        self.input_smart_key = QLineEdit(sk)
        self.input_smart_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_smart_key.setPlaceholderText("AIzaSy... or sk-... or sk-ant-...")
        self.input_smart_key.textChanged.connect(self._on_smart_key_typed)
        key_row.addWidget(self.input_smart_key)

        self.btn_eye = QPushButton("👁", sk)
        self.btn_eye.setFixedSize(32, 32)
        self.btn_eye.setObjectName("BtnAction")
        self.btn_eye.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eye.clicked.connect(self._toggle_eye)
        key_row.addWidget(self.btn_eye)

        self.btn_auto = QPushButton("⚡ Auto-Configure", sk)
        self.btn_auto.setObjectName("BtnAutoConfig")
        self.btn_auto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_auto.clicked.connect(self._auto_configure_smart_key)
        key_row.addWidget(self.btn_auto)
        skl.addLayout(key_row)

        self.lbl_detect = QLabel("", sk)
        self.lbl_detect.setStyleSheet(
            f"font-size:8pt;font-weight:700;color:{EMERALD};"
            f"padding:2px 8px;background:rgba(16,229,153,0.10);border-radius:5px;"
        )
        self.lbl_detect.hide()
        skl.addWidget(self.lbl_detect)

        self.lbl_result = QLabel("", sk)
        self.lbl_result.setStyleSheet(f"font-size:8.5pt;font-weight:600;color:{EMERALD};")
        self.lbl_result.setWordWrap(True)
        skl.addWidget(self.lbl_result)
        pl.addWidget(sk)

        # Provider & Model
        pl.addWidget(self._section_label("Provider & Model"))
        prov_card = self._card()
        prow_l = QVBoxLayout(prov_card)
        prow_l.setContentsMargins(14, 10, 14, 10)
        prow_l.setSpacing(8)

        prow = QHBoxLayout()
        prow.addWidget(self._make_rlabel("Active Backend", "Select AI provider backend"), 1)
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(["Google Gemini", "OpenAI", "Anthropic Claude", "Ollama (Local)", "Custom Endpoint"])
        self.combo_provider.currentIndexChanged.connect(self._on_provider_changed)
        prow.addWidget(self.combo_provider)
        prow_l.addLayout(prow)

        mrow = QHBoxLayout()
        mrow.addWidget(self._make_rlabel("Active Model", "Model identifier for screen reasoning"), 1)
        self.combo_active_model = QComboBox()
        self.combo_active_model.addItems([
            "gemini-2.5-flash-lite", "gemini-2.5-flash-8b",
            "gemini-2.0-flash", "gemini-2.0-flash-lite",
            "gemini-2.5-flash", "gemini-1.5-flash",
            "gpt-4o", "gpt-4o-mini",
            "claude-3-5-sonnet-20241022"
        ])
        mrow.addWidget(self.combo_active_model)
        prow_l.addLayout(mrow)
        pl.addWidget(prov_card)

        # Prompt Strategy
        pl.addWidget(self._section_label("Prompt Strategy"))
        strat_card = self._card()
        srl = QVBoxLayout(strat_card)
        srl.setContentsMargins(14, 10, 14, 10)
        srl.setSpacing(6)

        self.combo_prompt_preset = QComboBox()
        self.combo_prompt_preset.addItems([
            "Direct Answer Only (Recommended)",
            "Concise Solution & Reasoning",
            "Multiple Choice Detective",
            "Code Only (Optimal)",
            "Step-by-Step Instructions",
            "Custom Prompt",
        ])
        self.combo_prompt_preset.currentIndexChanged.connect(self._on_prompt_preset_changed)
        srl.addWidget(self.combo_prompt_preset)

        self.text_custom_prompt = QTextEdit()
        self.text_custom_prompt.setMaximumHeight(55)
        self.text_custom_prompt.setPlaceholderText("Enter custom system prompt here...")
        self.text_custom_prompt.setEnabled(False)
        srl.addWidget(self.text_custom_prompt)
        pl.addWidget(strat_card)
        pl.addStretch()

        return self._scrollable(page)

    # ── Hotkeys Page ─────────────────────────────────────────────
    def _build_hotkeys_page(self) -> QWidget:
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(10)

        # Keyboard panel
        pl.addWidget(self._section_label("Visual Key Selector"))
        kb_card = self._card()
        kbl = QVBoxLayout(kb_card)
        kbl.setContentsMargins(10, 10, 10, 10)
        kbl.setSpacing(4)

        hint = QLabel("Click a function's  Bind  button, then press any key (or modifier+key) on the keyboard below.")
        hint.setStyleSheet(f"font-size:8pt;color:{SUBTLE};font-style:italic;")
        hint.setWordWrap(True)
        kbl.addWidget(hint)
        kbl.addWidget(self._vkb)
        pl.addWidget(kb_card)

        # Hotkey rows
        pl.addWidget(self._section_label("Trigger Bindings"))
        hk_card = self._card()
        hk_l = QVBoxLayout(hk_card)
        hk_l.setContentsMargins(0, 4, 0, 4)
        hk_l.setSpacing(2)

        hk_defs = [
            ("Primary Scan Solve", "Capture & solve screen", "hotkey_scan", "ctrl+alt+s"),
            ("Quick Scan Trigger", "Single-key instant scan", "hotkey_quick_scan", "f9"),
            ("Instant Panic Hide", "Instant smooth HUD vanish", "hotkey_panic", "esc"),
            ("Open Control Center", "Open this settings window", "hotkey_settings", "ctrl+alt+o"),
            ("Repeat Last Answer", "Re-show cached solution", "hotkey_repeat", "ctrl+alt+r"),
        ]

        for name, desc, key, default in hk_defs:
            row_widget = HotkeyBindRow(name, desc, key, default, self._vkb)
            self._hk_rows[key] = row_widget
            # Add separator line
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background:{BORDER};margin:0 12px;")
            hk_l.addWidget(row_widget)
            hk_l.addWidget(sep)

        pl.addWidget(hk_card)

        reset_btn = QPushButton("↺ Reset All Hotkeys to Defaults")
        reset_btn.setObjectName("BtnAction")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_hotkeys)
        pl.addWidget(reset_btn)

        info = QLabel("💡 Uses Windows RegisterHotKey — works in background even when window is not focused. F-keys work without modifiers.")
        info.setStyleSheet(f"color:{SUBTLE};font-size:8pt;background:rgba(255,255,255,0.02);padding:8px 10px;border-radius:8px;")
        info.setWordWrap(True)
        pl.addWidget(info)
        pl.addStretch()

        return self._scrollable(page)

    # ── HUD Visuals Page ──────────────────────────────────────────
    def _build_visuals_page(self) -> QWidget:
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(10)

        # Simple Mode
        pl.addWidget(self._section_label("Stealth Display Mode"))
        simple_card = QFrame()
        simple_card.setObjectName("SimpleModeCard")
        sml = QVBoxLayout(simple_card)
        sml.setContentsMargins(14, 12, 14, 12)
        sml.setSpacing(6)

        s_top = QHBoxLayout()
        s_lbl = QVBoxLayout()
        s_title = QLabel("⚡ S1mple Stealth Mode — Pure Transparent Text")
        s_title.setStyleSheet(f"font-size:9.5pt;font-weight:700;color:{EMERALD};")
        s_desc = QLabel("Transforms the HUD into a pure transparent window with white text. Fully movable & resizable. No headers or chrome.")
        s_desc.setStyleSheet(f"font-size:8pt;color:{SUBTLE};")
        s_desc.setWordWrap(True)
        s_lbl.addWidget(s_title)
        s_lbl.addWidget(s_desc)
        s_top.addLayout(s_lbl, 1)
        self.switch_simple_mode = ModernSwitch(active_color=EMERALD)
        s_top.addWidget(self.switch_simple_mode)
        sml.addLayout(s_top)
        pl.addWidget(simple_card)

        # Theme Selector
        pl.addWidget(self._section_label("HUD Luxury Theme"))
        theme_card = self._card()
        tml = QVBoxLayout(theme_card)
        tml.setContentsMargins(10, 8, 10, 8)
        tml.setSpacing(6)

        grid = QGridLayout()
        grid.setSpacing(6)
        self._active_theme_key = self.config.get("hud_theme", "midnight_obsidian")

        for idx, (t_key, t_data) in enumerate(HUD_THEMES.items()):
            card_btn = QFrame()
            card_btn.setObjectName("ThemeCardWidgetActive" if t_key == self._active_theme_key else "ThemeCardWidget")
            card_btn.setCursor(Qt.CursorShape.PointingHandCursor)

            c_lay = QHBoxLayout(card_btn)
            c_lay.setContentsMargins(8, 6, 8, 6)
            c_lay.setSpacing(8)

            swatch = QLabel("●")
            swatch.setStyleSheet(f"color:{t_data['accent']};font-size:14pt;")
            c_lay.addWidget(swatch)

            t_info = QVBoxLayout()
            t_info.setSpacing(1)
            t_name = QLabel(t_data["name"])
            t_name.setStyleSheet(f"font-size:8.5pt;font-weight:700;color:{BRIGHT};")
            t_sub = QLabel(t_data["desc"])
            t_sub.setStyleSheet(f"font-size:7.5pt;color:{SUBTLE};")
            t_info.addWidget(t_name)
            t_info.addWidget(t_sub)
            c_lay.addLayout(t_info, 1)

            card_btn.mouseReleaseEvent = lambda e, k=t_key: self._select_theme(k)
            self._theme_cards[t_key] = card_btn
            grid.addWidget(card_btn, idx // 2, idx % 2)

        tml.addLayout(grid)
        pl.addWidget(theme_card)

        # Opacity & Font
        pl.addWidget(self._section_label("Opacity & Typography"))
        op_card = self._card()
        opl = QVBoxLayout(op_card)
        opl.setContentsMargins(14, 10, 14, 10)
        opl.setSpacing(10)

        def slider_row(title, desc, attr_name, lo, hi, unit, default):
            row = QHBoxLayout()
            row.addWidget(self._make_rlabel(title, desc), 1)
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(lo, hi)
            sl.setFixedWidth(130)
            lv = QLabel(f"{default}{unit}")
            lv.setFixedWidth(42)
            lv.setStyleSheet(f"color:{INDIGO_H};font-weight:700;")
            sl.valueChanged.connect(lambda v, lv=lv, u=unit: lv.setText(f"{v}{u}"))
            row.addWidget(sl)
            row.addWidget(lv)
            setattr(self, attr_name, sl)
            setattr(self, attr_name + "_val", lv)
            opl.addLayout(row)

        slider_row("Active Opacity", "Overlay opacity when in focus", "slider_opacity", 20, 100, "%", 90)
        slider_row("Ghost Dim Opacity", "Auto-dims when cursor leaves HUD", "slider_idle", 5, 80, "%", 45)
        slider_row("Font Scale", "Text size in points", "slider_font_size", 8, 22, "pt", 11)
        slider_row("Auto-Hide Delay", "Seconds before HUD auto-hides (0 = never)", "slider_autohide", 0, 60, "s", 0)

        # Font Family
        ff_row = QHBoxLayout()
        ff_row.addWidget(self._make_rlabel("Font Family", "Primary HUD typography font"), 1)
        self.combo_font_family = QComboBox()
        self.combo_font_family.addItems(["Inter", "Segoe UI", "JetBrains Mono", "Consolas", "Roboto", "Arial"])
        ff_row.addWidget(self.combo_font_family)
        opl.addLayout(ff_row)
        pl.addWidget(op_card)

        # Position
        pl.addWidget(self._section_label("Screen Position"))
        pos_card = self._card()
        posl = QVBoxLayout(pos_card)
        posl.setContentsMargins(14, 10, 14, 10)
        posl.setSpacing(8)

        p_row = QHBoxLayout()
        p_row.addWidget(self._make_rlabel("Position Preset", "Anchor location on primary display"), 1)
        self.combo_position = QComboBox()
        self.combo_position.addItems([
            "Top-Left (Default)", "Top-Right", "Top-Center",
            "Bottom-Left", "Bottom-Right", "Bottom-Center",
            "Center Screen", "Custom (Freeform drag)"
        ])
        p_row.addWidget(self.combo_position)
        posl.addLayout(p_row)
        pl.addWidget(pos_card)

        # Visual Toggles
        togg_card = self._card()
        tgl = QVBoxLayout(togg_card)
        tgl.setContentsMargins(14, 10, 14, 10)
        tgl.setSpacing(8)

        self.switch_hover_dim = ModernSwitch(checked=True)
        tgl.addWidget(self._build_setting_row("Ghost Dimming", "Auto-dim when cursor is outside the HUD", self.switch_hover_dim))

        self.switch_animations = ModernSwitch(checked=True)
        tgl.addWidget(self._build_setting_row("Fluid Animations", "Smooth spring fades and micro-transitions", self.switch_animations))
        pl.addWidget(togg_card)
        pl.addStretch()

        return self._scrollable(page)

    def _select_theme(self, theme_key: str):
        self._active_theme_key = theme_key
        for k, card in self._theme_cards.items():
            card.setObjectName("ThemeCardWidgetActive" if k == theme_key else "ThemeCardWidget")
            card.setStyleSheet("")
            self.style().unpolish(card)
            self.style().polish(card)

    # ── Stealth Page ─────────────────────────────────────────────
    def _build_stealth_page(self) -> QWidget:
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(10)

        pl.addWidget(self._section_label("Screen-Share & Capture Bypass"))
        st_card = self._card("StealthCard")
        stl = QVBoxLayout(st_card)
        stl.setContentsMargins(14, 10, 14, 10)
        stl.setSpacing(8)

        self.switch_exclude_capture = ModernSwitch(checked=True)
        stl.addWidget(self._build_setting_row(
            "Screen-Share Invisibility",
            "Hides HUD from Zoom, Teams, Discord & OBS via WDA_EXCLUDEFROMCAPTURE",
            self.switch_exclude_capture
        ))

        self.switch_click_through = ModernSwitch(checked=False)
        stl.addWidget(self._build_setting_row(
            "Click-Through Mode",
            "Mouse clicks pass through the HUD to underlying windows",
            self.switch_click_through
        ))

        self.switch_alttab_hide = ModernSwitch(checked=False)
        stl.addWidget(self._build_setting_row(
            "Hide from Alt-Tab",
            "Makes HUD invisible in the Windows Alt-Tab switcher (Tool Window mode)",
            self.switch_alttab_hide
        ))

        self.switch_taskbar_hide = ModernSwitch(checked=True)
        stl.addWidget(self._build_setting_row(
            "Hide from Taskbar",
            "Prevents HUD from appearing in the Windows taskbar",
            self.switch_taskbar_hide
        ))
        pl.addWidget(st_card)

        pl.addWidget(self._section_label("Anti-Detection Settings"))
        det_card = self._card()
        detl = QVBoxLayout(det_card)
        detl.setContentsMargins(14, 10, 14, 10)
        detl.setSpacing(10)

        # Capture delay slider
        delay_row = QHBoxLayout()
        delay_row.addWidget(self._make_rlabel(
            "Pre-Capture Delay",
            "Milliseconds delay before screenshot (helps avoid detection on key press)"
        ), 1)
        self.slider_capture_delay = QSlider(Qt.Orientation.Horizontal)
        self.slider_capture_delay.setRange(0, 500)
        self.slider_capture_delay.setFixedWidth(120)
        self.lbl_capture_delay_val = QLabel("0ms")
        self.lbl_capture_delay_val.setFixedWidth(40)
        self.lbl_capture_delay_val.setStyleSheet(f"color:{INDIGO_H};font-weight:700;")
        self.slider_capture_delay.valueChanged.connect(
            lambda v: self.lbl_capture_delay_val.setText(f"{v}ms")
        )
        delay_row.addWidget(self.slider_capture_delay)
        delay_row.addWidget(self.lbl_capture_delay_val)
        detl.addLayout(delay_row)

        # Window title masking
        wt_row = QHBoxLayout()
        wt_row.addWidget(self._make_rlabel(
            "Window Title Masking",
            "Custom title shown in Alt-Tab and task managers"
        ), 1)
        self.input_window_title = QLineEdit()
        self.input_window_title.setPlaceholderText("Windows Desktop Window Helper")
        self.input_window_title.setMaximumWidth(220)
        wt_row.addWidget(self.input_window_title)
        detl.addLayout(wt_row)
        pl.addWidget(det_card)

        pl.addWidget(self._section_label("Process Identity"))
        dis_card = self._card()
        disl = QVBoxLayout(dis_card)
        disl.setContentsMargins(14, 10, 14, 10)
        disl.setSpacing(4)

        lbl1 = QLabel("💼  Process Name: DesktopWindowHelper.exe")
        lbl1.setStyleSheet(f"color:{BRIGHT};font-weight:600;")
        lbl2 = QLabel("🏷  Description: Windows Desktop Window Helper Service")
        lbl2.setStyleSheet(f"color:{SUBTLE};font-size:8pt;")
        lbl3 = QLabel("🔒  API Keys: AES-encrypted with Windows DPAPI (user+machine locked)")
        lbl3.setStyleSheet(f"color:{SUBTLE};font-size:8pt;")
        disl.addWidget(lbl1)
        disl.addWidget(lbl2)
        disl.addWidget(lbl3)
        pl.addWidget(dis_card)

        # Emergency wipe
        pl.addWidget(self._section_label("Emergency Controls"))
        emer_card = self._card()
        emerl = QHBoxLayout(emer_card)
        emerl.setContentsMargins(14, 10, 14, 10)
        emerl.setSpacing(12)

        wipe_lbl = self._make_rlabel(
            "🗑 Emergency Wipe",
            "Instantly clears all API keys and resets configuration to defaults"
        )
        self.btn_wipe = QPushButton("Wipe & Reset")
        self.btn_wipe.setObjectName("BtnDanger")
        self.btn_wipe.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_wipe.clicked.connect(self._emergency_wipe)
        emerl.addWidget(wipe_lbl, 1)
        emerl.addWidget(self.btn_wipe)
        pl.addWidget(emer_card)
        pl.addStretch()

        return self._scrollable(page)

    # ── System Page ───────────────────────────────────────────────
    def _build_system_page(self) -> QWidget:
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(10)

        pl.addWidget(self._section_label("Application Preferences"))
        pref_card = self._card()
        prl = QVBoxLayout(pref_card)
        prl.setContentsMargins(14, 10, 14, 10)
        prl.setSpacing(8)

        self.switch_auto_copy = ModernSwitch(checked=False)
        prl.addWidget(self._build_setting_row(
            "Auto-Copy Answer",
            "Automatically copy solution to clipboard when scan finishes",
            self.switch_auto_copy
        ))

        self.switch_sound_alert = ModernSwitch(checked=False)
        prl.addWidget(self._build_setting_row(
            "Audio Notification",
            "Soft sound cue when AI finishes reasoning",
            self.switch_sound_alert
        ))

        self.switch_autostart = ModernSwitch(checked=False)
        prl.addWidget(self._build_setting_row(
            "Launch on Windows Startup",
            "Start silently in notification tray on Windows login",
            self.switch_autostart
        ))
        pl.addWidget(pref_card)

        pl.addWidget(self._section_label("Capture Engine"))
        cap_card = self._card()
        cpl = QVBoxLayout(cap_card)
        cpl.setContentsMargins(14, 10, 14, 10)
        cpl.setSpacing(8)

        c_row = QHBoxLayout()
        c_row.addWidget(self._make_rlabel("Capture Resolution", "Screenshot compression quality preset"), 1)
        self.combo_capture_quality = QComboBox()
        self.combo_capture_quality.addItems(["Ultra (Full Native Res)", "Balanced (1080p Optimized)", "Fast (High Compression)"])
        c_row.addWidget(self.combo_capture_quality)
        cpl.addLayout(c_row)

        mon_row = QHBoxLayout()
        mon_row.addWidget(self._make_rlabel("Monitor Index", "Which display to capture (0 = primary)"), 1)
        self.combo_monitor = QComboBox()
        self.combo_monitor.addItems(["0 — Primary", "1 — Secondary", "2 — Tertiary"])
        mon_row.addWidget(self.combo_monitor)
        cpl.addLayout(mon_row)
        pl.addWidget(cap_card)

        info = QLabel(
            "📦  Standalone Binary: dist/DesktopWindowHelper.exe\n"
            "No Python or dependencies required on target machine. Disguised in Task Manager."
        )
        info.setStyleSheet(f"color:{SUBTLE};font-size:8pt;background:rgba(255,255,255,0.02);padding:10px;border-radius:8px;")
        info.setWordWrap(True)
        pl.addWidget(info)
        pl.addStretch()

        return self._scrollable(page)

    # ── Action Bar ────────────────────────────────────────────────
    def _build_action_bar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(
            f"background:{VOID};border-top:1px solid {BORDER};"
            f"border-bottom-left-radius:16px;border-bottom-right-radius:16px;"
        )
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(16, 0, 16, 0)
        bl.setSpacing(8)

        self.btn_preview = QPushButton("👁 Toggle HUD")
        self.btn_preview.setObjectName("BtnAction")
        self.btn_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_preview.clicked.connect(lambda: self.toggle_preview.emit())

        self.btn_scan_now = QPushButton("⚡ Scan Now")
        self.btn_scan_now.setObjectName("BtnAction")
        self.btn_scan_now.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scan_now.clicked.connect(lambda: self.trigger_test_scan.emit())

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("BtnCancel")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.hide)

        self.btn_save = QPushButton("💾  Save & Apply")
        self.btn_save.setObjectName("BtnSave")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._on_save_clicked)

        bl.addWidget(self.btn_preview)
        bl.addWidget(self.btn_scan_now)
        bl.addStretch()
        bl.addWidget(self.btn_cancel)
        bl.addWidget(self.btn_save)

        return bar

    # ── Logic ─────────────────────────────────────────────────────
    def _toggle_eye(self):
        if self.input_smart_key.echoMode() == QLineEdit.EchoMode.Password:
            self.input_smart_key.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.input_smart_key.setEchoMode(QLineEdit.EchoMode.Password)

    def _on_smart_key_typed(self, text: str):
        raw = text.strip()
        if not raw:
            self.lbl_detect.hide()
            return
        _, pname = auto_detect_provider(raw)
        self.lbl_detect.setText(f"✦ {pname} Detected")
        self.lbl_detect.show()

    def _auto_configure_smart_key(self):
        """Non-blocking: runs test_smart_key in a background QThread."""
        key = self.input_smart_key.text().strip()
        if not key:
            self.lbl_result.setText("⚠ Please enter an API key first.")
            self.lbl_result.setStyleSheet(f"color:{CRIMSON};")
            return

        # Prevent double-click
        if self._auto_config_thread and self._auto_config_thread.isRunning():
            return

        self.lbl_result.setText("⏳ Connecting & discovering models…")
        self.lbl_result.setStyleSheet(f"color:{AMBER};")
        self.btn_auto.setEnabled(False)

        self._auto_config_thread = QThread(self)
        self._auto_config_worker = AutoConfigWorker(self.ai_engine, key)
        self._auto_config_worker.moveToThread(self._auto_config_thread)
        self._auto_config_thread.started.connect(self._auto_config_worker.run)
        self._auto_config_worker.finished.connect(self._on_auto_config_finished)
        self._auto_config_worker.finished.connect(self._auto_config_thread.quit)
        self._auto_config_thread.start()

        # Spinner animation while waiting
        self._spinner_dots = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(400)
        self._spinner_timer.timeout.connect(self._spin_label)
        self._spinner_timer.start()

    def _spin_label(self):
        dots = "." * (self._spinner_dots % 4)
        self.lbl_result.setText(f"⏳ Connecting & discovering models{dots}")
        self._spinner_dots += 1

    def _on_auto_config_finished(self, success: bool, prov: str, best_model: str, msg: str):
        if hasattr(self, "_spinner_timer"):
            self._spinner_timer.stop()
        self.btn_auto.setEnabled(True)

        if success:
            self.lbl_result.setText(f"✓ {msg}")
            self.lbl_result.setStyleSheet(f"color:{EMERALD};")
            prov_map = {"gemini": 0, "openai": 1, "claude": 2, "ollama": 3, "custom": 4}
            self.combo_provider.setCurrentIndex(prov_map.get(prov, 0))
            if best_model:
                if self.combo_active_model.findText(best_model) == -1:
                    self.combo_active_model.addItem(best_model)
                self.combo_active_model.setCurrentText(best_model)
            # Mask key back to password mode for security
            self.input_smart_key.setEchoMode(QLineEdit.EchoMode.Password)
            self.config_updated.emit()
        else:
            self.lbl_result.setText(f"✗ {msg}")
            self.lbl_result.setStyleSheet(f"color:{CRIMSON};")

    def _on_provider_changed(self):
        prov = ["gemini", "openai", "claude", "ollama", "custom"][self.combo_provider.currentIndex()]
        if prov == "gemini":
            self.combo_active_model.clear()
            self.combo_active_model.addItems([
                "gemini-2.5-flash-lite", "gemini-2.5-flash-8b",
                "gemini-2.0-flash", "gemini-2.0-flash-lite",
                "gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro",
            ])
        elif prov == "openai":
            self.combo_active_model.clear()
            self.combo_active_model.addItems(["gpt-4o", "gpt-4o-mini"])
        elif prov == "claude":
            self.combo_active_model.clear()
            self.combo_active_model.addItems(["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"])

    def _on_prompt_preset_changed(self):
        self.text_custom_prompt.setEnabled(self.combo_prompt_preset.currentIndex() == 5)

    def _reset_hotkeys(self):
        defaults = {
            "hotkey_scan": "ctrl+alt+s",
            "hotkey_quick_scan": "f9",
            "hotkey_panic": "esc",
            "hotkey_settings": "ctrl+alt+o",
            "hotkey_repeat": "ctrl+alt+r",
        }
        for k, v in defaults.items():
            if k in self._hk_rows:
                self._hk_rows[k].set_combo(v)

    def _emergency_wipe(self):
        """Clear all API keys and reset to defaults."""
        from .config import DEFAULT_CONFIG
        self.config.data.clear()
        self.config.data.update(DEFAULT_CONFIG.copy())
        self.config.save()
        self.load_from_config()
        self.lbl_result.setText("🗑 Config wiped. All keys cleared.")
        self.lbl_result.setStyleSheet(f"color:{AMBER};font-weight:700;")
        self.config_updated.emit()

    def load_from_config(self):
        prov = self.config.get("ai_provider", "gemini").lower()
        prov_map = {"gemini": 0, "openai": 1, "claude": 2, "ollama": 3, "custom": 4}
        self.combo_provider.setCurrentIndex(prov_map.get(prov, 0))

        active_key = self.config.get_decrypted_key(prov)
        self.input_smart_key.setText(active_key)
        if active_key:
            self._on_smart_key_typed(active_key)

        model_key = f"{prov}_model"
        active_model = self.config.get(model_key, "gemini-2.0-flash")
        if self.combo_active_model.findText(active_model) == -1:
            self.combo_active_model.addItem(active_model)
        self.combo_active_model.setCurrentText(active_model)

        preset_map = {
            "direct_answer": 0, "concise_solution": 1, "multiple_choice": 2,
            "code_only": 3, "step_by_step": 4, "custom": 5
        }
        self.combo_prompt_preset.setCurrentIndex(
            preset_map.get(self.config.get("prompt_preset", "direct_answer"), 0)
        )
        self.text_custom_prompt.setPlainText(self.config.get("custom_system_prompt", ""))

        self.switch_simple_mode.setChecked(bool(self.config.get("simple_stealth_mode", False)), animate=False)

        theme = self.config.get("hud_theme", "midnight_obsidian")
        self._select_theme(theme)

        op = int(float(self.config.get("overlay_opacity", 0.90)) * 100)
        self.slider_opacity.setValue(op)
        self.slider_opacity_val.setText(f"{op}%")

        idle_op = int(float(self.config.get("idle_opacity", 0.45)) * 100)
        self.slider_idle.setValue(idle_op)
        self.slider_idle_val.setText(f"{idle_op}%")

        fs = int(self.config.get("font_size", 11))
        self.slider_font_size.setValue(fs)
        self.slider_font_size_val.setText(f"{fs}pt")

        ah = int(self.config.get("auto_hide_seconds", 0))
        self.slider_autohide.setValue(ah)
        self.slider_autohide_val.setText(f"{ah}s")

        ff = self.config.get("font_family", "Inter")
        idx_ff = self.combo_font_family.findText(ff)
        if idx_ff != -1:
            self.combo_font_family.setCurrentIndex(idx_ff)

        pos_map = {
            "top_left": 0, "top_right": 1, "top_center": 2,
            "bottom_left": 3, "bottom_right": 4, "bottom_center": 5,
            "center": 6, "custom": 7
        }
        self.combo_position.setCurrentIndex(pos_map.get(self.config.get("overlay_position", "top_left"), 0))

        self.switch_hover_dim.setChecked(bool(self.config.get("hover_dimming", True)), animate=False)
        self.switch_animations.setChecked(bool(self.config.get("enable_animations", True)), animate=False)
        self.switch_exclude_capture.setChecked(bool(self.config.get("stealth_exclude_capture", True)), animate=False)
        self.switch_click_through.setChecked(bool(self.config.get("click_through", False)), animate=False)
        self.switch_alttab_hide.setChecked(bool(self.config.get("alttab_hide", False)), animate=False)
        self.switch_taskbar_hide.setChecked(bool(self.config.get("taskbar_hide", True)), animate=False)
        self.switch_auto_copy.setChecked(bool(self.config.get("auto_copy_clipboard", False)), animate=False)
        self.switch_sound_alert.setChecked(bool(self.config.get("sound_alert", False)), animate=False)
        self.switch_autostart.setChecked(bool(self.config.get("autostart", False)), animate=False)

        cap_q = self.config.get("capture_quality", "balanced")
        cap_map = {"ultra": 0, "balanced": 1, "fast": 2}
        self.combo_capture_quality.setCurrentIndex(cap_map.get(cap_q, 1))

        mon_idx = int(self.config.get("monitor_index", 0))
        self.combo_monitor.setCurrentIndex(min(mon_idx, 2))

        cap_delay = int(self.config.get("capture_delay_ms", 0))
        self.slider_capture_delay.setValue(cap_delay)
        self.lbl_capture_delay_val.setText(f"{cap_delay}ms")

        self.input_window_title.setText(self.config.get("window_title_mask", ""))

        for k, row_widget in self._hk_rows.items():
            row_widget.set_combo(self.config.get(k, row_widget.get_combo()))

    def _on_save_clicked(self):
        providers = ["gemini", "openai", "claude", "ollama", "custom"]
        prov = providers[self.combo_provider.currentIndex()]
        self.config.set("ai_provider", prov)

        smart_key = self.input_smart_key.text().strip()
        if smart_key:
            self.config.set(f"{prov}_api_key", smart_key)

        model_val = self.combo_active_model.currentText()
        if model_val:
            self.config.set(f"{prov}_model", model_val)

        preset_keys = ["direct_answer", "concise_solution", "multiple_choice",
                       "code_only", "step_by_step", "custom"]
        self.config.set("prompt_preset", preset_keys[self.combo_prompt_preset.currentIndex()])
        self.config.set("custom_system_prompt", self.text_custom_prompt.toPlainText().strip())

        self.config.set("simple_stealth_mode", self.switch_simple_mode.isChecked())
        self.config.set("hud_theme", self._active_theme_key)
        self.config.set("overlay_opacity", round(self.slider_opacity.value() / 100.0, 2))
        self.config.set("idle_opacity", round(self.slider_idle.value() / 100.0, 2))
        self.config.set("hover_dimming", self.switch_hover_dim.isChecked())
        self.config.set("enable_animations", self.switch_animations.isChecked())
        self.config.set("font_size", self.slider_font_size.value())
        self.config.set("auto_hide_seconds", self.slider_autohide.value())
        self.config.set("font_family", self.combo_font_family.currentText())

        pos_keys = ["top_left", "top_right", "top_center", "bottom_left",
                    "bottom_right", "bottom_center", "center", "custom"]
        self.config.set("overlay_position", pos_keys[self.combo_position.currentIndex()])

        self.config.set("stealth_exclude_capture", self.switch_exclude_capture.isChecked())
        self.config.set("click_through", self.switch_click_through.isChecked())
        self.config.set("alttab_hide", self.switch_alttab_hide.isChecked())
        self.config.set("taskbar_hide", self.switch_taskbar_hide.isChecked())
        self.config.set("auto_copy_clipboard", self.switch_auto_copy.isChecked())
        self.config.set("sound_alert", self.switch_sound_alert.isChecked())

        cap_keys = ["ultra", "balanced", "fast"]
        self.config.set("capture_quality", cap_keys[self.combo_capture_quality.currentIndex()])
        self.config.set("monitor_index", self.combo_monitor.currentIndex())
        self.config.set("capture_delay_ms", self.slider_capture_delay.value())
        self.config.set("window_title_mask", self.input_window_title.text().strip())

        for k, row_widget in self._hk_rows.items():
            self.config.set(k, row_widget.get_combo().strip().lower())

        autostart = self.switch_autostart.isChecked()
        self.config.set("autostart", autostart)
        self._apply_autostart_registry(autostart)

        self.config.save()
        self.config_updated.emit()
        self.hide()

    def _apply_autostart_registry(self, enable: bool):
        if sys.platform != "win32":
            return
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            if enable:
                exe_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, "DesktopWindowHelper", 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(key, "DesktopWindowHelper")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass
