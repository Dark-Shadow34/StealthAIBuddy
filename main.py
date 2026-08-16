import sys
import os

# Ensure the project root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from stealth_buddy.config import ConfigManager
from stealth_buddy.licensing import LicenseManager, ActivationDialog
from stealth_buddy.app import StealthBuddyApp


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    config = ConfigManager()
    license_mgr = LicenseManager(config)

    # Hardware-locked DRM License Check
    if not license_mgr.is_activated():
        activation_dialog = ActivationDialog(license_mgr)
        if activation_dialog.exec() != ActivationDialog.DialogCode.Accepted:
            sys.exit(0)

    buddy = StealthBuddyApp(app, config_mgr=config, license_mgr=license_mgr)

    print("=" * 60)
    print(f" ⚡ StealthAI Buddy ({license_mgr.get_tier()}) - Active & Running")
    print(f" • Device HWID: {license_mgr.get_hwid()}")
    print("=" * 60)
    print(" • Press [F9] or [Ctrl + Alt + S] to Scan & Solve screen")
    print(" • Press [Esc] for Instant Panic Hide")
    print(" • Press [Ctrl + Alt + O] to Open Settings & API Keys")
    print(" • Press [Ctrl + Alt + R] to Re-display Last Answer")
    print(" • Tray icon is active in Windows Notification Area")
    print("=" * 60)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
