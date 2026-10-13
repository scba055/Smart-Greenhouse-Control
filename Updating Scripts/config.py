import os

# -------- Base directory --------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Google Sheets Configuration
SPREADSHEET_ID = "1-SUFcdM8K_eleKb0_B5FCG4nA1t_actNMDbOsYIxiFM"
SHEET_NAME = "Inputs"

# Give each board its own columns in the sheet
COLUMNS = {
    "timestamp": "A",
    "SEEED_EC": "B",
    "SEEED_PH": "C",
    "SEEED_CO2": "D",
    "SEEED_AirTemperature": "E",
    "SEEED_Humidity": "F",
    "SEEED_Light": "G",
    "UNO_PH": "H",
    "UNO_CO2": "I",
    "UNO_AirTemperature": "J",
    "UNO_Humidity": "K",
    "String": "L",
    "Last_Dose": "M",
    "Dose_Amount": "N",
    "Dose_Direction": "O"
}

# Full row order used for Sheets (after timestamp)
DEVICE_COLUMN_ORDER = [
    "SEEED_EC",
    "SEEED_PH",
    "SEEED_CO2",
    "SEEED_AirTemperature",
    "SEEED_Humidity",
    "SEEED_Light",
    "UNO_PH",
    "UNO_CO2",
    "UNO_AirTemperature",
    "UNO_Humidity",
    "String",
    "Last_Dose",
    "Dose_Amount",
    "Dose_Direction"
]

# Use stable USB serial symlinks instead of ttyACM numbers
# Run: ls /dev/serial/by-id/
# Then paste the exact names below
PORT_DEVICE_MAP = {
    "/dev/serial/by-id/usb-Seeed_Seeed_XIAO_M0_CF91530C503058414E2E3120FF0A1337-if00": "seeed",
    "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_851333231363517060C1-if00": "uno",
}

SERIAL_PORTS = list(PORT_DEVICE_MAP.keys())
SERIAL_BAUDRATE = 9600

# Rclone Configuration
RCLONE_REMOTE = "GoogleDrive"
RCLONE_REMOTE_PATH = "Images"
RCLONE_CONFIG_FILE = None

# Local paths
IMAGE_DIR = "/home/rpi/Pictures"
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials", "service-account-key.json")

# Google API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

# Photo settings
PHOTO_WIDTH = 4608
PHOTO_HEIGHT = 2592
PHOTO_TIMEOUT = 5000

# Upload settings
MAX_RETRIES = 3
RETRY_DELAY = 5

# File cleanup settings
MAX_LOCAL_FILES = 50

# Rclone settings
RCLONE_COPY_FLAGS = [
    "--progress",
    "--stats", "1s",
    "--transfers", "1",
    "--checkers", "1",
    "--drive-acknowledge-abuse"
]

# Discord Configuration
DISCORD_BOT_TOKEN = "YOUR_BOT_TOKEN"
DISCORD_CHANNEL_ID = "YOUR_CHANNEL_ID"
DISCORD_ENABLED = True

# Discord notification settings
DISCORD_NOTIFY_SUCCESS = True
DISCORD_NOTIFY_ERROR = True
DISCORD_EMBED_COLOR = 0x00ff00
DISCORD_ERROR_COLOR = 0xff0000
DISCORD_TIMEOUT = 30

# Discord message templates
DISCORD_SUCCESS_TEMPLATE = "📸 **Greenhouse Photo Captured**\n🕐 **Time:** {timestamp}\n📁 **File:** {filename}\n💾 **Size:** {file_size}\n🔗 **Link:** {drive_link}"
DISCORD_ERROR_TEMPLATE = "❌ **Greenhouse Photo Error**\n🕐 **Time:** {timestamp}\n🔴 **Error:** {error_message}"
