import os
import sys
import subprocess

# Ensure utf-8 output encoding for Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def build():
    print("=" * 60)
    print(" [BUILD] StealthAI Buddy - Standalone Single-File EXE Builder")
    print("=" * 60)

    project_root = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(project_root, "main.py")
    version_file = os.path.join(project_root, "version_info.txt")
    dist_dir = os.path.join(project_root, "dist")

    exe_name = "DesktopWindowHelper"

    excludes = [
        "PySide6.Qt3DCore", "PySide6.Qt3DAnimation", "PySide6.Qt3DExtras", "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic", "PySide6.Qt3DRender", "PySide6.QtBluetooth", "PySide6.QtCharts",
        "PySide6.QtDBus", "PySide6.QtDataVisualization", "PySide6.QtDesigner", "PySide6.QtHelp",
        "PySide6.QtHttpServer", "PySide6.QtLocation", "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
        "PySide6.QtNetworkAuth", "PySide6.QtNfc", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
        "PySide6.QtPositioning", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D",
        "PySide6.QtQuickWidgets", "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtSensors",
        "PySide6.QtSerialBus", "PySide6.QtSerialPort", "PySide6.QtSpatialAudio", "PySide6.QtSql",
        "PySide6.QtStateMachine", "PySide6.QtSvg", "PySide6.QtSvgWidgets", "PySide6.QtTest",
        "PySide6.QtTextToSpeech", "PySide6.QtUiTools", "PySide6.QtVirtualKeyboard", "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineQuick", "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebSockets", "PySide6.QtXml", "scipy", "matplotlib", "tkinter"
    ]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--windowed",
        "--onefile",
        f"--name={exe_name}",
        f"--version-file={version_file}",
        "--clean",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=mss",
        "--hidden-import=PIL",
        "--hidden-import=requests",
        "--hidden-import=openai",
        "--hidden-import=anthropic",
    ]

    for ex in excludes:
        cmd.append(f"--exclude-module={ex}")

    cmd.append(main_py)

    print(f"Compiling optimized standalone {exe_name}.exe (Task Manager Disguised)...")
    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode == 0:
        final_exe = os.path.join(dist_dir, f"{exe_name}.exe")
        print("\n" + "=" * 60)
        print(" [SUCCESS] Standalone Single-File Executable built!")
        print(f" Output Location: {final_exe}")
        print("=" * 60)
        print(" - Pure background execution (zero console popups)")
        print(" - Disguised in Task Manager as 'Windows Desktop Window Helper Service'")
        print(" - Completely standalone (runs on any Windows PC without Python)")
    else:
        print("\n [ERROR] Build failed with exit code:", result.returncode)

if __name__ == "__main__":
    build()
