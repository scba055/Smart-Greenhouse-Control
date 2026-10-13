import os
import time
import subprocess
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config
import threading

sheets_service = None # creating a global variable that is shared between different threads
sheets_lock = threading.Lock()

def authenticate_sheets():
    """Authenticate with Google Sheets API using service account"""
    try:
        if not os.path.exists(config.CREDENTIALS_FILE):
            raise FileNotFoundError(f"Credentials file not found: {config.CREDENTIALS_FILE}")
        
        credentials = service_account.Credentials.from_service_account_file(
            config.CREDENTIALS_FILE, 
            scopes=config.SCOPES
        )
        return credentials
    except Exception as e:
        print(f"[Auth] Error authenticating with Google Sheets: {e}")
        raise

def get_sheets_service():
    global sheets_service
    # created a global sheets_service variable to prevent EOF errors
    if sheets_service is None:
        """Get Google Sheets service object"""
        creds = authenticate_sheets()
        sheets_service = build('sheets', 'v4', credentials=creds)
        
    return sheets_service

def check_rclone_config():
    """Check if rclone is configured and the remote exists"""
    try:
        # Check if rclone is installed
        result = subprocess.run(['rclone', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("[rclone] Error: rclone is not installed or not in PATH")
            return False
        
        print(f"[rclone] rclone version check passed")
        
        # Check if the remote exists
        cmd = ['rclone', 'listremotes']
        if config.RCLONE_CONFIG_FILE:
            cmd.extend(['--config', config.RCLONE_CONFIG_FILE])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"[rclone] Error checking remotes: {result.stderr}")
            return False
        
        remotes = result.stdout.strip().split('\n')
        remote_names = [remote.replace(':', '') for remote in remotes if remote.strip()]
        
        if config.RCLONE_REMOTE not in remote_names:
            print(f"[rclone] Error: Remote '{config.RCLONE_REMOTE}' not found in configured remotes")
            print(f"[rclone] Available remotes: {', '.join(remote_names)}")
            print(f"[rclone] Please configure the remote with: rclone config")
            return False
        
        print(f"[rclone] Remote '{config.RCLONE_REMOTE}' found and configured")
        return True
        
    except subprocess.TimeoutExpired:
        print("[rclone] Error: rclone command timed out")
        return False
    except FileNotFoundError:
        print("[rclone] Error: rclone not found. Please install rclone.")
        return False
    except Exception as e:
        print(f"[rclone] Error checking configuration: {e}")
        return False

# Function to upload image to Google Drive using rclone
# This function uses rclone to copy the file to Google Drive and handles retries
def upload_to_drive_rclone(filepath, timestamp, retry_count=0):
    """Upload image to Google Drive using rclone with retry logic"""
    try:
        # Verify file exists
        if not os.path.exists(filepath):
            print(f"[rclone] File not found: {filepath}")
            return ""
        
        # Get file size
        file_size = os.path.getsize(filepath)
        print(f"[rclone] File size: {file_size / (1024*1024):.2f} MB")
        
        # Create filename from timestamp (replace spaces and colons for filename compatibility)
        safe_timestamp = timestamp.replace(" ", "_").replace(":", "-")
        filename = f"greenhouse_{safe_timestamp}.jpg"
        
        # Construct rclone destination path
        remote_path = f"{config.RCLONE_REMOTE}:{config.RCLONE_REMOTE_PATH}/{filename}"
        
        # Build rclone command
        cmd = ['rclone', 'copy', filepath, f"{config.RCLONE_REMOTE}:{config.RCLONE_REMOTE_PATH}"]
        
        # Add config file if specified
        if config.RCLONE_CONFIG_FILE:
            cmd.extend(['--config', config.RCLONE_CONFIG_FILE])
        
        # Add rclone flags
        cmd.extend(config.RCLONE_COPY_FLAGS)
        
        print(f"[rclone] Uploading: {filename}")
        print(f"[rclone] Command: {' '.join(cmd)}")
        
        # Execute rclone copy
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print(f"[rclone] Upload successful: {filename}")
            return remote_path
        else:
            print(f"[rclone] Upload failed with return code {result.returncode}")
            print(f"[rclone] Error output: {result.stderr}")
            
            # Retry logic
            if retry_count < config.MAX_RETRIES:
                print(f"[rclone] Retrying upload... (attempt {retry_count + 1}/{config.MAX_RETRIES})")
                time.sleep(config.RETRY_DELAY)
                return upload_to_drive_rclone(filepath, timestamp, retry_count + 1)
            else:
                print(f"[rclone] Max retries reached. Upload failed.")
                return ""
                
    except subprocess.TimeoutExpired:
        print("[rclone] Error: Upload timed out")
        if retry_count < config.MAX_RETRIES:
            print(f"[rclone] Retrying upload... (attempt {retry_count + 1}/{config.MAX_RETRIES})")
            time.sleep(config.RETRY_DELAY)
            return upload_to_drive_rclone(filepath, timestamp, retry_count + 1)
        else:
            print(f"[rclone] Max retries reached. Upload failed.")
            return ""
    except Exception as e:
        print(f"[rclone] Error uploading image: {e}")
        if retry_count < config.MAX_RETRIES:
            print(f"[rclone] Retrying upload... (attempt {retry_count + 1}/{config.MAX_RETRIES})")
            time.sleep(config.RETRY_DELAY)
            return upload_to_drive_rclone(filepath, timestamp, retry_count + 1)
        else:
            print(f"[rclone] Max retries reached. Upload failed.")
            return ""

# Function to log data to Google Sheets
# This function assumes you have a Google Sheet set up with the correct columns
# and that config.COLUMNS is a mapping of column names to letters (e.g., {"timestamp": "A", "CO2": "B", ...})
def log_to_sheets(timestamp, data_array):
    global sheets_service
    """Log data to Google Sheets using config.COLUMNS mapping for columns.
    Assumes data_array is a list of values matching the order of config.COLUMNS (excluding timestamp).
    """
    retries = 3 # allows data transfer attempts so that no data is lost on an EOF error
    for attempt in range(retries):
        try:
            sheets_service = get_sheets_service()

            # Build row: first column is timestamp, rest are from data_array
            row = [str(timestamp)] + [str(item) for item in data_array]

            body = {
                'values': [row]
            }

            # Determine range based on columns mapping
            start_col = config.COLUMNS["timestamp"]
            end_col = list(config.COLUMNS.values())[-1]
            range_str = f"{config.SHEET_NAME}!{start_col}:{end_col}"

            # Append to the sheet
            with sheets_lock: # ensures that only either Uno or Seeed accesses the google sheet at a time
                result = sheets_service.spreadsheets().values().append(
                    spreadsheetId=config.SPREADSHEET_ID,
                    range=range_str,
                    valueInputOption='RAW',
                    body=body
                ).execute()

            print(f"[Google Sheets] Logged entry: {row}")
            return True

        except Exception as e:
            print(f"[Google Sheets] Attempt {attempt+1} failed: {e}")
            
            # recreating the client connection to retry data transfer
            sheets_service = None # force reconnect
            
            time.sleep(2)
    
    print("[Google Sheets] All attempts to transfer data failed.")
    return False
            

# Function to initialize Google Sheet with headers
# If headers are not provided, use config.COLUMNS keys as headers
# This function will create the sheet if it doesn't exist and set up the headers
def initialize_sheet(headers=None):
    """Initialize the Google Sheet with headers matching config.COLUMNS mapping"""
    try:
        sheets_service = get_sheets_service()

        # Use config.COLUMNS keys as headers if none provided
        if headers is None:
            # Sort headers by column mapping order
            sorted_columns = sorted(config.COLUMNS.items(), key=lambda x: ord(x[1][0]))
            headers = [col[0] for col in sorted_columns]

        # Ensure headers is a list
        if not isinstance(headers, list):
            headers = [headers]

        # Determine end column letter from config.COLUMNS
        end_col = list(config.COLUMNS.values())[-1]
        range_str = f"{config.SHEET_NAME}!{config.COLUMNS['timestamp']}1:{end_col}1"

        # Check if sheet exists and has headers
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=config.SPREADSHEET_ID,
            range=range_str
        ).execute()

        values = result.get('values', [])

        # If no headers exist or headers are incomplete, add/update them
        if not values or len(values[0]) < len(headers):
            header_values = [[str(header) for header in headers]]
            body = {'values': header_values}

            sheets_service.spreadsheets().values().update(
                spreadsheetId=config.SPREADSHEET_ID,
                range=range_str,
                valueInputOption='RAW',
                body=body
            ).execute()

            print(f"[Google Sheets] Headers initialized: {headers}")

        return True

    except Exception as e:
        print(f"[Google Sheets] Error initializing sheet: {e}")
        return False

