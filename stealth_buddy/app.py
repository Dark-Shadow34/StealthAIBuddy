import sys
import ctypes
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication

from .config import ConfigManager
from .capture import ScreenCaptureEngine
from .ai_engine import AIEngine
from .overlay import StealthOverlayHUD
from .hotkey_listener import GlobalHotkeyManager
from .settings_gui import SettingsDialog
from .system_tray import SystemTrayManager


class AIWorkerThread(QThread):
    finished_signal = Signal(bool, str)

    def __init__(self, ai_engine: AIEngine, b64_img: str):
        super().__init__()
        self.ai_engine = ai_engine
        self.b64_img = b64_img

    def run(self):
        try:
            success, response = self.ai_engine.analyze_screen(self.b64_img)
            self.finished_signal.emit(success, response)
        except Exception as e:
            self.finished_signal.emit(False, f"Internal Error: {e}")


class StealthBuddyApp(QObject):
    def __init__(self, q_app: QApplication, config_mgr: Optional[ConfigManager] = None, license_mgr=None):
        super().__init__()
        self.q_app = q_app
        self.config = config_mgr or ConfigManager()
        self.license_mgr = license_mgr
        self.capture_engine = ScreenCaptureEngine()
        self.ai_engine = AIEngine(self.config)

        # Core Components
        self.overlay = StealthOverlayHUD(self.config)
        self.tray = SystemTrayManager(self.config)
        self.settings_dialog = SettingsDialog(self.config)
        self.hotkeys = GlobalHotkeyManager(self.config)

        self._active_worker: Optional[AIWorkerThread] = None
        self._last_answer: str = "No previous scan available yet."
        self._is_busy = False

        self._wire_signals()
        self.hotkeys.start()

        # Initial launch greeting
        self._show_initial_status()

    def _show_initial_status(self):
        prov = self.config.get("ai_provider", "gemini")
        key_field = f"{prov}_api_key"
        has_key = bool(self.config.get(key_field, "").strip()) or prov in ("ollama", "custom")

        if has_key:
            init_msg = (
                f"**⚡ StealthAI Active** (`{prov.upper()}`)\n\n"
                "• Press **[F9]** or **[Ctrl+Alt+S]** to scan & solve screen\n"
                "• Press **[Esc]** for instant panic hide\n"
                "• Press **[Ctrl+Alt+O]** to open Control Center\n"
                "• Hover over HUD for quick actions (Copy, Font Scale, Settings)"
            )
            self.overlay.set_content(init_msg, status="Ready")
        else:
            init_msg = (
                "**⚡ Welcome to StealthAI Buddy**\n\n"
                "⚠️ **No API Key Configured Yet**\n"
                "Click **⚙️** or press **[Ctrl+Alt+O]** to set your Gemini, OpenAI, or Claude API Key."
            )
            self.overlay.set_content(init_msg, status="Setup Needed")

        self.overlay.show_overlay()
        self.tray.show_message("StealthAI Active", "Press F9 or Ctrl+Alt+S to scan screen")

    def _wire_signals(self):
        # Hotkeys
        self.hotkeys.scan_requested.connect(self.trigger_scan)
        self.hotkeys.panic_requested.connect(self.trigger_panic)
        self.hotkeys.settings_requested.connect(self.open_settings)
        self.hotkeys.repeat_requested.connect(self.repeat_last_answer)

        # Overlay UI Buttons
        self.overlay.scan_clicked.connect(self.trigger_scan)
        self.overlay.settings_clicked.connect(self.open_settings)
        self.overlay.font_size_changed.connect(lambda sz: self.config.save())

        # Tray
        self.tray.scan_requested.connect(self.trigger_scan)
        self.tray.toggle_overlay_requested.connect(self.overlay.toggle_overlay)
        self.tray.settings_requested.connect(self.open_settings)
        self.tray.clear_requested.connect(self.clear_overlay)
        self.tray.exit_requested.connect(self.shutdown)

        # Settings
        self.settings_dialog.config_updated.connect(self._on_config_updated)
        self.settings_dialog.trigger_test_scan.connect(self.trigger_scan)
        self.settings_dialog.toggle_preview.connect(self.toggle_preview)

    def _on_config_updated(self):
        self.overlay.apply_config()
        self.tray.update_tray_mode()
        self.hotkeys.register_all()

    def trigger_panic(self):
        """Instantly vanishes the overlay. Sets user-hidden flag so auto-show is suppressed."""
        self.overlay.set_user_hidden(True)
        self.overlay.hide_overlay()

    def clear_overlay(self):
        self.overlay.set_content("", status="Ready")
        self.overlay.set_user_hidden(True)
        self.overlay.hide_overlay()

    def repeat_last_answer(self):
        if self._last_answer:
            self.overlay.set_user_hidden(False)
            self.overlay.set_content(self._last_answer, status="Repeat")

    def toggle_preview(self):
        if self.overlay.isVisible():
            self.overlay.hide_overlay()
        else:
            sample_text = (
                "**Option B: Linear Regression with L2 Regularization (Ridge)**\n\n"
                "• Penalty term `λ∑w²` prevents coefficient explosion.\n"
                "• Closed-form solution: `w = (XᵀX + λI)⁻¹Xᵀy`\n"
                "• Time complexity: `O(d³ + d²n)`"
            )
            self.overlay.set_user_hidden(False)
            self.overlay.set_content(sample_text, status="Preview")

    def open_settings(self):
        self.settings_dialog.load_from_config()
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()
        # Force foreground on Windows
        if sys.platform == "win32":
            try:
                hwnd = int(self.settings_dialog.winId())
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
            except Exception:
                pass

    def trigger_scan(self):
        if self._is_busy:
            self.overlay.show_status("Already scanning…", "#f59e0b", pulse=True)
            return

        prov = self.config.get("ai_provider", "gemini")
        key_field = f"{prov}_api_key"
        if not self.config.get(key_field, "").strip() and prov not in ("ollama", "custom"):
            self.overlay.set_user_hidden(False)
            self.overlay.set_content(
                f"⚠️ **{prov.capitalize()} API key is missing!**\n\n"
                "Click **⚙️ Settings** (or press Ctrl+Alt+O) to paste your API key.",
                status="Missing Key"
            )
            self.open_settings()
            return

        self._is_busy = True
        self._t_scan_start = time.monotonic()

        # Unhide so user sees the status
        self.overlay.set_user_hidden(False)
        self.overlay.show_status("Scanning screen...", "#38bdf8", pulse=True)

        # Step 1: Capture screen
        try:
            mon_idx = int(self.config.get("monitor_index", 0))
            cap_q = self.config.get("capture_quality", "balanced")
            if cap_q == "ultra":
                max_dim, quality = 2560, 95
            elif cap_q == "fast":
                max_dim, quality = 1280, 70
            else:
                max_dim, quality = 1920, 85

            _, b64_img, (w, h) = self.capture_engine.capture_optimized_bytes(
                monitor_index=mon_idx,
                max_dim=max_dim,
                quality=quality
            )
        except Exception as e:
            self.overlay.set_content(f"Screen capture failed: {e}", status="Error")
            self._is_busy = False
            return

        self._t_ocr_done = time.monotonic()
        self.overlay.show_status("Reasoning...", "#f59e0b", pulse=True)

        # Step 2: Background AI query
        self._active_worker = AIWorkerThread(self.ai_engine, b64_img)
        self._active_worker.finished_signal.connect(self._on_ai_finished)
        self._active_worker.start()

    def _on_ai_finished(self, success: bool, response_text: str):
        self._is_busy = False
        ocr_ms = int((self._t_ocr_done - self._t_scan_start) * 1000)
        ai_ms  = int((time.monotonic() - self._t_ocr_done) * 1000)

        if success:
            self._last_answer = response_text
            self.overlay.set_content(response_text, status="Answer")
            self.overlay.update_latency(ocr_ms, ai_ms)

            # Auto-copy if configured
            if self.config.get("auto_copy_clipboard", False):
                try:
                    QGuiApplication.clipboard().setText(response_text)
                except Exception:
                    pass

            # Audio alert if configured
            if self.config.get("sound_alert", False):
                try:
                    QApplication.beep()
                except Exception:
                    pass
        else:
            self.overlay.set_content(f"⚠️ {response_text}", status="Error")
            self.overlay.update_latency(ocr_ms, ai_ms)

    def shutdown(self):
        self.hotkeys.stop()
        self.overlay.close()
        self.settings_dialog.close()
        self.q_app.quit()
