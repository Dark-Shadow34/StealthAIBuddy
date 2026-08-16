import sys
import html
import re
import ctypes
import time
from typing import Optional

from PySide6.QtCore import (
    Qt, QPoint, QTimer, Signal, QPropertyAnimation, QEasingCurve, QEvent, QSize, QRect
)
from PySide6.QtGui import (
    QFont, QColor, QMouseEvent, QEnterEvent, QGuiApplication, QCursor
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextBrowser, QGraphicsDropShadowEffect,
    QHBoxLayout, QPushButton, QFrame, QApplication, QSizeGrip
)

from .config import ConfigManager, HUD_THEMES

# Win32 Constants
WDA_NONE               = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011
GWL_EXSTYLE            = -20
WS_EX_TRANSPARENT      = 0x00000020
WS_EX_LAYERED          = 0x00080000
SWP_NOMOVE             = 0x0002
SWP_NOSIZE             = 0x0001
SWP_NOACTIVATE         = 0x0010
SWP_SHOWWINDOW         = 0x0040
HWND_TOPMOST           = -1

INDIGO  = "#6366f1"
EMERALD = "#10e599"
CRIMSON = "#ff4d4d"
AMBER   = "#f59e0b"
BRIGHT  = "#e2e8f4"
SUBTLE  = "#6b7280"
MUTED   = "#3a4055"
WHITE   = "#ffffff"


def get_hud_qss(theme: dict, is_simple_mode: bool = False) -> str:
    card_bg = theme.get("card_bg", "rgba(8, 9, 14, 0.94)")
    border = theme.get("border", "rgba(255, 255, 255, 0.08)")
    hover_border = theme.get("hover_border", "rgba(99, 102, 241, 0.45)")
    accent = theme.get("accent", "#6366f1")
    accent_hover = theme.get("accent_hover", "#818cf8")
    muted = theme.get("muted_color", "#6b7280")
    
    if is_simple_mode:
        return f"""
QFrame#HUDCard {{
    background-color: {card_bg if theme.get('name') != 'Midnight Obsidian' else 'rgba(0, 0, 0, 0.01)'};
    border: 1px solid transparent;
    border-radius: 6px;
}}
QFrame#HUDCard:hover {{
    background-color: rgba(6, 8, 14, 0.4);
    border: 1px dashed {hover_border};
}}
QTextBrowser {{
    background: transparent;
    border: none;
}}
QTextBrowser QScrollBar:vertical {{
    background: transparent; width: 4px;
}}
QTextBrowser QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.18); border-radius: 2px; min-height: 14px;
}}
QTextBrowser QScrollBar::add-line:vertical,
QTextBrowser QScrollBar::sub-line:vertical {{ height: 0; }}
"""
    return f"""
QFrame#HUDCard {{
    background-color: {card_bg};
    border: 1px solid {border};
    border-radius: 12px;
}}
QFrame#HUDCard:hover {{
    border: 1px solid {hover_border};
}}
QFrame#HUDHeader {{
    background: rgba(255, 255, 255, 0.02);
    border-bottom: 1px solid rgba(255, 255, 255, 0.045);
}}
QLabel#HUDStatus {{
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 8.5pt;
    font-weight: 600;
    letter-spacing: 1.5px;
    color: {muted};
}}
QTextBrowser {{
    background: transparent;
    border: none;
}}
QTextBrowser QScrollBar:vertical {{
    background: rgba(255, 255, 255, 0.02); width: 4px; border-radius: 2px;
}}
QTextBrowser QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.14); border-radius: 2px; min-height: 18px;
}}
QTextBrowser QScrollBar::handle:vertical:hover {{
    background: {accent};
}}
QTextBrowser QScrollBar::add-line:vertical,
QTextBrowser QScrollBar::sub-line:vertical {{ height: 0; }}

QPushButton#HUDBtnIcon {{
    background: transparent;
    border: 1px solid transparent;
    color: #64748b;
    font-size: 11px;
    border-radius: 4px;
    padding: 1px 4px;
}}
QPushButton#HUDBtnIcon:hover {{
    background: rgba(255, 255, 255, 0.09);
    border-color: rgba(255, 255, 255, 0.15);
    color: #f1f5f9;
}}
QPushButton#HUDBtnIcon:pressed {{
    background: rgba(255, 255, 255, 0.15);
}}

QPushButton#HUDBtnScan {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {accent}, stop:1 {accent_hover});
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 5px;
    padding: 2px 9px;
    font-family: "Inter", sans-serif;
    font-size: 8.5pt;
    font-weight: 700;
}}
QPushButton#HUDBtnScan:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {accent_hover}, stop:1 {accent});
    border-color: rgba(255, 255, 255, 0.35);
}}
QPushButton#HUDBtnScan:pressed {{
    padding-top: 3px;
    padding-bottom: 1px;
}}

QPushButton#HUDBtnCopy {{
    background: rgba(255, 255, 255, 0.04);
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    padding: 2px 7px;
    font-family: "JetBrains Mono", monospace;
    font-size: 8.5pt;
}}
QPushButton#HUDBtnCopy:hover {{
    background: rgba(255, 255, 255, 0.1);
    color: {accent_hover};
    border-color: {accent};
}}

QLabel#HUDLat {{
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 8pt;
    color: #64748b;
}}
"""


