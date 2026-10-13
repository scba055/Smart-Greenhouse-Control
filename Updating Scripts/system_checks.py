import os
import config
from camera import test_rpicam
from google_services import verify_rclone_access, verify_sheets_access, initialize_sheet


def check_system_requirements():
    print("[System Check] Verifying requirements...")
    all_good = True

    if not os.path.exists(config.IMAGE_DIR):
        os.makedirs(config.IMAGE_DIR, exist_ok=True)

    if not os.path.exists(config.CREDENTIALS_FILE):
        print(f"[System Check] Missing credentials file: {config.CREDENTIALS_FILE}")
        all_good = False

    if not test_rpicam():
        print("[System Check] rpicam-still not available")
        all_good = False

    if not verify_rclone_access():
        print("[Warning] rclone - not availiable - continuing")
        

    if not verify_sheets_access() or not initialize_sheet():
        print("[System Check] Cannot access or init Google Sheets")
        all_good = False

    return all_good
