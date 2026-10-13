import csv
import os
from google_services import log_to_sheets

# moving this function here from serial_reader.py
def save_locally(timestamp, data_array):
    with open("backup.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp] + data_array)
        
def resend_backup():
    if not os.path.exists("backup.csv"):
        return

    with open("backup.csv", "r") as f:
        rows = list(csv.reader(f))

    if not rows:
        return

    #  clear file immediately
    open("backup.csv", "w").close()

    print(f"[BACK UP] Resending {len(rows)} rows to Google Sheets...")

    failedRows = []

    for i, row in enumerate(rows):
        timestamp = row[0]
        data_array = row[1:]

        if not log_to_sheets(timestamp, data_array):
            print("[BACK UP] Failed, keeping remaining rows for retry.")

            # keep this row + all remaining rows
            failedRows.extend(rows[i:])
            break

    # write back failed + unprocessed rows
    if failedRows:
        with open("backup.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(failedRows)
    else:
        print("[BACK UP] Upload complete.")