def format_answer_html(text: str, font_size: int, theme: dict, font_family: str = "Inter", is_simple_mode: bool = False) -> str:
    if not text:
        return ""
    esc = html.escape(text)
    accent = theme.get("accent", INDIGO)
    text_color = theme.get("text_color", "#f1f5f9")
    code_bg = theme.get("code_bg", "rgba(15, 23, 42, 0.85)")
    code_border = theme.get("code_border", accent)

    if is_simple_mode:
        def code_block_simple(m):
            code = m.group(1).strip()
            return (
                f'<div style="background:{code_bg}; border-left: 2px solid {accent}; '
                f'padding:4px 8px; margin:4px 0; border-radius:3px; font-family:\'JetBrains Mono\',\'Consolas\',monospace; '
                f'font-size:{font_size-1}pt; color:#ffffff; text-shadow:0px 1px 3px #000;">{code}</div>'
            )
        esc = re.sub(r"```(?:[\w+-]*\n)?(.*?)```", code_block_simple, esc, flags=re.DOTALL)
        esc = re.sub(
            r"`([^`]+)`",
            rf'<span style="background:rgba(0,0,0,0.55); border:1px solid rgba(255,255,255,0.1); padding:1px 4px; border-radius:3px; font-family:\'JetBrains Mono\',monospace; color:{accent}; text-shadow:0px 1px 2px #000;">\1</span>',
            esc,
        )
        esc = re.sub(r"\*\*([^*]+)\*\*", rf'<b style="color:#ffffff; text-shadow:0px 1px 3px #000;">\1</b>', esc)

        lines = esc.split("\n")
        out = []
        for line in lines:
            s = line.strip()
            if s.startswith(("• ", "* ", "- ")):
                out.append(f'<div style="margin-left:6px; margin-bottom:2px;"><span style="color:{accent};">▸ </span>{s[2:]}</div>')
            elif re.match(r"^(Option [A-Z]:|[A-D]\)|\d+\.)\s*", s, re.IGNORECASE):
                out.append(f'<div style="color:{accent}; font-weight:700; margin-bottom:3px; font-size:{font_size}pt; text-shadow:0px 1px 3px #000;">{s}</div>')
            elif s.startswith("#"):
                clean = s.lstrip("#").strip()
                out.append(f'<div style="color:#ffffff; font-weight:700; font-size:{font_size+1}pt; margin-bottom:3px; text-shadow:0px 1px 3px #000;">{clean}</div>')
            else:
                if s:
                    out.append(f'<div style="margin-bottom:2px;">{s}</div>')
                else:
                    out.append('<div style="height:3px;"></div>')

        return (
            f'<div style="font-family:\'{font_family}\',\'Segoe UI\',sans-serif;'
            f'font-size:{font_size}pt; color:{text_color}; line-height:1.45;'
            f'text-shadow: 0px 1px 3px rgba(0,0,0,0.95), 0px 0px 2px rgba(0,0,0,0.9);">'
            f'{"".join(out)}</div>'
        )
    else:
        def code_block(m):
            code = m.group(1).strip()
            return (
                f'<div style="background:{code_bg};border:1px solid rgba(255,255,255,0.08);'
                f'border-left:3px solid {code_border};border-radius:6px;padding:6px 9px;margin:5px 0;'
                f'font-family:\'JetBrains Mono\',\'Consolas\',monospace;font-size:{font_size-1}pt;color:{accent};">'
                f'{code}</div>'
            )
        esc = re.sub(r"```(?:[\w+-]*\n)?(.*?)```", code_block, esc, flags=re.DOTALL)
        esc = re.sub(
            r"`([^`]+)`",
            rf'<span style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.08);padding:1px 5px;border-radius:3px;'
            rf'font-family:\'JetBrains Mono\',monospace;color:{accent};font-size:{font_size-1}pt;">\1</span>',
            esc,
        )
        esc = re.sub(r"\*\*([^*]+)\*\*", rf'<b style="color:#ffffff;">\1</b>', esc)

        lines = esc.split("\n")
        out = []
        for line in lines:
            s = line.strip()
            if s.startswith(("• ", "* ", "- ")):
                out.append(
                    f'<div style="margin-left:8px;margin-bottom:2px;">'
                    f'<span style="color:{accent};">▸ </span>{s[2:]}</div>'
                )
            elif re.match(r"^(Option [A-Z]:|[A-D]\)|\d+\.)\s*", s, re.IGNORECASE):
                out.append(
                    f'<div style="color:{accent};font-weight:700;margin-bottom:3px;font-size:{font_size}pt;">{s}</div>'
                )
            elif s.startswith("#"):
                clean = s.lstrip("#").strip()
                out.append(
                    f'<div style="color:#ffffff;font-weight:700;font-size:{font_size+1}pt;margin-bottom:3px;">{clean}</div>'
                )
            else:
                if s:
                    out.append(f'<div style="margin-bottom:2px;">{s}</div>')
                else:
                    out.append('<div style="height:4px;"></div>')

        return (
            f'<div style="font-family:\'{font_family}\',\'Segoe UI\',sans-serif;'
            f'font-size:{font_size}pt;color:{text_color};line-height:1.45;">{"".join(out)}</div>'
        )


