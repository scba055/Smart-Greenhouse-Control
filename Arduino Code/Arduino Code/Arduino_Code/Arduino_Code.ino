#include <Wire.h>
#include "Adafruit_SCD30.h"

#define PH_PIN A0

Adafruit_SCD30 scd30;

const unsigned long REPORT_INTERVAL_MS = 600000;   // 10 min
const int NUM_PH_SAMPLES = 100;

const float ADC_REF = 5.0;      // Uno/Nano default analog reference
const float ADC_MAX = 1023.0;

// Replace these with your measured calibration voltages
const float V_PH7 = 2.50;
const float V_PH4 = 3.00;

const float M_PH = (4.0f - 7.0f) / (V_PH4 - V_PH7);
const float B_PH = 7.0f - M_PH * V_PH7;

unsigned long lastReport = 0;

float readPHVoltage() {
  float sum = 0.0;
  for (int i = 0; i < NUM_PH_SAMPLES; i++) {
    int raw = analogRead(PH_PIN);
    sum += raw * (ADC_REF / ADC_MAX);
    delay(10);
  }
  return sum / NUM_PH_SAMPLES;
}

float readPH() {
  float voltage = readPHVoltage();
  return M_PH * voltage + B_PH;
}

void setup() {
  Serial.begin(9600);
  Wire.begin();

  if (!scd30.begin()) {
    Serial.println("{\"PH2\":\"N/A\",\"CO2_2\":\"SENSOR_ERROR\",\"AirTemp_2\":\"N/A\",\"Humidity_2\":\"N/A\"}");
  } else {
    scd30.setMeasurementInterval(5);
  }
}

void loop() {
  unsigned long now = millis();

  if (now - lastReport >= REPORT_INTERVAL_MS) {
    lastReport = now;

    float phValue = readPH();

    if (scd30.dataReady()) {
      if (scd30.read()) {
        Serial.print("{");
        Serial.print("\"PH2\":\""); Serial.print(phValue, 2); Serial.print("\",");
        Serial.print("\"CO2_2\":\""); Serial.print(scd30.CO2, 1); Serial.print("\",");
        Serial.print("\"AirTemp_2\":\""); Serial.print(scd30.temperature, 1); Serial.print("\",");
        Serial.print("\"Humidity_2\":\""); Serial.print(scd30.relative_humidity, 1); Serial.print("\"");
        Serial.println("}");
      } else {
        Serial.print("{");
        Serial.print("\"PH2\":\""); Serial.print(phValue, 2); Serial.print("\",");
        Serial.print("\"CO2_2\":\"READ_ERROR\",\"AirTemp_2\":\"N/A\",\"Humidity_2\":\"N/A\"");
        Serial.println("}");
      }
    } else {
      Serial.print("{");
      Serial.print("\"PH2\":\""); Serial.print(phValue, 2); Serial.print("\",");
      Serial.print("\"CO2_2\":\"WAITING\",\"AirTemp_2\":\"N/A\",\"Humidity_2\":\"N/A\"");
      Serial.println("}");
    }
  }
}