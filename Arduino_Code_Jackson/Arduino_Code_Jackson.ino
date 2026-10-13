#include <Wire.h>
#include "Adafruit_SCD30.h"

#define PH_PIN A0

Adafruit_SCD30 scd30;

const unsigned long REPORT_INTERVAL_MS = 600000;   // 10 min
const int NUM_PH_SAMPLES = 100;

const float ADC_REF = 5.0;
const float ADC_MAX = 1023.0;

const float V_PH7 = 1.9583;
const float V_PH4 = 1.7561;

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
    Serial.println("{\"PH\":\"N/A\",\"CO2_DATA\":{\"CO2\":\"SENSOR_ERROR\",\"AirTemperature\":\"N/A\",\"Humidity\":\"N/A\"}}");
  } else {
    scd30.setMeasurementInterval(5);
  }

  delay(3000); // let serial settle after opening
  lastReport = millis() - REPORT_INTERVAL_MS; // send first reading immediately
}

void loop() {
  unsigned long now = millis();

  if (now - lastReport >= REPORT_INTERVAL_MS) {
    lastReport = now;

    float phValue = readPH();

    if (scd30.dataReady()) {
      if (scd30.read()) {
        Serial.print("{");
        Serial.print("\"PH\":\""); Serial.print(phValue, 2); Serial.print("\",");
        Serial.print("\"CO2_DATA\":{");
        Serial.print("\"CO2\":\""); Serial.print(scd30.CO2, 1); Serial.print("\",");
        Serial.print("\"AirTemperature\":\""); Serial.print(scd30.temperature, 1); Serial.print("\",");
        Serial.print("\"Humidity\":\""); Serial.print(scd30.relative_humidity, 1); Serial.print("\"");
        Serial.print("}");
        Serial.println("}");
      } else {
        Serial.print("{");
        Serial.print("\"PH\":\""); Serial.print(phValue, 2); Serial.print("\",");
        Serial.print("\"CO2_DATA\":{");
        Serial.print("\"CO2\":\"READ_ERROR\",");
        Serial.print("\"AirTemperature\":\"N/A\",");
        Serial.print("\"Humidity\":\"N/A\"");
        Serial.print("}");
        Serial.println("}");
      }
    } else {
      Serial.print("{");
      Serial.print("\"PH\":\""); Serial.print(phValue, 2); Serial.print("\",");
      Serial.print("\"CO2_DATA\":{");
      Serial.print("\"CO2\":\"WAITING\",");
      Serial.print("\"AirTemperature\":\"N/A\",");
      Serial.print("\"Humidity\":\"N/A\"");
      Serial.print("}");
      Serial.println("}");
    }
  }
}