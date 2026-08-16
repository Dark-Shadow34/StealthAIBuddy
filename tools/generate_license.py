"""
StealthAI Buddy — Official License & Voucher Generator
Use this private tool to issue cryptographically signed, HWID-locked keys or Universal Voucher keys.
"""

import sys
import os
import argparse
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stealth_buddy.licensing import (
    generate_license_key,
    generate_voucher_key,
    verify_license_key,
    get_machine_hwid,
    UNIVERSAL_DEV_KEY
)

def main():
    parser = argparse.ArgumentParser(description="StealthAI Buddy — License Key Generator")
    parser.add_argument("--hwid", type=str, help="Target machine HWID (e.g. 2B35-4D95-40FF-ACE0)")
    parser.add_argument("--tier", type=str, default="LIFETIME", choices=["LIFETIME", "MONTHLY", "7DAY", "TRIAL"], help="License tier")
    parser.add_argument("--days", type=int, default=0, help="Expiration in days (0 = lifetime)")
    parser.add_argument("--voucher", action="store_true", help="Generate universal machine-independent vouchers")
    parser.add_argument("--count", type=int, default=5, help="Number of voucher keys to generate")
    parser.add_argument("--my-hwid", action="store_true", help="Print this current machine's HWID")

    args = parser.parse_args()

    if args.my_hwid:
        my_hwid = get_machine_hwid()
        print("\n========================================================")
        print(f"  Current Machine HWID: {my_hwid}")
        print("========================================================\n")
        return

    if args.voucher:
        days = args.days if args.days > 0 else 7
        count = args.count
        print("\n" + "=" * 65)
        print(f"  [SUCCESS] Generated {count} Universal {days}-Day Voucher Keys")
        print("  (Can be redeemed on ANY machine — countdown starts on activation)")
        print("=" * 65)
        for i in range(1, count + 1):
            vkey = generate_voucher_key(days=days, serial=int(time.time() % 10000) + i)
            print(f"  {i:02d}. {vkey}")
        print("=" * 65 + "\n")
        return

    if not args.hwid:
        print("\n========================================================")
        print("  ⚡ STEALTHAI BUDDY — LICENSE KEY GENERATOR (OWNER ONLY)")
        print("========================================================\n")
        print("1. Generate HWID-Locked Key")
        print("2. Generate Universal Voucher Keys (e.g. for selling online)")
        choice = input("Select [1/2] (default: 1): ").strip()
        
        if choice == "2":
            days_input = input("Enter Validity Days (e.g. 7, 30, 365): ").strip()
            days = int(days_input) if days_input.isdigit() else 7
            count_input = input("How many voucher keys to generate (default: 5): ").strip()
            count = int(count_input) if count_input.isdigit() else 5
            print("\n" + "=" * 65)
            print(f"  Generated {count} Universal {days}-Day Vouchers:")
            print("=" * 65)
            for i in range(1, count + 1):
                vkey = generate_voucher_key(days=days, serial=int(time.time() % 10000) + i)
                print(f"  {i:02d}. {vkey}")
            print("=" * 65 + "\n")
            return

        hwid_input = input("Enter Customer Machine HWID (e.g. 2B35-4D95-40FF-ACE0): ").strip()
        if not hwid_input:
            hwid_input = get_machine_hwid()
            print(f"Using local machine HWID: {hwid_input}")
            
        tier_input = input("Enter Tier [LIFETIME / MONTHLY / 7DAY] (default: LIFETIME): ").strip().upper() or "LIFETIME"
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

    print("\n" + "=" * 65)
    print("  [SUCCESS] Cryptographically Signed License Generated")
    print("=" * 65)
    print(f"  • Target HWID:   {hwid}")
    print(f"  • License Tier:  {tier}")
    print(f"  • Expiration:    {'Permanent (Lifetime)' if days == 0 else f'{days} Days'}")
    print(f"  • Generated Key: {key}")
    print(f"  • Verification:  {msg}")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
