import signal


def setup_signal_handler(stop_event, running_flag):
    """Attach a Ctrl+C handler for graceful shutdown"""
    def handler(sig, frame):
        print("\n[Info] Shutdown signal received")
        stop_event.set()
        running_flag[0] = False
    signal.signal(signal.SIGINT, handler)