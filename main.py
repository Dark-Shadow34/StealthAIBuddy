import sys
import os

# Ensure the project root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from stealth_buddy.app import StealthBuddyApp


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    buddy = StealthBuddyApp(app)

    print("=" * 60)
    print(" ⚡ StealthAI Buddy - Active & Running")
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
