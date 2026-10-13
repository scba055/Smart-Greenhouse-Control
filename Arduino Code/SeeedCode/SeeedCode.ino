#include <Arduino.h>
#include <string.h>
#include <Wire.h>
#include <BH1750.h>
#include "Adafruit_SCD30.h"

// Pin assignments
#define ANALOG_PH_PIN A0
#define TdsSensorPin A1

#define PH_UP_PUMP D2
#define PH_DOWN_PUMP D3

const int VREF = 3.3;
const int SCOUNT = 30;
const int ADCresconst = 4096;

BH1750 lightMeter;
Adafruit_SCD30 scd30;
bool scd30Initialised = false;
bool bh1750Available = false;

int analogBuffer[SCOUNT];
int analogBufferIndex = 0;

float temperature = 25;
float ECValue = 0;

// Output buffers
char ecBuf[24];
char co2Buf[80];
char LightBuf[20];
char phBuffer[128];
char jsonBuf[512];

// Function declarations
const char* ReadPH();
const char* ReadEC();
const char* ReadCO2();
const char* ReadLight();
const char* run();
const char* MeasureCO2();
const char* MeasureLight();
void samplePH();
void handlePumpCommand(String cmd);
void runPump(int pin, int duration);
void updatePump();

// Timing variables
unsigned long lastMeasurementTime = 0;
const unsigned long measurementInterval = 600000; // 5 sec for debugging
unsigned long lastCO2Read = 0;
const unsigned long CO2Interval = 5000; // 5 seconds to ensure that it has enough time to read

// pH sensor calibration constants
const float V_PH7 = 1.9583;
const float V_PH4 = 1.7561;

const float M_PH = (4.0f - 7.0f) / (V_PH4 - V_PH7);
const float B_PH = 7.0f - M_PH * V_PH7;

// pH sampling variables
const unsigned long SAMPLE_INTERVAL_MS = 1000;
const int SAMPLES_PER_MEASUREMENT = measurementInterval / SAMPLE_INTERVAL_MS;

// Variables for pH averaging
unsigned long lastSampleTime = 0;
int currentSampleCount = 0;
float sumPHVoltage = 0.0f;
float currentPH = 7.0f;  // safer startup value for debugging

// Variables for pH Pumps
bool pumpRunning = false;
int activePump = -1;
unsigned long pumpStartTime = 0;
unsigned long pumpDuration = 0;

enum Type {
  PH = 'P',
  EC = 'E',
  CO2 = 'C',
  Light = 'L',
  Main = 'M'
};

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(50);
  Wire.begin();
  analogReadResolution(12);

  unsigned long serialStart = millis();
  while (!Serial && millis() - serialStart < 3000) {
    delay(10);
  }

  for (int i = 0; i < SCOUNT; i++) {
    analogBuffer[i] = 0;
  }

  pinMode(PH_UP_PUMP, OUTPUT);
  pinMode(PH_DOWN_PUMP, OUTPUT);

  digitalWrite(PH_UP_PUMP, LOW);
  digitalWrite(PH_DOWN_PUMP, LOW);

  Serial.println("{\"STATUS\":\"SEEED_STARTED\"}");
}

void loop() {

  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');

    Serial.print("RECEIVED: ");
    Serial.println(cmd); // for debugging
     
    
    if (cmd.length() > 0) {
      handlePumpCommand(cmd);
    }
  }

  samplePH();
  updatePump();

  unsigned long now = millis();
  if (now - lastMeasurementTime >= measurementInterval) {
    lastMeasurementTime = now;
    const char* result = run();
    Serial.println(result);
  }
}

//***********Main Run Function***********
const char* run() {
  const char* ph = ReadPH();
  const char* ec = ReadEC();
  const char* co2 = ReadCO2();
  const char* light = ReadLight();

  snprintf(jsonBuf, sizeof(jsonBuf),
           "{\"EC\":\"%s\",\"PH\":\"%s\",\"CO2_DATA\":%s,\"Light\":\"%s\"}",
           ec, ph, co2, light);
  return jsonBuf;
}

//***********Light Sensor***********
const char* ReadLight() {
  if (!bh1750Available) {
    if (lightMeter.begin()) {
      bh1750Available = true;
    } else {
      snprintf(LightBuf, sizeof(LightBuf), "SENSOR_ERROR");
      return LightBuf;
    }
  }

  return MeasureLight();
}

const char* MeasureLight() {
  float lux = lightMeter.readLightLevel();

  if (lux < 0 || lux > 100000) {
    snprintf(LightBuf, sizeof(LightBuf), "READ_ERROR");
  } else {
    snprintf(LightBuf, sizeof(LightBuf), "%.1f", lux);
  }
  return LightBuf;
}

