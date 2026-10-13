import time
import serial
import config
from datetime import datetime
from JSon import parse_sensor_string, prepare_for_sheets
from google_services import log_to_sheets
from Pump_Controller import PumpController  # 17/04/26 - moved this file to updating scripts since this could have caused the halting issue
from backup_manager import save_locally, resend_backup
from ML_param_referesher import ML_param_refresher

running = True

def serial_watcher(port):
    device_type = config.PORT_DEVICE_MAP.get(port, "unknown")
    column_order = config.DEVICE_COLUMN_ORDER
    ser = None

    # ----- Pump Control Things ------- #
    lastDoseTime = 0
    lastDoseTimestamp = "N/A"
    lastDoseDirection = "N/A"
    lastDoseAmount = 0
    doseAmount = 0.4
    
    pump = None
    lastPH = None
    watchdogTimeout = 15 * 60
    
    # ml params replaces the hardcoded params
    ml_params = ML_param_refresher()
    ml_params.get_params() # load initial params from JSON
    lower_threshold = ml_params.lower_threshold
    upper_threshold = ml_params.upper_threshold
    dosingBuffer = ml_params.dosing_buffer
    
    # Open port once, retry only if open fails or connection is genuinely lost
    while running and ser is None:
        try:
            ser = serial.Serial(port, config.SERIAL_BAUDRATE, timeout=10)
            last_data_time = time.time()
            # Give Arduino/Seeeduino time to settle after serial open
            time.sleep(2)
            ser.reset_input_buffer()

            print(f"[Serial] Listening on {port} at {config.SERIAL_BAUDRATE} baud as {device_type}")

            if device_type == "seeed":
                pump = PumpController(ser)

        except Exception as e:
            print(f"[Serial {port}] Could not open port: {e}")
            print(f"[Serial {port}] Retrying in 3 seconds...")
            time.sleep(3)

    while running and ser is not None:
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if line:
                print(f"[Serial {port}] Received: {line}")
                last_data_time = time.time()

                try:
                    sensor_data = parse_sensor_string(line)
                    
                    # checks for any data being passed into sensor_data, if nothing then skip
                    if not sensor_data:
                        continue

                    if device_type == "seeed" and isinstance(sensor_data, dict):
                        ph = sensor_data.get("PH")

                        try:
                             #print(f"[DEBUGGING] Raw pH reading: {ph}")
                            ph = float(ph)
                            lastPH = ph
                        except:
                            print(f"[WARNING] Skipping invalid PH: {ph}")
                            continue # skips bad pH reading instead of being logged

                    # convert last dose time to readable timestamp
                    if lastDoseTime > 0:
                        lastDoseTimestamp = datetime.fromtimestamp(lastDoseTime).strftime("%H:%M:%S")
                    else:
                        lastDoseTimestamp = "N/A"
                        
                    # inject it into sensor_data
                    sensor_data["Last_Dose"] = lastDoseTimestamp
                    sensor_data["Dose_Amount"] = lastDoseAmount
                    sensor_data["Dose_Direction"] = lastDoseDirection
                    
                    data_array = prepare_for_sheets(sensor_data, device_type, column_order)
                    print(f"[Serial {port}] Parsed row: {data_array}")
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    successfulLog = log_to_sheets(timestamp, data_array)
                    if not successfulLog:
                        print("[Fallback] Cannot log data to Google Sheets. Saving locally.")
                        save_locally(timestamp, data_array)
                        
                    else:
                        resend_backup()
                    
                    # resets values
                    lastDoseAmount = 0
                    lastDoseDirection = "N/A"

                except Exception as e:
                    print(f"[Serial {port}] Error processing line: {e}")
            
            # moving pump-related controls down here to separate data collection and pumps   
            now = time.time()
            
            if device_type == "seeed" and pump is not None and lastPH is not None:
                elapsed = now - lastDoseTime
                
                #print(f"[STATE] pH = {lastPH:.2f}, elapsed = {int(elapsed)}")
                
                if elapsed >= dosingBuffer:
                    if lastPH < lower_threshold:
                        print("[ACTION] Dose Up")
                        pump.dose_up(doseAmount) # smaller dose because we are running out of pH Up
                        lastDoseTime = now
                        lastDoseAmount = doseAmount
                        lastDoseDirection = "UP"
                    elif lastPH > upper_threshold:
                        print("[ACTION] Dose down")
                        pump.dose_down(doseAmount)
                        lastDoseTime = now
                        lastDoseAmount = doseAmount
                        lastDoseDirection = "DOWN"
                    else:
                        print("[INFO] pH is within acceptable range")
            
            if time.time() - last_data_time > watchdogTimeout: # 15mins 
                print(f"[WATCHDOG {port}] No data for 15mins -> forcing reconnection")
                
                try:
                    if ser and ser.is_open:
                        ser.close()
                        print(f"[WATCHDOG {port}] Port Closed")
                except:
                    pass
                
                ser = None
                break
            # prevents tight looping
            time.sleep(5)

        except Exception as e:
            print(f"[Serial {port}] Error reading: {e}")

            try:
                if ser and ser.is_open:
                    ser.close()
                    print(f"[Serial {port}] Port closed.")
            except Exception:
                pass

            ser = None
            print(f"[Serial {port}] Retrying in 3 seconds...")
            time.sleep(3)

            while running and ser is None:
                try:
                    ser = serial.Serial(port, config.SERIAL_BAUDRATE, timeout=10)
                    last_data_time = time.time()
                    # Give Arduino/Seeeduino time to settle after reconnect
                    time.sleep(2)
                    ser.reset_input_buffer()

                    print(f"[Serial] Listening on {port} at {config.SERIAL_BAUDRATE} baud as {device_type}")

                    if device_type == "seeed":
                        pump = PumpController(ser)

                except Exception as e:
                    print(f"[Serial {port}] Could not open port: {e}")
                    print(f"[Serial {port}] Retrying in 3 seconds...")
                    time.sleep(3)

    if ser and ser.is_open:
        ser.close()
        print(f"[Serial {port}] Port closed.")