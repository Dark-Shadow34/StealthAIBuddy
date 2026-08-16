from typing import Optional

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QAction, QPolygon
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QWidget

from .config import ConfigManager


class SystemTrayManager(QObject):
    scan_requested = Signal()
    toggle_overlay_requested = Signal()
    settings_requested = Signal()
    clear_requested = Signal()
    exit_requested = Signal()

    def __init__(self, config_mgr: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config_mgr
        self.tray_icon = QSystemTrayIcon(parent)
        self._init_tray()
        self.update_tray_mode()

    def _create_discreet_icon(self) -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        accent_hex = self.config.get("accent_color", "#38bdf8")
        accent = QColor(accent_hex)

        painter.setBrush(QBrush(QColor(15, 23, 42)))
        painter.setPen(QPen(accent, 2))
        painter.drawEllipse(2, 2, 28, 28)

        painter.setBrush(QBrush(accent))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(11, 11, 10, 10)
        painter.end()
        return QIcon(pixmap)

    def _create_audio_disguise_icon(self) -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw harmless speaker icon
        painter.setBrush(QBrush(QColor(148, 163, 184)))
        painter.setPen(Qt.PenStyle.NoPen)

        # Speaker body
        painter.drawRect(6, 11, 6, 10)
        poly = QPolygon([QPoint(12, 11), QPoint(19, 5), QPoint(19, 27), QPoint(12, 21)])
        painter.drawPolygon(poly)

        # Sound waves
        painter.setPen(QPen(QColor(148, 163, 184), 2))
        painter.drawArc(18, 9, 8, 14, -60 * 16, 120 * 16)
        painter.end()
        return QIcon(pixmap)

    def _create_display_disguise_icon(self) -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QPen(QColor(148, 163, 184), 2))
        painter.setBrush(QBrush(QColor(15, 23, 42)))
        painter.drawRoundedRect(4, 6, 24, 16, 2, 2)
        painter.drawLine(16, 22, 16, 26)
        painter.drawLine(10, 26, 22, 26)
        painter.end()
        return QIcon(pixmap)

    def _init_tray(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0f172a;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px;
                font-family: 'Segoe UI', sans-serif;
            }
            QMenu::item {
                padding: 7px 24px;
                border-radius: 5px;
                font-size: 11px;
                font-weight: 500;
            }
            QMenu::item:selected {
                background-color: #0284c7;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #334155;
                margin: 4px 0;
            }
        """)

        action_scan = menu.addAction("⚡ Scan Screen Now (F9 / Ctrl+Alt+S)")
        action_scan.triggered.connect(lambda: self.scan_requested.emit())

        action_toggle = menu.addAction("👁️ Toggle HUD Overlay")
        action_toggle.triggered.connect(lambda: self.toggle_overlay_requested.emit())

        action_clear = menu.addAction("🧹 Clear / Hide HUD (Esc)")
        action_clear.triggered.connect(lambda: self.clear_requested.emit())

        menu.addSeparator()

        action_settings = menu.addAction("⚙️ Control Center & Settings (Ctrl+Alt+O)")
        action_settings.triggered.connect(lambda: self.settings_requested.emit())

        menu.addSeparator()

        action_exit = menu.addAction("🚪 Exit StealthAI")
        action_exit.triggered.connect(lambda: self.exit_requested.emit())

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

    def update_tray_mode(self):
        mode = self.config.get("tray_mode", "discreet")

        if mode == "ghost":
            # 100% Invisible Ghost Mode
            self.tray_icon.hide()
        elif mode == "disguised_audio":
            self.tray_icon.setIcon(self._create_audio_disguise_icon())
            self.tray_icon.setToolTip("Windows Audio Endpoint Service")
            self.tray_icon.show()
        elif mode == "disguised_display":
            self.tray_icon.setIcon(self._create_display_disguise_icon())
            self.tray_icon.setToolTip("Desktop Display Adapter Host")
            self.tray_icon.show()
        else:  # discreet
            self.tray_icon.setIcon(self._create_discreet_icon())
            self.tray_icon.setToolTip("StealthAI Buddy")
            self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()

    def show_message(self, title: str, msg: str):
        if self.config.get("tray_mode") != "ghost" and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 2000)