# Function to verify rclone access
def verify_rclone_access():
    """Verify that we can access the rclone remote"""
    try:
        # Check rclone configuration
        if not check_rclone_config():
            return False
        
        # Try to list the remote directory
        cmd = ['rclone', 'lsd', f"{config.RCLONE_REMOTE}:{config.RCLONE_REMOTE_PATH}"]
        if config.RCLONE_CONFIG_FILE:
            cmd.extend(['--config', config.RCLONE_CONFIG_FILE])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"[rclone] Successfully accessed remote path: {config.RCLONE_REMOTE}:{config.RCLONE_REMOTE_PATH}")
            return True
        else:
            # If directory doesn't exist, try to create it
            print(f"[rclone] Remote path may not exist, attempting to create: {config.RCLONE_REMOTE_PATH}")
            
            mkdir_cmd = ['rclone', 'mkdir', f"{config.RCLONE_REMOTE}:{config.RCLONE_REMOTE_PATH}"]
            if config.RCLONE_CONFIG_FILE:
                mkdir_cmd.extend(['--config', config.RCLONE_CONFIG_FILE])
            
            mkdir_result = subprocess.run(mkdir_cmd, capture_output=True, text=True, timeout=30)
            
            if mkdir_result.returncode == 0:
                print(f"[rclone] Successfully created remote directory")
                return True
            else:
                print(f"[rclone] Error creating remote directory: {mkdir_result.stderr}")
                return False
            
    except subprocess.TimeoutExpired:
        print("[rclone] Error: Access verification timed out")
        return False
    except Exception as e:
        print(f"[rclone] Error verifying access: {e}")
        return False

# Function to verify Google Sheets access
def verify_sheets_access():
    """Verify that we can access Google Sheets"""
    try:
        sheets_service = get_sheets_service()
        
        # Try to get sheet info
        result = sheets_service.spreadsheets().get(
            spreadsheetId=config.SPREADSHEET_ID
        ).execute()
        
        sheet_title = result.get('properties', {}).get('title', 'Unknown')
        print(f"[Google Sheets] Successfully accessed sheet: {sheet_title}")
        return True
        
    except Exception as e:
        print(f"[Google Sheets] Error verifying access: {e}")
        return False

# Wrapper function for compatibility with main.py
def upload_to_drive(filepath, timestamp, retry_count=0):
    """Wrapper function that calls rclone upload"""
    return upload_to_drive_rclone(filepath, timestamp, retry_count)

# Wrapper function for compatibility with main.py
def verify_drive_access():
    """Wrapper function that calls rclone access verification"""
    return verify_rclone_access()