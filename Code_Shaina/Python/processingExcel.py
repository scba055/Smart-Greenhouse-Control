import pandas as pd
import numpy as np

# load excel file
df = pd.read_excel(
    "Greenhouse.xlsx",
    sheet_name="Inputs"
)

# clean out any "N/A", "WAITING", or empty string values
df.replace(
    ["N/A", "WAITING", ""],
    np.nan,
    inplace=True
)

# clean column names
df.columns = df.columns.str.strip()

# timestamp parsing and sorting
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

df = df.sort_values("timestamp")

# sensor columns to forward-fill
sensor_columns = [
    "SEEED_EC",
    "SEEED_PH",
    "SEEED_CO2",
    "SEEED_AirTemperature",
    "SEEED_Humidity",
    "SEEED_Light",
    "UNO_PH",
    "UNO_CO2",
    "UNO_AirTemperature",
    "UNO_Humidity"
]

# only forward-fill sensor/environmental data
existing_sensor_columns = [
    col for col in sensor_columns
    if col in df.columns
]

# Remove rows missing all sensor data
df = df.dropna(
    subset=existing_sensor_columns,
    how="all"
)

df[existing_sensor_columns] = (
    df[existing_sensor_columns]
    .ffill()
)

# convert sensor columns to numeric, coercing errors to NaN
for col in existing_sensor_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# dosing feature
# fill missing dose amounts with 0
if "Dose_Amount" in df.columns:

    df["Dose_Amount"] = pd.to_numeric(
        df["Dose_Amount"],
        errors="coerce"
    ).fillna(0)

# encode dose direction
if "Dose_Direction" in df.columns:

    df["Dose_Direction_Encoded"] = (
        df["Dose_Direction"]
        .astype(str)
        .str.upper()
        .map({
            "UP": 1,
            "DOWN": -1,
            "NONE": 0
        })
        .fillna(0)
    )


# time since last dose feature
if "Dose_Amount" in df.columns:

    df["Dose_Event"] = df["Dose_Amount"] > 0

    df["Last_Dose_Time"] = np.where(
        df["Dose_Event"],
        df["timestamp"],
        pd.NaT
    )

    df["Last_Dose_Time"] = (
        pd.to_datetime(df["Last_Dose_Time"])
        .ffill()
    )

    df["Minutes_Since_Last_Dose"] = (
        (
            df["timestamp"] -
            df["Last_Dose_Time"]
        )
        .dt.total_seconds() / 60
    )

# create future pH target column
df["Future_pH"] = df["SEEED_PH"].shift(-1)

# create previous pH and pH change features
df["Previous_pH"] = df["SEEED_PH"].shift(1)

df["pH_Change"] = (
    df["SEEED_PH"] -
    df["Previous_pH"]
)

# export cleaned data to new CSV
df.to_csv(
    "Greenhouse_Processed.csv",
    index=False
)

print("Processing complete.")
print(df.head())