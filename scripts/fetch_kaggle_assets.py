#!/usr/bin/env python3
"""Fetch official Kaggle competition assets for med-gemma-impact-challenge.

This is OPTIONAL. The EdgeMed Agent runs fully without it.
Use this to obtain official write-up templates, submission instructions,
logos, or starter notebooks if the competition provides them.

Usage:
    python scripts/fetch_kaggle_assets.py

Requirements:
    - kaggle CLI installed:  pip install kaggle
    - API token configured:  ~/.kaggle/kaggle.json  (chmod 600 on Linux/Mac)
      Or set KAGGLE_CONFIG_DIR to a directory containing kaggle.json.

The script will NOT fail your build if Kaggle is unavailable.
It will print clear instructions for every failure mode.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

COMPETITION = "med-gemma-impact-challenge"
REPO_ROOT = Path(__file__).resolve().parent.parent
DEST_DIR = REPO_ROOT / "assets" / "kaggle"


def run(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        timeout=120,
    )


def check_cli() -> bool:
    """Verify kaggle CLI is installed."""
    if shutil.which("kaggle") is None:
        print("ERROR: kaggle CLI not found on PATH.")
        print()
        print("  Install it with:  pip install kaggle")
        print("  Then re-run this script.")
        return False

    result = run(["kaggle", "--version"])
    if result.returncode != 0:
        print("ERROR: 'kaggle --version' failed.")
        print(f"  stderr: {result.stderr.strip()}")
        return False

    print(f"  Kaggle CLI: {result.stdout.strip()}")
    return True


def check_credentials() -> bool:
    """Verify Kaggle API credentials are configured."""
    config_dir = os.environ.get("KAGGLE_CONFIG_DIR")
    if config_dir:
        kaggle_json = Path(config_dir) / "kaggle.json"
    else:
        kaggle_json = Path.home() / ".kaggle" / "kaggle.json"

    # Also accept KAGGLE_USERNAME + KAGGLE_KEY env vars
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        print("  Credentials: via KAGGLE_USERNAME + KAGGLE_KEY env vars")
        return True

    if not kaggle_json.exists():
        print("ERROR: Kaggle API credentials not found.")
        print()
        print("  Option 1: Place kaggle.json at:")
        print(f"    {kaggle_json}")
        print()
        print("  Option 2: Set environment variables:")
        print("    KAGGLE_USERNAME=your_username")
        print("    KAGGLE_KEY=your_api_key")
        print()
        print("  Option 3: Set KAGGLE_CONFIG_DIR to a folder containing kaggle.json")
        print()
        print("  Get your API token from: https://www.kaggle.com/settings -> API -> Create New Token")
        print()
        print("  IMPORTANT: Never commit kaggle.json to git.")
        return False

    # Warn about permissions on Unix
    if platform.system() != "Windows":
        mode = oct(kaggle_json.stat().st_mode)[-3:]
        if mode != "600":
            print(f"  WARNING: {kaggle_json} has permissions {mode}, Kaggle expects 600.")
            print(f"    Fix with: chmod 600 {kaggle_json}")

    print(f"  Credentials: {kaggle_json}")
    return True


def list_competition_files() -> list[dict] | None:
    """List files available in the competition. Returns None on error."""
    result = run(["kaggle", "competitions", "files", "-c", COMPETITION, "--csv"])

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "404" in stderr or "not found" in stderr.lower():
            print(f"  Competition '{COMPETITION}' not found or not accessible.")
            print("  Make sure you have accepted the competition rules on Kaggle.")
            return None
        if "403" in stderr or "forbidden" in stderr.lower():
            print("  Access denied. Accept the competition rules at:")
            print(f"  https://www.kaggle.com/competitions/{COMPETITION}/rules")
            return None
        print(f"  Failed to list competition files: {stderr}")
        return None

    stdout = result.stdout.strip()
    if not stdout or stdout.lower().startswith("no files"):
        return []

    lines = stdout.strip().split("\n")
    if len(lines) <= 1:
        # Only header row or empty
        return []

    files = []
    header = lines[0].split(",")
    for line in lines[1:]:
        parts = line.split(",")
        entry = {}
        for i, col in enumerate(header):
            entry[col.strip()] = parts[i].strip() if i < len(parts) else ""
        files.append(entry)

    return files


def download_files() -> bool:
    """Download competition files to assets/kaggle/."""
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    result = run(
        [
            "kaggle", "competitions", "download",
            "-c", COMPETITION,
            "-p", str(DEST_DIR),
            "--force",
        ],
    )

    if result.returncode != 0:
        print(f"  Download failed: {result.stderr.strip()}")
        return False

    print(f"  Download output: {result.stdout.strip()}")

    # Attempt to unzip any .zip files
    for zf in DEST_DIR.glob("*.zip"):
        print(f"  Unzipping: {zf.name}")
        try:
            import zipfile
            with zipfile.ZipFile(zf, "r") as z:
                z.extractall(DEST_DIR)
            zf.unlink()
        except Exception as e:
            print(f"  WARNING: Could not unzip {zf.name}: {e}")

    return True


def print_directory_listing():
    """Print what ended up in the assets/kaggle/ directory."""
    files = [f for f in DEST_DIR.rglob("*") if f.is_file() and f.name != ".gitkeep"]
    if not files:
        print("  Directory is empty (no files were downloaded).")
        return

    print(f"  Downloaded {len(files)} file(s) to assets/kaggle/:")
    for f in sorted(files):
        rel = f.relative_to(DEST_DIR)
        size = f.stat().st_size
        if size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        print(f"    {rel}  ({size_str})")


def main():
    print("=" * 60)
    print("EdgeMed Agent — Fetch Kaggle Competition Assets")
    print(f"Competition: {COMPETITION}")
    print("=" * 60)
    print()

    # Step 1: Check CLI
    print("[1/4] Checking kaggle CLI...")
    if not check_cli():
        print()
        print("Exiting. Install the kaggle CLI and try again.")
        sys.exit(1)
    print()

    # Step 2: Check credentials
    print("[2/4] Checking Kaggle API credentials...")
    if not check_credentials():
        print()
        print("Exiting. Configure credentials and try again.")
        sys.exit(1)
    print()

    # Step 3: List competition files
    print("[3/4] Listing competition files...")
    files = list_competition_files()

    if files is None:
        print()
        print("Could not access competition files. See errors above.")
        print("This is non-blocking — EdgeMed Agent runs without Kaggle assets.")
        sys.exit(0)

    if len(files) == 0:
        print()
        print("  No competition files available to download.")
        print()
        print("  This is expected — the med-gemma-impact-challenge competition")
        print("  states 'Competition Data: None'. No datasets are provided.")
        print("  Check the competition page for updates:")
        print(f"  https://www.kaggle.com/competitions/{COMPETITION}/data")
        print()
        print("EdgeMed Agent does not require any Kaggle downloads to function.")
        sys.exit(0)

    print(f"  Found {len(files)} file(s):")
    for f in files:
        name = f.get("name", f.get("fileName", "unknown"))
        size = f.get("size", f.get("totalBytes", "?"))
        print(f"    - {name}  ({size})")
    print()

    # Step 4: Download
    print("[4/4] Downloading to assets/kaggle/...")
    if download_files():
        print()
        print_directory_listing()
        print()
        print("Done. Review downloaded assets before using them.")
        print("REMINDER: Verify no PHI or restricted data is present.")
    else:
        print()
        print("Download failed. See errors above.")
        print("This is non-blocking — EdgeMed Agent runs without Kaggle assets.")

    sys.exit(0)


if __name__ == "__main__":
    main()
