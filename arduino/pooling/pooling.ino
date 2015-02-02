

void setup() {
  for (int thisPin = 3; thisPin < 13; thisPin++) {
    pinMode(thisPin, INPUT);
  } 
  Serial.begin(115200);
}

void loop() {
  for (int thisPin = 3; thisPin < 12; thisPin++) {
    Serial.print(digitalRead(thisPin));
  }
  Serial.println(digitalRead(12));
  delay(10);
}

