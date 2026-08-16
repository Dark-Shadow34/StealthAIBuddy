import sys
import os
import hmac
import hashlib
import time
import winreg
from typing import Tuple, Optional

# ── Cryptographic Master Salts (Keep confidential) ───────────────
MASTER_SECRET_KEY = b"STEALTH_AI_BUDDY_DRM_SUPER_SECRET_SALT_V1_2026"
UNIVERSAL_DEV_KEY = "STEALTH-MASTER-DEV-9999-LIFETIME-ACCESS"


def get_machine_hwid() -> str:
    """
    Extracts a unique, permanent hardware fingerprint for this Windows machine.
    Uses Windows MachineGuid hashed with secret salt.
    """
    guid = "UNKNOWN-GUID"
    if sys.platform == "win32":
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY
            )
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
        except Exception:
            pass

    h = hashlib.sha256(f"{guid}:{MASTER_SECRET_KEY.decode()}".encode()).hexdigest().upper()
    return f"{h[0:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"


def generate_license_key(hwid: str, tier: str = "LIFETIME", expiry_days: int = 0) -> str:
    """
    Generates a cryptographically signed license key locked to a specific HWID.
    Format: STEALTH-{TIER}-{EXPIRY}-{SIGNATURE}
    """
    clean_hwid = hwid.strip().upper()
    clean_tier = tier.strip().upper()
    expiry_ts = int(time.time() + expiry_days * 86400) if expiry_days > 0 else 0
    
    payload = f"{clean_hwid}:{clean_tier}:{expiry_ts}"
    sig = hmac.new(MASTER_SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest().upper()[:12]
    
    return f"STEALTH-{clean_tier}-{expiry_ts}-{sig[:4]}-{sig[4:8]}-{sig[8:12]}"


def generate_voucher_key(days: int = 7, serial: int = 1) -> str:
    """
    Generates a machine-independent Voucher Key (e.g. for selling online).
    Format: STEALTH-VOUCHER-{DAYS}D-{SERIAL}-{SIG}
    Activates any machine for N days starting from the moment of activation.
    """
    payload = f"VOUCHER:{days}:{serial}"
    sig = hmac.new(MASTER_SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest().upper()[:8]
    return f"STEALTH-VOUCHER-{days}D-{serial:04d}-{sig[:4]}-{sig[4:8]}"


def verify_license_key(license_key: str, current_hwid: Optional[str] = None, activation_time: Optional[int] = None) -> Tuple[bool, str, str]:
    """
    Verifies if a license key is cryptographically valid.
    Returns: (is_valid: bool, tier: str, message: str)
    """
    key = license_key.strip().upper()
    if not key:
        return False, "", "License key is empty."

    # 1. Universal Master Key
    if key == UNIVERSAL_DEV_KEY:
        return True, "DEV-MASTER", "[OK] Developer Master License Active"

    # 2. Universal Voucher Key (e.g. STEALTH-VOUCHER-7D-0001-XXXX-XXXX)
    if key.startswith("STEALTH-VOUCHER-"):
        parts = key.split("-")
        if len(parts) == 6:
            try:
                days_str = parts[2].replace("D", "")
                days = int(days_str)
                serial = int(parts[3])
                sig_received = f"{parts[4]}{parts[5]}"
                
                payload = f"VOUCHER:{days}:{serial}"
                expected_sig = hmac.new(MASTER_SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest().upper()[:8]
                
                if hmac.compare_digest(sig_received, expected_sig):
                    # Check activation timestamp if provided
                    if activation_time:
                        expires_at = activation_time + (days * 86400)
                        remaining_seconds = expires_at - int(time.time())
                        if remaining_seconds <= 0:
                            return False, f"{days}D-VOUCHER", "Voucher license has expired. Please renew."
                        days_left = max(1, int(remaining_seconds / 86400))
                        return True, f"{days}D-VOUCHER", f"[OK] {days}-Day Voucher Valid — {days_left} days remaining"
                    return True, f"{days}D-VOUCHER", f"[OK] Valid {days}-Day Voucher Key"
            except Exception:
                pass
        return False, "", "Invalid voucher license key signature."

    # 3. HWID-Locked Key (e.g. STEALTH-LIFETIME-0-XXXX-XXXX-XXXX)
    hwid = (current_hwid or get_machine_hwid()).strip().upper()
    parts = key.split("-")
    if len(parts) != 6 or parts[0] != "STEALTH":
        return False, "", "Invalid license key format."

    tier = parts[1]
    try:
        expiry_ts = int(parts[2])
    except ValueError:
        return False, "", "Invalid license expiration format."

    sig_received = f"{parts[3]}{parts[4]}{parts[5]}"

    # Verify HMAC signature
    payload = f"{hwid}:{tier}:{expiry_ts}"
    expected_sig = hmac.new(MASTER_SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest().upper()[:12]

    if not hmac.compare_digest(sig_received, expected_sig):
        return False, "", "License key is invalid for this machine HWID."

    # Check expiration date if timed
    if expiry_ts > 0 and time.time() > expiry_ts:
        return False, tier, "License key has expired. Please renew."

    days_left = int((expiry_ts - time.time()) / 86400) if expiry_ts > 0 else -1
    if days_left >= 0:
        return True, tier, f"[OK] License Valid ({tier}) — {days_left} days remaining"
    return True, tier, f"[OK] Lifetime License Valid ({tier})"


class LicenseManager:
    """Manages local machine activation state using Windows Registry & DPAPI."""
    def __init__(self, config_mgr=None):
        self.config = config_mgr
        self._hwid = get_machine_hwid()
        self._license_key = ""
        self._tier = ""
        self._activation_time = 0
        self._is_active = False
        self.load_activation()

    def get_hwid(self) -> str:
        return self._hwid

    def is_activated(self) -> bool:
        return self._is_active

    def get_tier(self) -> str:
        return self._tier

    def load_activation(self):
        saved_key = ""
        act_time = 0

        # 1. Check local config
        if self.config:
            saved_key = self.config.get("license_key", "")
            act_time = int(self.config.get("license_activated_at", 0))

        # 2. Check Windows Registry
        if not saved_key and sys.platform == "win32":
            try:
                reg = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\StealthAIBuddy", 0, winreg.KEY_READ)
                saved_key, _ = winreg.QueryValueEx(reg, "LicenseKey")
                try:
                    act_time, _ = winreg.QueryValueEx(reg, "ActivatedAt")
                    act_time = int(act_time)
                except Exception:
                    act_time = int(time.time())
                winreg.CloseKey(reg)
            except Exception:
                pass

        if saved_key:
            valid, tier, _ = verify_license_key(saved_key, self._hwid, activation_time=act_time)
            if valid:
                self._license_key = saved_key
                self._tier = tier
                self._activation_time = act_time
                self._is_active = True
                return

        self._is_active = False

    def activate(self, license_key: str) -> Tuple[bool, str]:
        now = int(time.time())
        valid, tier, msg = verify_license_key(license_key, self._hwid, activation_time=now)
        if valid:
            self._license_key = license_key.strip().upper()
            self._tier = tier
            self._activation_time = now
            self._is_active = True

            # Save in config
            if self.config:
                self.config.set("license_key", self._license_key)
                self.config.set("license_tier", self._tier)
                self.config.set("license_activated_at", self._activation_time)
                self.config.save()

            # Save in Windows Registry
            if sys.platform == "win32":
                try:
                    reg = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\StealthAIBuddy")
                    winreg.SetValueEx(reg, "LicenseKey", 0, winreg.REG_SZ, self._license_key)
                    winreg.SetValueEx(reg, "ActivatedAt", 0, winreg.REG_DWORD, self._activation_time)
                    winreg.CloseKey(reg)
                except Exception:
                    pass

            return True, msg
        return False, msg


# ── Activation UI Dialog ─────────────────────────────────────────
ACTIVATION_QSS = """
QDialog { background: transparent; }
QFrame#ActFrame {
    background-color: #090c14;
    border: 1px solid rgba(99, 102, 241, 0.45);
    border-radius: 16px;
    color: #b8c6de;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
QLabel#ActTitle { font-size: 14pt; font-weight: 800; color: #ffffff; }
QLabel#ActSub { font-size: 8.5pt; color: #7a8aaa; }
QLabel#HWIDBox {
    background: #0e1220;
    border: 1px solid #1b2235;
    border-radius: 8px;
    padding: 8px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9.5pt;
    font-weight: 700;
    color: #10e599;
}
QLineEdit#KeyInput {
    background: rgba(0, 0, 0, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 10px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9.5pt;
    color: #ffffff;
}
QLineEdit#KeyInput:focus {
    border-color: #6366f1;
    background: rgba(99, 102, 241, 0.08);
}
QPushButton#BtnActivate {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 9px;
    padding: 11px 20px;
    font-size: 9.5pt;
    font-weight: 700;
    color: #ffffff;
}
QPushButton#BtnActivate:hover {
    background: linear-gradient(135deg, #818cf8 0%, #6366f1 100%);
}
QPushButton#BtnCopy {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid #1b2235;
    border-radius: 8px;
    padding: 6px 12px;
    color: #b8c6de;
    font-size: 8.5pt;
    font-weight: 600;
}
QPushButton#BtnCopy:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
}
"""

from PySide6.QtCore import Signal, QPoint
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QApplication, QGraphicsDropShadowEffect
)

class ActivationDialog(QDialog):
    activated_signal = Signal()

    def __init__(self, license_mgr: LicenseManager, parent=None):
        super().__init__(parent)
        self.license_mgr = license_mgr
        self.resize(520, 360)
        self.setStyleSheet(ACTIVATION_QSS)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._dragging = False
        self._drag_pos = QPoint()

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)

        self.frame = QFrame(self)
        self.frame.setObjectName("ActFrame")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setColor(QColor(0, 0, 0, 220))
        shadow.setOffset(0, 10)
        self.frame.setGraphicsEffect(shadow)

        fl = QVBoxLayout(self.frame)
        fl.setContentsMargins(24, 22, 24, 22)
        fl.setSpacing(14)

        # Header
        top_row = QHBoxLayout()
        icon = QLabel("🛡️")
        icon.setStyleSheet("font-size: 20pt;")
        top_row.addWidget(icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        t = QLabel("StealthAI Activation")
        t.setObjectName("ActTitle")
        sub = QLabel("Device License Key Required")
        sub.setObjectName("ActSub")
        title_box.addWidget(t)
        title_box.addWidget(sub)
        top_row.addLayout(title_box, 1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setStyleSheet("background:transparent;color:#ff5f57;font-size:12px;border:none;")
        btn_close.clicked.connect(self.reject)
        top_row.addWidget(btn_close)
        fl.addLayout(top_row)

        # Machine HWID Display
        hwid_sec = QVBoxLayout()
        hwid_sec.setSpacing(4)
        hwid_lbl = QLabel("YOUR UNIQUE MACHINE HWID:")
        hwid_lbl.setStyleSheet("font-size: 7.5pt; font-weight:700; color: #62728f; letter-spacing: 1.5px;")
        hwid_sec.addWidget(hwid_lbl)

        hwid_row = QHBoxLayout()
        self.hwid_display = QLabel(self.license_mgr.get_hwid())
        self.hwid_display.setObjectName("HWIDBox")
        hwid_row.addWidget(self.hwid_display, 1)

        self.btn_copy_hwid = QPushButton("📋 Copy HWID")
        self.btn_copy_hwid.setObjectName("BtnCopy")
        self.btn_copy_hwid.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_hwid.clicked.connect(self._copy_hwid)
        hwid_row.addWidget(self.btn_copy_hwid)
        hwid_sec.addLayout(hwid_row)
        fl.addLayout(hwid_sec)

        # License Key Input
        key_sec = QVBoxLayout()
        key_sec.setSpacing(4)
        key_lbl = QLabel("ENTER LICENSE OR VOUCHER KEY:")
        key_lbl.setStyleSheet("font-size: 7.5pt; font-weight:700; color: #62728f; letter-spacing: 1.5px;")
        key_sec.addWidget(key_lbl)

        self.input_key = QLineEdit()
        self.input_key.setObjectName("KeyInput")
        self.input_key.setPlaceholderText("STEALTH-VOUCHER-7D-... or STEALTH-LIFETIME-...")
        key_sec.addWidget(self.input_key)
        fl.addLayout(key_sec)

        # Status feedback label
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 8.5pt; font-weight: 600;")
        self.lbl_status.hide()
        fl.addWidget(self.lbl_status)

        # Actions
        btn_row = QHBoxLayout()
        self.btn_activate = QPushButton("⚡ Activate License")
        self.btn_activate.setObjectName("BtnActivate")
        self.btn_activate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_activate.clicked.connect(self._on_activate_clicked)
        btn_row.addWidget(self.btn_activate)
        fl.addLayout(btn_row)

        main_layout.addWidget(self.frame)

    def _copy_hwid(self):
        QApplication.clipboard().setText(self.license_mgr.get_hwid())
        self.btn_copy_hwid.setText("✓ Copied!")
        self.btn_copy_hwid.setStyleSheet("background: rgba(16,229,153,0.15); color: #10e599; border-color: #10e599;")

    def _on_activate_clicked(self):
        key = self.input_key.text().strip()
        if not key:
            self.lbl_status.setText("⚠ Please enter a license key.")
            self.lbl_status.setStyleSheet("color: #ff4d4d; font-size: 8.5pt; font-weight: 600;")
            self.lbl_status.show()
            return

        success, msg = self.license_mgr.activate(key)
        if success:
            self.lbl_status.setText(f"✓ {msg}")
            self.lbl_status.setStyleSheet("color: #10e599; font-size: 8.5pt; font-weight: 700;")
            self.lbl_status.show()
            self.btn_activate.setEnabled(False)
            self.activated_signal.emit()
            self.accept()
        else:
            self.lbl_status.setText(f"✗ {msg}")
            self.lbl_status.setStyleSheet("color: #ff4d4d; font-size: 8.5pt; font-weight: 600;")
            self.lbl_status.show()

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._dragging and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._dragging = False
