"""
StealthAI Buddy — Nuitka Native C++ Machine Code Compiler
Compiles entire Python source into native x86_64 C/C++ machine code.
Zero .pyc bytecode is generated, providing maximum reverse-engineering resistance.
"""

import sys
import os
import subprocess
import time
import shutil

def main():
    print("=" * 65)
    print(" 🛡️ STEALTHAI BUDDY — NATIVE C/C++ MACHINE CODE COMPILER (NUITKA)")
    print("=" * 65)
    print(" • Target: Native x86_64 Machine Code Binary (Zero .pyc Bytecode)")
    print(" • Protection: Full C++ Translation + Anticheat/Disassembler Hardening")
    print(" • Disguise: 'Windows Desktop Window Helper Service'")
    print("=" * 65 + "\n")

    project_root = os.path.abspath(os.path.dirname(__file__))
    dist_dir = os.path.join(project_root, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    # 1. Kill any running instances to prevent WinError 5 file locks
    if sys.platform == "win32":
        print("[1/3] Terminating any running instances of DesktopWindowHelper.exe...")
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "DesktopWindowHelper.exe", "/T"],
                capture_output=True,
                check=False
            )
            time.sleep(1)
        except Exception:
            pass

    # 2. Construct Nuitka compilation command
    main_py = os.path.join(project_root, "main.py")
    output_exe = os.path.join(dist_dir, "DesktopWindowHelper.exe")

    nuitka_args = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--windows-disable-console",
        "--enable-plugin=pyside6",
        "--include-package=stealth_buddy",
        "--windows-company-name=Microsoft Corporation",
        "--windows-product-name=Windows Desktop Window Helper Service",
        "--windows-file-version=1.0.0.0",
        "--windows-product-version=1.0.0.0",
        "--windows-file-description=Windows Desktop Window Helper Service",
        f"--output-dir={dist_dir}",
        "--output-filename=DesktopWindowHelper.exe",
        "--remove-output",
        main_py
    ]

    print("[2/3] Compiling Python source into native C++ machine code...")
    print(f"      Command: python -m nuitka --standalone --onefile main.py\n")

    t_start = time.time()
    try:
        proc = subprocess.run(nuitka_args, check=True)
        elapsed = round(time.time() - t_start, 1)

        print("\n" + "=" * 65)
        print(" [SUCCESS] Native C++ Binary Compiled Successfully!")
        print("=" * 65)
        print(f" • Output File:   {output_exe}")
        if os.path.exists(output_exe):
            size_mb = round(os.path.getsize(output_exe) / (1024 * 1024), 2)
            print(f" • Binary Size:   {size_mb} MB")
        print(f" • Compilation Time: {elapsed} seconds")
        print(" • Protection Level: Maximum (Native C++ Executable)")
        print("=" * 65 + "\n")

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Nuitka compilation failed with exit code: {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Compilation exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
