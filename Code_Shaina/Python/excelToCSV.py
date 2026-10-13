import pandas as pd

# loads the excel file
ef= pd.read_excel("Greenhouse.xlsx", sheet_name="Inputs")

print(ef.columns)

ef["timestamp"] = pd.to_datetime(ef["timestamp"])

# replaces "N/A" with "NaN"
ef = ef.replace("N/A", pd.NA)

# convert pH columns to numeric
ef["SEEED_PH"] = pd.to_numeric(ef["SEEED_PH"], errors="coerce")
ef["UNO_PH"] = pd.to_numeric(ef["UNO_PH"], errors="coerce")

# grabs dosing data from excel sheet
dose_data = ef[["Last_Dose", "Dose_Amount", "Dose_Direction"]].copy()

dose_data["Last_Dose"] = pd.to_datetime(dose_data["Last_Dose"], errors="coerce")
dose_data["Dose_Amount"] = pd.to_numeric(dose_data["Dose_Amount"], errors="coerce")
dose_data["Dose_Direction"] = dose_data["Dose_Direction"].str.upper()

valid_dose = dose_data.dropna(
    subset=["Last_Dose", "Dose_Amount", "Dose_Direction"]
)

valid_dose = valid_dose.sort_values("Last_Dose")

# merge dosing into full dataset
ef = pd.merge_asof(
    ef.sort_values("timestamp"),
    valid_dose,
    left_on="timestamp",
    right_on="Last_Dose",
    direction="backward"
)

# fix column naming after merge
ef = ef.rename(columns={
    "Last_Dose_y": "Last_Dose",
    "Dose_Amount_y": "Dose_Amount",
    "Dose_Direction_y": "Dose_Direction"
})

ef = ef.drop(columns=[
    "Last_Dose_x", "Dose_Amount_x", "Dose_Direction_x"
], errors="ignore")

# split the two data streams
seeed = ef.dropna(subset=["SEEED_PH"])[["timestamp", "SEEED_PH", "Last_Dose", "Dose_Amount", "Dose_Direction"]]
uno = ef.dropna(subset=["UNO_PH"])[["timestamp", "UNO_PH"]]

# time-match both seeed and uno
merged = pd.merge_asof(
    seeed.sort_values("timestamp"),
    uno.sort_values("timestamp"),
    on = "timestamp",
    direction = "nearest",
    tolerance = pd.Timedelta("7min")
)

# remove bad time matches
merged = merged.dropna(subset=["UNO_PH"])

# compute delta_pH
merged["delta"] = merged["UNO_PH"] - merged["SEEED_PH"]

# detect a change in reservoir pH
merged["pH_Change"] = merged["SEEED_PH"].diff()

# water cycle detection
threshold = -0.25
merged["water_cycle_on"] = (
    (merged["pH_Change"] < threshold) &
    (merged["pH_Change"].shift(1) >= threshold)
).astype(int)

# detect dose events
merged["Dose_event"] = (
    merged["Last_Dose"] != merged["Last_Dose"].shift()
).astype(int)

# creates a column that counts the time since last dose
merged["Time_since_dose"] = (
    merged["timestamp"] - merged["Last_Dose"]
).dt.total_seconds() / 60

# save clean dataset
merged.to_excel("cleanedData.xlsx", index=False)
merged.to_csv("cleanedData.csv", index=False)