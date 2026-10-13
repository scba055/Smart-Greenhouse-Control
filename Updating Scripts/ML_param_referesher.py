import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GA_PARAM_FILE = os.path.join(
    BASE_DIR, 
    "..",
    "Code_Shaina",
    "Python",
    "ga_params.json"
    )

class ML_param_refresher:
    def __init__(self):
        # default params - will be overwritten if JSON load is successful
        self.lower_threshold = 5.8
        self.upper_threshold = 6.4
        self.dosing_buffer = 50 * 60 # 3000 seconds = 50 minutes
        
        self.load_params()
        
    def load_params(self):
        try:
            with open(GA_PARAM_FILE, "r") as f:
                params = json.load(f)
                self.lower_threshold = params["lower_trigger"]
                self.upper_threshold = params["upper_trigger"]
                self.dosing_buffer = params["cooldown_time"] * 60  # convert minutes to seconds
                print(f"[ML Param Refresher] Parameters loaded successfully. \nParams: {params}")
        except Exception as e:
            print(f"[ML Param Refresher] Error loading parameters: {e}")
            print("[ML Param Refresher] Using default parameters.")
                
    # return params to serial_reader for dosing decisions
    def get_params(self):
        return {
            "lower_threshold": self.lower_threshold,
            "upper_threshold": self.upper_threshold,
            "dosing_buffer": self.dosing_buffer
        }