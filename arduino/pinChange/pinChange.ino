#define NO_PORTC_PINCHANGES // to indicate that port c will not be used for pin change interrupts
#define DISABLE_PCINT_MULTI_SERVICE

#include <PinChangeInt.h>


// use micros() for precision, overflow after 70minutes
// use millis() for long experiment, overflow after 50 days

void dispfunc() {
  Serial.print(PCintPort::arduinoPin);
  Serial.print(":");
  Serial.print(PCintPort::pinState);
  Serial.print(":");
//  Serial.println(micros());
  Serial.println(millis());
};

void setup() {
  for (int thisPin = 3; thisPin < 13; thisPin++) {
    pinMode(thisPin, INPUT);
    PCintPort::attachInterrupt(thisPin, &dispfunc, CHANGE);
  } 
  Serial.begin(115200);
}

void loop() {
  if (Serial.available() > 0) {
    int inByte = Serial.read();
    switch (inByte) {
      case 't':    
        Serial.print("t:");
//        Serial.println(micros());
        Serial.println(millis());
        break;
      }
  }
}

