import sys
import config
import threading
from scheduler import PhotoScheduler
from serial_reader import serial_watcher
from photo_manager import process_photo, cleanup_old_photos
from system_checks import check_system_requirements 
from system_checks import check_system_requirements
from google_services import initialize_sheet


running = True

def main_continuous():
    global running

    if not check_system_requirements():
        print("[Error] System requirements not met. Exiting.")
        return

    initialize_sheet()

    serial_threads = []
    for port in config.SERIAL_PORTS:
        t = threading.Thread(target=serial_watcher, args=(port,), daemon=True)
        t.start()
        serial_threads.append(t)

    def photo_job():
        if process_photo():
            cleanup_old_photos()

    scheduler = PhotoScheduler(interval_minutes=30, callback=photo_job)
    scheduler.start()

    try:
        scheduler.join()
    except KeyboardInterrupt:
        print("\n[Info] Shutdown requested")
        running = False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        process_photo()
    else:
        main_continuous()