//***********EC/TDS Sensor***********
const char* ReadEC() {
  int samples[SCOUNT];

  for (int i = 0; i < SCOUNT; i++) {
    samples[i] = analogRead(TdsSensorPin);
  }

  unsigned long sum = 0;
  for (int i = 0; i < SCOUNT; i++) sum += samples[i];
  float averageVoltage = (sum / (float)SCOUNT) * VREF / ADCresconst;

  float compensationCoefficient = 1.0 + 0.02 * (temperature - 25.0);
  float compensationVoltage = averageVoltage / compensationCoefficient;

  ECValue = (133.42 * compensationVoltage * compensationVoltage * compensationVoltage
            - 255.86 * compensationVoltage * compensationVoltage
            + 857.39 * compensationVoltage);

  snprintf(ecBuf, sizeof(ecBuf), "%.2f", ECValue);
  return ecBuf;
}

//***********pH Sensor***********
const char* ReadPH() {
  if (currentSampleCount > 0) {
    float avgPHVoltage = sumPHVoltage / currentSampleCount;
    float livePH = M_PH * avgPHVoltage + B_PH;
    snprintf(phBuffer, sizeof(phBuffer), "%.2f", livePH);
  } else {
    snprintf(phBuffer, sizeof(phBuffer), "%.2f", currentPH);
  }
  return phBuffer;
}

void samplePH() {
  unsigned long now = millis();

  if (now - lastSampleTime >= SAMPLE_INTERVAL_MS) {
    lastSampleTime = now;

    int rawPH = analogRead(ANALOG_PH_PIN);
    float voltage = rawPH * (3.3f / 4095.0f);
    sumPHVoltage += voltage;
    currentSampleCount++;

    if (currentSampleCount >= SAMPLES_PER_MEASUREMENT) {
      float avgPHVoltage = sumPHVoltage / currentSampleCount;
      currentPH = M_PH * avgPHVoltage + B_PH;

      sumPHVoltage = 0.0f;
      currentSampleCount = 0;
    }
  }
}

//***********CO2 Sensor***********
const char* ReadCO2() {
  if (!scd30Initialised) {
    if (scd30.begin()) {
      scd30.setMeasurementInterval(5);
      scd30Initialised = true;
    } else {
      snprintf(co2Buf, sizeof(co2Buf), "{\"CO2\":\"SENSOR_ERROR\",\"AirTemperature\":\"N/A\",\"Humidity\":\"N/A\"}");
      return co2Buf;
    }
  }

  return MeasureCO2();
}

const char* MeasureCO2() {
  unsigned long now = millis();

  if (now - lastCO2Read < CO2Interval) {
    snprintf(co2Buf, sizeof(co2Buf),
             "{\"CO2\":\"WAITING\",\"AirTemperature\":\"N/A\",\"Humidity\":\"N/A\"}");
    return co2Buf;
  }

  if (scd30.dataReady()) {
    lastCO2Read = now; // only update when there is a reading

    if (!scd30.read()) {
      snprintf(co2Buf, sizeof(co2Buf), "{\"CO2\":\"READ_ERROR\",\"AirTemperature\":\"N/A\",\"Humidity\":\"N/A\"}");
      return co2Buf;
    }

    snprintf(co2Buf, sizeof(co2Buf),
             "{\"CO2\":\"%.1f\",\"AirTemperature\":\"%.1f\",\"Humidity\":\"%.1f\"}",
             scd30.CO2, scd30.temperature, scd30.relative_humidity);
    return co2Buf;
  } else {
    snprintf(co2Buf, sizeof(co2Buf), "{\"CO2\":\"WAITING\",\"AirTemperature\":\"N/A\",\"Humidity\":\"N/A\"}");
    return co2Buf;
  }
}

// *********** PUMP CONTROL **********
void handlePumpCommand(String cmd) {
  //Serial.println("HANDLER CALLED");
  cmd.trim();

  if (cmd.startsWith("DOSE_UP:")) {
    //Serial.println("DOSE_UP DETECTED");
    float duration = cmd.substring(8).toFloat();
    runPump(PH_UP_PUMP, duration);
  }
  else if (cmd.startsWith("DOSE_DOWN:")) {
    //Serial.println("DOSE_DOWN DETECTED");
    float duration = cmd.substring(10).toFloat();
    runPump(PH_DOWN_PUMP, duration);
  }
}

void runPump(int pin, float duration) {
  /*Serial.print("PUMP ");
  Serial.print(pin);
  Serial.println(" HAS STARTED");*/
  digitalWrite(pin, HIGH);

  pumpRunning = true;
  activePump = pin;
  pumpStartTime = millis();
  pumpDuration = duration * 1000;
}

void updatePump() {
  if (pumpRunning) {
    if (millis() - pumpStartTime >= pumpDuration) {
      digitalWrite(activePump, LOW);
      /*Serial.print("STOPPING PUMP "); 
      Serial.print(activePump); 
      Serial.println(" NOW");*/
      pumpRunning = false;
      activePump = -1;
    }
  }
}
