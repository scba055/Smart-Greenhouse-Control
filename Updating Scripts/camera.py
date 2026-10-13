import subprocess
import os
import config
from datetime import datetime

# Ensure image directory exists
os.makedirs(config.IMAGE_DIR, exist_ok=True)

def take_picture():
    """Take a picture with rotation using rpicam-still"""
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename_timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    filename = f"picture_{filename_timestamp}.jpg"
    filepath = os.path.join(config.IMAGE_DIR, filename)
    
    # Take picture with rpicam-still (updated from libcamera-still)
    cmd = [
            "rpicam-still",
            "-o", filepath,
            "--timeout", "5000",
            "--width", str(config.PHOTO_WIDTH),
            "--height", str(config.PHOTO_HEIGHT),
            "--rotation", "180",           # Rotate 180 degrees
    ]
    
    try:
        print("Taking picture with rpicam-still...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"Picture captured: {filepath}")
            return filename, timestamp, filepath
        else:
            print(f"Error taking picture: {result.stderr}")
            print(f"Command output: {result.stdout}")
            return None
            
    except subprocess.TimeoutExpired:
        print("Error: rpicam-still command timed out")
        return None
    except FileNotFoundError:
        print("Error: rpicam-still not found. Please ensure it's installed and in PATH")
        print("Try: sudo apt update && sudo apt install rpicam-apps")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_rpicam():
    """Test rpicam-still availability and basic functionality"""
    try:
        # Test rpicam-still version
        result = subprocess.run(["rpicam-still", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"rpicam-still available: {result.stdout.strip()}")
            return True
        else:
            print(f"rpicam-still test failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("rpicam-still not found. Install with: sudo apt install rpicam-apps")
        return False
    except Exception as e:
        print(f"Error testing rpicam-still: {e}")
        return False