class PulseLabel(QLabel):
    def __init__(self, text="●", parent=None):
        super().__init__(text, parent)
        self._alpha = 1.0
        self._dir   = -1
        self._color = EMERALD
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._apply()

    def start_pulse(self, color: str = EMERALD):
        self._color = color
        if not self._timer.isActive():
            self._timer.start(45)

    def stop_pulse(self, color: str = EMERALD):
        self._timer.stop()
        self._color = color
        self._alpha = 1.0
        self._apply()

    def _tick(self):
        self._alpha += 0.07 * self._dir
        if self._alpha <= 0.2: self._alpha = 0.2; self._dir = 1
        elif self._alpha >= 1.0: self._alpha = 1.0; self._dir = -1
        self._apply()

    def _apply(self):
        h = self._color.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        a = int(self._alpha * 255)
        self.setStyleSheet(f"color: rgba({r},{g},{b},{a}); font-size: 8pt;")


class StealthOverlayHUD(QWidget):
    update_text_signal = Signal(str, str)
    hide_signal        = Signal()
    show_signal        = Signal()
    scan_clicked       = Signal()
    settings_clicked   = Signal()
    font_size_changed  = Signal(int)

    # Resize margin in pixels
    RESIZE_MARGIN = 14

    def __init__(self, config_mgr: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config_mgr
        self.setObjectName("HUDOuter")

        self._is_dragging    = False
        self._is_resizing    = False
        self._drag_position  = QPoint()
        self._resize_start_geo = None
        self._resize_start_pos = None
        self._resize_mode    = None  # 'bottom_right', 'right', 'bottom'
        self._raw_content    = ""
        self._is_hovered     = False
        self._user_hidden    = False  # True after explicit panic/close; suppresses auto-show

        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hide_overlay)

        self._anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        self._anim_opacity.setDuration(160)
        self._anim_opacity.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)

        self._init_ui()
        self.apply_config()

        self.update_text_signal.connect(self._on_update_content)
        self.hide_signal.connect(self.hide_overlay)
        self.show_signal.connect(self.show_overlay)

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(0)

        self.card = QFrame(self)
        self.card.setObjectName("HUDCard")
        card_l = QVBoxLayout(self.card)
        card_l.setContentsMargins(0, 0, 0, 0)
        card_l.setSpacing(0)

        # ── Header ──
        self.header = QFrame(self.card)
        self.header.setObjectName("HUDHeader")
        self.header.setFixedHeight(32)
        hdr_l = QHBoxLayout(self.header)
        hdr_l.setContentsMargins(8, 0, 6, 0)
        hdr_l.setSpacing(5)

        self.pulse_dot = PulseLabel("●", self.header)
        self.pulse_dot.setFixedWidth(12)
        self.status_label = QLabel("STEALTH AI · READY", self.header)
        self.status_label.setObjectName("HUDStatus")

        hdr_l.addWidget(self.pulse_dot)
        hdr_l.addWidget(self.status_label)
        hdr_l.addStretch()

        self.btn_copy = QPushButton("⎘", self.header)
        self.btn_copy.setObjectName("HUDBtnCopy")
        self.btn_copy.setFixedSize(QSize(32, 19))
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy.setToolTip("Copy solution")
        self.btn_copy.clicked.connect(self._copy_to_clipboard)

        self.btn_scan = QPushButton("⚡ Scan", self.header)
        self.btn_scan.setObjectName("HUDBtnScan")
        self.btn_scan.setFixedHeight(19)
        self.btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scan.setToolTip("Scan Screen (F9)")
        self.btn_scan.clicked.connect(lambda: self.scan_clicked.emit())

        self.btn_font_dec = self._icon_btn("A⁻", "Smaller font")
        self.btn_font_dec.clicked.connect(self._decrease_font)
        self.btn_font_inc = self._icon_btn("A⁺", "Larger font")
        self.btn_font_inc.clicked.connect(self._increase_font)

        self.btn_settings = self._icon_btn("⚙", "Settings (Ctrl+Alt+O)")
        self.btn_settings.clicked.connect(lambda: self.settings_clicked.emit())

        self.btn_close = self._icon_btn("✕", "Hide (Esc)")
        self.btn_close.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#4b5563;font-size:10px;border-radius:4px;}"
            "QPushButton:hover{background:rgba(255,77,77,0.15);color:#ff4d4d;}"
        )
        self.btn_close.clicked.connect(self.hide_overlay)

        for w in [self.btn_copy, self.btn_scan, self.btn_font_dec,
                  self.btn_font_inc, self.btn_settings, self.btn_close]:
            hdr_l.addWidget(w)

        card_l.addWidget(self.header)

        # ── Divider ──
        self.divider = QFrame(self.card)
        self.divider.setFixedHeight(1)
        self.divider.setStyleSheet("background:rgba(255,255,255,0.045);")
        card_l.addWidget(self.divider)

        # ── Text Area ──
        self.text_area = QTextBrowser(self.card)
        self.text_area.setOpenExternalLinks(False)
        self.text_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_area.setFrameShape(QFrame.Shape.NoFrame)
        self.text_area.setContentsMargins(10, 6, 10, 4)
        card_l.addWidget(self.text_area)

        # ── Latency Footer ──
        self.lat_bar = QFrame(self.card)
        self.lat_bar.setFixedHeight(20)
        self.lat_bar.setStyleSheet(
            "background:rgba(255,255,255,0.012);"
            "border-top:1px solid rgba(255,255,255,0.035);"
        )
        lat_l = QHBoxLayout(self.lat_bar)
        lat_l.setContentsMargins(10, 0, 10, 0)
        lat_l.setSpacing(10)

        self.lbl_lat_ocr   = self._lat_lbl("OCR –")
        self.lbl_lat_ai    = self._lat_lbl("AI –")
        self.lbl_lat_total = self._lat_lbl("Total –")
        for w in [self.lbl_lat_ocr, self.lbl_lat_ai, self.lbl_lat_total]:
            lat_l.addWidget(w)
        lat_l.addStretch()

        self.lbl_model = QLabel("", self.lat_bar)
        self.lbl_model.setStyleSheet(
            f"font-family:'JetBrains Mono','Consolas',monospace;font-size:7.5pt;"
            f"color:{INDIGO};background:rgba(99,102,241,0.08);"
            f"border:1px solid rgba(99,102,241,0.2);border-radius:8px;padding:0 6px;"
        )
        lat_l.addWidget(self.lbl_model)
        card_l.addWidget(self.lat_bar)

        outer.addWidget(self.card)

        # Soft drop shadow for readability
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(24)
        self.shadow.setColor(QColor(0, 0, 0, 210))
        self.shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(self.shadow)

    def _icon_btn(self, text: str, tip: str) -> QPushButton:
        btn = QPushButton(text, self.header)
        btn.setObjectName("HUDBtnIcon")
        btn.setFixedSize(QSize(19, 19))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tip)
        return btn

    def _lat_lbl(self, text: str) -> QLabel:
        lbl = QLabel(text, self.lat_bar)
        lbl.setObjectName("HUDLat")
        return lbl

    def is_simple_mode(self) -> bool:
        return bool(self.config.get("simple_stealth_mode", False))

    def apply_config(self):
        simple = self.is_simple_mode()
        theme_key = self.config.get("hud_theme", "midnight_obsidian")
        theme = HUD_THEMES.get(theme_key, HUD_THEMES["midnight_obsidian"])
        
        ff     = self.config.get("font_family", "Inter")
        fs     = int(self.config.get("font_size", 11))
        accent = theme.get("accent", INDIGO)

        qss = get_hud_qss(theme, simple)
        self.setStyleSheet(qss)

        # Update shadow
        sh_c = theme.get("shadow_rgba", (0, 0, 0, 220))
        self.shadow.setColor(QColor(*sh_c))

        if simple:
            self.header.hide()
            self.divider.hide()
            self.lat_bar.hide()
            self.text_area.setContentsMargins(6, 4, 6, 4)
            # S1mple mode custom dimensions
            w = int(self.config.get("simple_mode_width", 380))
            h = int(self.config.get("simple_mode_height", 240))
            self.resize(w, h)
            self.setMinimumSize(180, 80)
            self.setMaximumSize(1920, 1080)
        else:
            self.header.show()
            self.divider.show()
            self.lat_bar.show()
            self.text_area.setContentsMargins(10, 6, 10, 4)
            max_w = int(self.config.get("max_width", 390))
            max_h = int(self.config.get("max_height", 480))
            self.setMinimumSize(220, 100)
            self.setMaximumSize(max_w, max_h)
            self.resize(max_w, min(240, max_h))

        # Re-render content
        if self._raw_content:
            self.text_area.setHtml(format_answer_html(self._raw_content, fs, theme, ff, simple))

        self.setWindowOpacity(float(self.config.get("overlay_opacity", 0.90)))
        self._apply_position()
        self._apply_win32_attributes()

        prov  = self.config.get("ai_provider", "gemini")
        model = self.config.get(f"{prov}_model", "")
        if model:
            short = model.replace("gemini-","").replace("-flash"," Flash").replace("-lite"," Lite")
            self.lbl_model.setText(short.title())
            self.lbl_model.setStyleSheet(
                f"font-family:'JetBrains Mono','Consolas',monospace;font-size:7.5pt;"
                f"color:{accent};background:rgba(255,255,255,0.04);"
                f"border:1px solid {accent};border-radius:8px;padding:0 6px;"
            )

    def _apply_position(self):
        simple = self.is_simple_mode()
        if simple:
            sx = int(self.config.get("simple_mode_x", 30))
            sy = int(self.config.get("simple_mode_y", 30))
            self.move(sx, sy)
            return

        pos  = self.config.get("overlay_position", "top_left")
        scr  = QApplication.primaryScreen()
        if not scr:
            return
        geo  = scr.availableGeometry()
        pad  = 14
        w, h = self.width(), self.height()
        pts  = {
            "top_left":      (geo.x()+pad, geo.y()+pad),
            "top_right":     (geo.x()+geo.width()-w-pad, geo.y()+pad),
            "top_center":    (geo.x()+(geo.width()-w)//2, geo.y()+pad),
            "bottom_left":   (geo.x()+pad, geo.y()+geo.height()-h-pad),
            "bottom_right":  (geo.x()+geo.width()-w-pad, geo.y()+geo.height()-h-pad),
            "bottom_center": (geo.x()+(geo.width()-w)//2, geo.y()+geo.height()-h-pad),
            "center":        (geo.x()+(geo.width()-w)//2, geo.y()+(geo.height()-h)//2),
        }
        if pos in pts:
            self.move(*pts[pos])
        elif pos == "custom":
            self.move(self.config.get("custom_pos_x", 14), self.config.get("custom_pos_y", 14))

    def _apply_win32_attributes(self):
        if sys.platform != "win32":
            return
        hwnd = int(self.winId())
        if not hwnd:
            return
        try:
            affinity = WDA_EXCLUDEFROMCAPTURE if self.config.get("stealth_exclude_capture", True) else WDA_NONE
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, affinity)
        except Exception:
            pass
        try:
            styles = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if self.config.get("click_through", False):
                styles |= (WS_EX_TRANSPARENT | WS_EX_LAYERED)
            else:
                styles &= ~WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, styles)
        except Exception:
            pass

    def _force_repaint(self):
        """Force Windows DWM compositor to flush immediately."""
        self.text_area.update()
        self.card.update()
        self.update()
        self.repaint()
        QApplication.processEvents()
        if sys.platform == "win32":
            try:
                ctypes.windll.user32.SetWindowPos(
                    int(self.winId()), HWND_TOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
                )
            except Exception:
                pass

    def show_status(self, status_text: str, color: str = SUBTLE, pulse: bool = False):
        if not self.is_simple_mode():
            self.status_label.setText(f"STEALTH AI · {status_text.upper()}")
            self.status_label.setStyleSheet(
                f'font-family:"JetBrains Mono","Consolas",monospace;'
                f'font-size:8.5pt;font-weight:600;letter-spacing:1.5px;color:{color};'
            )
            if pulse:
                self.pulse_dot.start_pulse(color)
            else:
                self.pulse_dot.stop_pulse(color)
        if not self.isVisible():
            self.show_overlay()

    def set_content(self, text: str, status: str = "Answer"):
        self._raw_content = text
        self.update_text_signal.emit(status, text)

    def _on_update_content(self, status: str, content: str):
        color_map = {
            "Answer": EMERALD, "Ready": EMERALD, "Preview": EMERALD, "Repeat": EMERALD,
            "Scanning...": AMBER, "Reasoning...": AMBER, "Thinking...": AMBER,
        }
        color = color_map.get(status, CRIMSON)
        pulse = status in ("Scanning...", "Reasoning...", "Thinking...")
        self.show_status(status, color, pulse=pulse)

        theme_key = self.config.get("hud_theme", "midnight_obsidian")
        theme = HUD_THEMES.get(theme_key, HUD_THEMES["midnight_obsidian"])
        fs     = int(self.config.get("font_size", 11))
        ff     = self.config.get("font_family", "Inter")
        simple = self.is_simple_mode()
        self.text_area.setHtml(format_answer_html(content, fs, theme, ff, simple))

        # Only auto-show if the user hasn't explicitly hidden the overlay
        if not self._user_hidden:
            self.show_overlay()
        self._force_repaint()

        # Dynamic resize in standard mode only (simple mode respects user's dragged dimensions)
        if not simple:
            doc_h    = int(self.text_area.document().size().height()) + 66
            max_h    = int(self.config.get("max_height", 480))
            target_h = max(110, min(doc_h, max_h))
            self.resize(self.width(), target_h)

        auto_hide = int(self.config.get("auto_hide_seconds", 0))
        if auto_hide > 0:
            self._auto_hide_timer.start(auto_hide * 1000)

    def update_latency(self, ocr_ms: int, ai_ms: int):
        if not self.is_simple_mode():
            self.lbl_lat_ocr.setText(f"OCR {ocr_ms}ms")
            self.lbl_lat_ai.setText(f"AI {ai_ms}ms")
            self.lbl_lat_total.setText(f"Total {ocr_ms + ai_ms}ms")
            self._force_repaint()

    def show_overlay(self):
        if not self.isVisible():
            if self.config.get("enable_animations", True):
                self.setWindowOpacity(0.0)
                self.show()
                self.raise_()
                target_op = float(self.config.get("overlay_opacity", 0.90))
                self._anim_opacity.stop()
                self._anim_opacity.setStartValue(0.0)
                self._anim_opacity.setEndValue(target_op)
                self._anim_opacity.start()
            else:
                self.show()
                self.raise_()
        else:
            self.raise_()
        self._apply_win32_attributes()

    def set_user_hidden(self, hidden: bool):
        """Call with True when user explicitly hides (panic/close); False when a scan should reveal."""
        self._user_hidden = hidden

    def hide_overlay(self):
        self._auto_hide_timer.stop()
        self.pulse_dot.stop_pulse(MUTED)
        if self.config.get("enable_animations", True) and self.isVisible():
            self._anim_opacity.stop()
            self._anim_opacity.setStartValue(self.windowOpacity())
            self._anim_opacity.setEndValue(0.0)
            # SingleShotConnection ensures we don't stack callbacks on rapid hide calls
            self._anim_opacity.finished.connect(self._do_hide, Qt.ConnectionType.SingleShotConnection)
            self._anim_opacity.start()
        else:
            self.hide()

    def _do_hide(self):
        self.hide()

    def toggle_overlay(self):
        if self.isVisible():
            self.hide_overlay()
        else:
            self.show_overlay()

    def enterEvent(self, event: QEnterEvent):
        self._is_hovered = True
        if self.config.get("hover_dimming", True) and self.config.get("enable_animations", True):
            active_op = float(self.config.get("overlay_opacity", 0.90))
            self._anim_opacity.stop()
            self._anim_opacity.setStartValue(self.windowOpacity())
            self._anim_opacity.setEndValue(active_op)
            self._anim_opacity.start()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        self._is_hovered = False
        if self.config.get("hover_dimming", True) and self.config.get("enable_animations", True):
            idle_op = float(self.config.get("idle_opacity", 0.45))
            self._anim_opacity.stop()
            self._anim_opacity.setStartValue(self.windowOpacity())
            self._anim_opacity.setEndValue(idle_op)
            self._anim_opacity.start()
        super().leaveEvent(event)

    def _increase_font(self):
        curr = int(self.config.get("font_size", 11))
        if curr < 24:
            self.config.set("font_size", curr + 1)
            self.apply_config()
            self.font_size_changed.emit(curr + 1)

    def _decrease_font(self):
        curr = int(self.config.get("font_size", 11))
        if curr > 7:
            self.config.set("font_size", curr - 1)
            self.apply_config()
            self.font_size_changed.emit(curr - 1)

    def _copy_to_clipboard(self):
        if self._raw_content:
            QGuiApplication.clipboard().setText(self._raw_content)
            self.btn_copy.setText("✓")
            self.btn_copy.setStyleSheet(
                "QPushButton{background:rgba(16,229,153,0.15);color:#10e599;"
                "border:1px solid rgba(16,229,153,0.4);border-radius:4px;"
                "font-family:'JetBrains Mono',monospace;font-size:8.5pt;padding:2px 7px;}"
            )
            QTimer.singleShot(1400, self._reset_copy_btn)

    def _reset_copy_btn(self):
        self.btn_copy.setText("⎘")
        self.btn_copy.setStyleSheet("")

    # ── Mouse Interaction (Drag & S1mple Mode Resizing) ────────────
    def _get_resize_edge(self, pos: QPoint) -> Optional[str]:
        """Detects if cursor is near window borders for resizing."""
        m = self.RESIZE_MARGIN
        w = self.width()
        h = self.height()
        in_right  = pos.x() >= w - m
        in_bottom = pos.y() >= h - m

        if in_right and in_bottom:
            return "bottom_right"
        elif in_right:
            return "right"
        elif in_bottom:
            return "bottom"
        return None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and not self.config.get("click_through", False):
            edge = self._get_resize_edge(event.pos())
            if edge:
                self._is_resizing = True
                self._resize_mode = edge
                self._resize_start_geo = self.geometry()
                self._resize_start_pos = event.globalPosition().toPoint()
            else:
                self._is_dragging = True
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.config.get("click_through", False):
            # Update cursor shape based on position
            if not self._is_dragging and not self._is_resizing:
                edge = self._get_resize_edge(event.pos())
                if edge == "bottom_right":
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                elif edge == "right":
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                elif edge == "bottom":
                    self.setCursor(Qt.CursorShape.SizeVerCursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)

            if self._is_resizing and self._resize_start_geo and self._resize_start_pos:
                delta = event.globalPosition().toPoint() - self._resize_start_pos
                new_w = max(160, self._resize_start_geo.width() + delta.x())
                new_h = max(70, self._resize_start_geo.height() + delta.y())

                if self._resize_mode == "bottom_right":
                    self.resize(new_w, new_h)
                elif self._resize_mode == "right":
                    self.resize(new_w, self.height())
                elif self._resize_mode == "bottom":
                    self.resize(self.width(), new_h)
                event.accept()
                return

            if self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
                new_pos = event.globalPosition().toPoint() - self._drag_position
                self.move(new_pos)
                if self.is_simple_mode():
                    self.config.set("simple_mode_x", new_pos.x())
                    self.config.set("simple_mode_y", new_pos.y())
                else:
                    self.config.set("overlay_position", "custom")
                    self.config.set("custom_pos_x", new_pos.x())
                    self.config.set("custom_pos_y", new_pos.y())
                event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_resizing:
            self._is_resizing = False
            self._resize_mode = None
            if self.is_simple_mode():
                self.config.set("simple_mode_width", self.width())
                self.config.set("simple_mode_height", self.height())
            else:
                self.config.set("max_width", self.width())
                self.config.set("max_height", self.height())
            self.config.save()
            event.accept()

        if self._is_dragging:
            self._is_dragging = False
            self.config.save()
            event.accept()
