import time
import threading
from datetime import datetime, timedelta

class PhotoScheduler(threading.Thread):
    def __init__(self, interval_minutes, callback, stop_event=None):
        super().__init__(daemon=True)
        self.interval = interval_minutes
        self.callback = callback
        self.stop_event = stop_event or threading.Event()

    def get_next_mark(self):
        now = datetime.now().replace(second=0, microsecond=0)
        minutes_to_add = self.interval - (now.minute % self.interval)
        if minutes_to_add == 0:
            return now
        return now + timedelta(minutes=minutes_to_add)

    def run(self):
        while not self.stop_event.is_set():
            next_mark = self.get_next_mark()
            wait_seconds = (next_mark - datetime.now()).total_seconds()
            end_time = time.time() + wait_seconds

            while time.time() < end_time:
                if self.stop_event.is_set():
                    return
                time.sleep(1)

            try:
                self.callback()
            except Exception as e:
                print(f"[Error] Photo callback failed: {e}")