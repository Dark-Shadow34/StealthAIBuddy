"""
StealthAI Buddy — Official License Key Generator
Use this private tool to issue cryptographically signed, HWID-locked license keys.
"""

import sys
import os
import argparse
import time

# Add parent directory to path to import licensing engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stealth_buddy.licensing import (
    generate_license_key,
    verify_license_key,
    get_machine_hwid,
    UNIVERSAL_DEV_KEY
)

def main():
    parser = argparse.ArgumentParser(description="StealthAI Buddy — License Key Generator")
    parser.add_argument("--hwid", type=str, help="Target machine HWID (e.g. 2B35-4D95-40FF-ACE0)")
    parser.add_argument("--tier", type=str, default="LIFETIME", choices=["LIFETIME", "MONTHLY", "PRO", "TRIAL"], help="License tier")
    parser.add_argument("--days", type=int, default=0, help="Expiration in days (0 = lifetime)")
    parser.add_argument("--my-hwid", action="store_true", help="Print this current machine's HWID")

    args = parser.parse_args()

    if args.my_hwid:
        my_hwid = get_machine_hwid()
        print("\n========================================================")
        print(f"  Current Machine HWID: {my_hwid}")
        print("========================================================\n")
        return

    if not args.hwid:
        print("\n========================================================")
        print("  ⚡ STEALTHAI BUDDY — LICENSE KEY GENERATOR (OWNER ONLY)")
        print("========================================================\n")
        hwid_input = input("Enter Customer Machine HWID (e.g. 2B35-4D95-40FF-ACE0): ").strip()
        if not hwid_input:
            hwid_input = get_machine_hwid()
            print(f"Using local machine HWID: {hwid_input}")
            
        tier_input = input("Enter Tier [LIFETIME / MONTHLY / PRO] (default: LIFETIME): ").strip().upper() or "LIFETIME"
        days_input = input("Enter Validity Days (0 for Lifetime): ").strip()
        days = int(days_input) if days_input.isdigit() else 0
        hwid = hwid_input
        tier = tier_input
    else:
        hwid = args.hwid
        tier = args.tier
        days = args.days

    key = generate_license_key(hwid, tier, days)
    valid, verified_tier, msg = verify_license_key(key, hwid)

    print("\n" + "=" * 60)
    print("  [SUCCESS] Cryptographically Signed License Generated")
    print("=" * 60)
    print(f"  • Target HWID:   {hwid}")
    print(f"  • License Tier:  {tier}")
    print(f"  • Expiration:    {'Permanent (Lifetime)' if days == 0 else f'{days} Days'}")
    print(f"  • Generated Key: {key}")
    print(f"  • Verification:  {msg}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
