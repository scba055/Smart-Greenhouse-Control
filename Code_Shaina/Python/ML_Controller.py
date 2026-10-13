import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error

class MLController:
    def __init__(self):
        self.ph_model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        self.feature_columns =[
            "SEEED_EC",
            "SEEED_PH",
            "Previous_pH",
            "pH_Change",
            "SEEED_CO2",
            "SEEED_AirTemperature",
            "SEEED_Humidity",
            "Minutes_Since_Last_Dose",
            "Dose_Direction_Encoded"
        ]
        
        self.target_column = "Future_pH"
        
    def train(self, data):
        # remove rows with missing values
        df = data.dropna(subset=self.feature_columns + [self.target_column])
        
        # split the data into features and target
        X = df[self.feature_columns]
        y = df[self.target_column]
        
        # split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42
        )
        
        # train the model
        self.ph_model.fit(X_train, y_train)
        
        # evaluate the model
        predictions = self.ph_model.predict(X_test)
        
        # performance metrics
        score = r2_score(y_test, predictions)
        mae = mean_absolute_error(y_test, predictions)
        rmse = root_mean_squared_error(y_test, predictions)
        
        # print performance metrics
        print(f"R^2 Score: {score:.4f}")
        print(f"Mean Absolute Error: {mae:.4f}")
        print(f"Root Mean Squared Error: {rmse:.4f}")
        
    def predict_ph(
        self,
        ec,
        pH,
        Previous_pH,
        pH_change,
        co2,
        air_temp,
        humidity,
        minutes_since_last_dose,
        dose_direction_encoded
    ):
        input_data = pd.DataFrame({
            "SEEED_EC": [ec],
            "SEEED_PH": [pH],
            "Previous_pH": [Previous_pH],
            "pH_Change": [pH_change],
            "SEEED_CO2": [co2],
            "SEEED_AirTemperature": [air_temp],
            "SEEED_Humidity": [humidity],
            "Minutes_Since_Last_Dose": [minutes_since_last_dose],
            "Dose_Direction_Encoded": [dose_direction_encoded]
        })
    
        predicted_ph = self.ph_model.predict(input_data)
        return predicted_ph[0]