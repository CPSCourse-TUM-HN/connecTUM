#include "AccelStepper.h"
#include "AccelStepperWithDistance.h"

#define dirPin 4
#define stepPin 2
#define buttonPin 14
#define potPin 15
#define motorInterfaceType 1

// to fix access to tty0
// sudo chmod a+rw /dev/ttyUSB0

AccelStepperWithDistance stepper(AccelStepperWithDistance::DRIVER, stepPin, dirPin);

void setup() {
  Serial.begin(9600);

  stepper.setMaxSpeed(36000);
  stepper.setAcceleration(20000);
  stepper.setStepsPerRotation(200);  // For a 1.8° stepper motor
  stepper.setMicroStep(16);          // If using 1/16 microstepping
  stepper.setDistancePerRotation(8); // based on the threads/mm

  pinMode(buttonPin, INPUT);
  pinMode(potPin, INPUT);
}

int pos = 0;
int tileWidth=20; //mm
int tileCount = 10;
void loop() {
  // Set the target position:
  if(Serial.available()) pos = Serial.parseInt();
  stepper.runToNewDistance((pos*tileWidth)%(tileWidth*tileCount));
  delay(50);
}