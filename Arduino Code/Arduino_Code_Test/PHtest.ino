/*#include <Arduino.h>

const int PH_PIN = A0;
const int RAW1_PIN = A1;
const int RAW2_PIN = A2;

const float V7 = 1.5444;  // Replace with actual measured voltage at pH 7
const float V4 = 1.1554;  // Replace with actual measured voltage at pH 4

// Linear calibration coefficients
const float m_pH = (4.0 - 7.0) / (V4 - V7);
const float b_pH = 7.0 - m_pH * V7;

const unsigned long SAMPLE_INTERVAL_MS = 100;
const unsigned long REPORT_INTERVAL_MS = 10000;

unsigned long lastSampleTime = 0;
unsigned long lastReportTime = 0;

unsigned long sampleCount = 0;
float sumPHVoltage = 0;
float sumRaw1 = 0;
float sumRaw2 = 0;

void setup() {
  Serial.begin(9600);
  while (!Serial); // Wait for USB Serial to be ready
  delay(100000);
  analogReadResolution(12);
}

void loop() {
  unsigned long now = millis();
  
  if (now - lastSampleTime >= SAMPLE_INTERVAL_MS) {
    lastSampleTime = now;
    sampleCount++;

    // Read and accumulate pH sensor voltage
    int rawPH = analogRead(PH_PIN);
    
    float phVoltage = rawPH * (3.3 / 4095.0);
    sumPHVoltage += phVoltage;

    // Read and accumulate raw sensors
    sumRaw1 += analogRead(RAW1_PIN);
    sumRaw2 += analogRead(RAW2_PIN);
  }

  if (now - lastReportTime >= REPORT_INTERVAL_MS) {
    lastReportTime = now;

    // Compute averages
    float avgPHVoltage = sumPHVoltage / sampleCount;
    float pH = m_pH * avgPHVoltage + b_pH;
    float avgRaw1 = sumRaw1 / sampleCount;
    float avgRaw2 = sumRaw2 / sampleCount;

    // Send JSON string
    
    Serial.print("{");
    Serial.print("\"ph_voltage\":"); Serial.print(avgPHVoltage, 3); Serial.print(",");
    Serial.print("\"ph\":"); Serial.print(pH, 2); Serial.print(",");
    Serial.print("\"sensor1\":"); Serial.print(avgRaw1, 2); Serial.print(",");
    Serial.print("\"sensor2\":"); Serial.print(avgRaw2, 2);
    Serial.println("}");

    // Reset accumulators
    sampleCount = 0;
    sumPHVoltage = sumRaw1 = sumRaw2 = 0;
  }
}*/

//Average Voltage @ A0: 1.5444 V (from 10000 samples) PH7
//Average Voltage @ A0: 1.1554 V (from 10000 samples) PH4

#include <Arduino.h>

const int PH_PIN = A0;
const int NUM_SAMPLES = 1000;

void setup() {
  Serial.begin(9600);
  analogReadResolution(12);
  while (!Serial);
  Serial.println("pH Calibration Script Starting...");
  Serial.println("Place probe in pH 7 or pH 4 solution and observe output.");
}

void loop() {
  float voltageSum = 0;

  for (int i = 0; i < NUM_SAMPLES; i++) {
    int raw = analogRead(PH_PIN);
    float voltage = raw * (3.3 / 4095.0); // Adjust if your reference is not 3.3V
    voltageSum += voltage;
    delay(10);
  }

  float avgVoltage = voltageSum / NUM_SAMPLES;

  Serial.print("Average Voltage @ A0: ");
  Serial.print(avgVoltage, 4);
  Serial.print(" V (from ");
  Serial.print(NUM_SAMPLES);
  Serial.println(" samples)");

  delay(2000);
}

