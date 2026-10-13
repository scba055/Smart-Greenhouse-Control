/*
  ph_calibration.ino
  DFRobot pH Meter V1.1 with Arduino Uno
  Commands over Serial:
    7 = capture pH 7 buffer voltage
    4 = capture pH 4 buffer voltage
    c = compute calibration
    r = read current pH
*/

const int PH_PIN = A0;
const float ADC_REF = 5.0;        // Uno default analog reference
const int ADC_RESOLUTION = 1023;  // 10-bit ADC

float voltagePH7 = -1.0;
float voltagePH4 = -1.0;

float calSlope = 0.0;
float calIntercept = 0.0;

float readPHVoltage(int pin, int samples = 30) {
  long sum = 0;

  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(30);
  }

  float avgADC = (float)sum / samples;
  float voltage = (avgADC * ADC_REF) / ADC_RESOLUTION;
  return voltage;
}

void capturePH7() {
  voltagePH7 = readPHVoltage(PH_PIN);
  Serial.print("PH7_VOLT:");
  Serial.println(voltagePH7, 4);
}

void capturePH4() {
  voltagePH4 = readPHVoltage(PH_PIN);
  Serial.print("PH4_VOLT:");
  Serial.println(voltagePH4, 4);
}

void computeCalibration() {
  if (voltagePH7 < 0 || voltagePH4 < 0) {
    Serial.println("ERROR: Capture pH 7 and pH 4 first");
    return;
  }

  if (voltagePH7 == voltagePH4) {
    Serial.println("ERROR: Calibration voltages identical");
    return;
  }

  // pH = slope * voltage + intercept
  calSlope = (4.0 - 7.0) / (voltagePH4 - voltagePH7);
  calIntercept = 7.0 - (calSlope * voltagePH7);

  Serial.print("SLOPE:");
  Serial.println(calSlope, 6);

  Serial.print("INTERCEPT:");
  Serial.println(calIntercept, 6);

  Serial.println("CAL_DONE");
}

void readPH() {
  float voltage = readPHVoltage(PH_PIN);
  float phValue = (calSlope * voltage) + calIntercept;

  Serial.print("VOLT:");
  Serial.println(voltage, 4);

  Serial.print("PH:");
  Serial.println(phValue, 2);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("DFROBOT_PH_V1.1_READY");
  Serial.println("Commands: 7, 4, c, r");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "7") {
      capturePH7();
    }
    else if (cmd == "4") {
      capturePH4();
    }
    else if (cmd == "c") {
      computeCalibration();
    }
    else if (cmd == "r") {
      readPH();
    }
    else {
      Serial.print("ERROR: Unknown command ");
      Serial.println(cmd);
    }
  }
}
