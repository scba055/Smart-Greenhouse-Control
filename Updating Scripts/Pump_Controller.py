import time

class PumpController:
    def __init__(self, ser):
        self.ser = ser

    def send_command(self, command: str):
        try:
            print("[DEBUG] About to send command")
            msg = command + "\n"
            self.ser.write(msg.encode("utf-8"))
            self.ser.flush()
            print("[DEBUG] Command sent successfully")
        except Exception as e: 
            print(f"[Pump Controller ERROR]: {e}")

    def dose_up(self, duration_sec: float):
        self.send_command(f"DOSE_UP:{duration_sec}")

    def dose_down(self, duration_sec: float):
        self.send_command(f"DOSE_DOWN:{duration_sec}")