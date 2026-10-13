import pandas as pd
from ML_Controller import MLController

# load cleaned dataset
df = pd.read_csv("Greenhouse_Processed.csv")

# create controller
ml = MLController()

ml.train(df)

# predict pH with example input
predicted_ph = ml.predict_ph(
    ec=1.5,
    pH = 4.5,
    Previous_pH = 4.7,
    pH_change = -0.2,
    co2=400,
    air_temp=25,
    humidity=60,
    minutes_since_last_dose=30,
    dose_direction_encoded=1
)

print("Predicted pH:", predicted_ph)