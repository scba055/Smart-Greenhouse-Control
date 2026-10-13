import os
from datetime import datetime
import config
from camera import take_picture
from google_services import upload_to_drive
#from discord_notifier import send_photo_success_notification, send_photo_error_notification
def send_photo_success_notification(*args, **kwargs):
    return True
    
def send_photo_error_notification(*args, **kwargs):
    return True

def format_file_size(size_bytes: float) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def process_photo():
    try:
        result = take_picture()
        if not result:
            error_msg = "Failed to take picture with rpicam-still"
            send_photo_error_notification(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg)
            return False

        filename, timestamp, filepath = result
        file_size_bytes = os.path.getsize(filepath)
        file_size_formatted = format_file_size(file_size_bytes)

        drive_link = upload_to_drive(filepath, timestamp)
        if not drive_link:
            error_msg = "Failed to upload to Google Drive"
            send_photo_error_notification(timestamp, error_msg)
            return False

        send_photo_success_notification(timestamp, filename, file_size_formatted)
        return True

    except Exception as e:
        error_msg = f"Exception in process_photo: {str(e)}"
        send_photo_error_notification(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_msg)
        return False


def cleanup_old_photos():
    try:
        import glob
        pattern = os.path.join(config.IMAGE_DIR, "picture_*.jpg")
        photos = glob.glob(pattern)
        if len(photos) > config.MAX_LOCAL_FILES:
            photos.sort(key=os.path.getmtime)
            for photo in photos[:-config.MAX_LOCAL_FILES]:
                os.remove(photo)
                print(f"[Cleanup] Removed {os.path.basename(photo)}")
    except Exception as e:
        print(f"[Cleanup] Error: {e}")
