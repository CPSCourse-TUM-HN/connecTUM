#include "AccelStepper.h"
#include "AccelStepperWithDistance.h"

#define dirPin 4
#define stepPin 2
#define limitSwitchPin 13
#define motorInterfaceType 1

// to fix access to tty0
// sudo chmod a+rw /dev/ttyUSB0
static volatile bool homingComplete = false;
static bool get_homingComplete() {
  bool val;
  noInterrupts();
  val = homingComplete;
  interrupts();
  return val;
}

AccelStepperWithDistance stepper(AccelStepperWithDistance::DRIVER, stepPin, dirPin);

void handleLimitSwitch() {
  if (digitalRead(limitSwitchPin) == LOW) {  // Confirm switch state
    stepper.stop();
    stepper.setCurrentPosition(0);          // Set home position
    noInterrupts();
    homingComplete = true;
    interrupts();
  }
}

void setup() {
  Serial.begin(9600);

  pinMode(limitSwitchPin, INPUT_PULLUP);
  attachInterrupt(limitSwitchPin, handleLimitSwitch, FALLING);

  stepper.setMaxSpeed(36000);
  stepper.setAcceleration(20000);
  stepper.setStepsPerRotation(200);  // For a 1.8° stepper motor
  stepper.setMicroStep(16);          // If using 1/16 microstepping
  stepper.setDistancePerRotation(8); // based on the threads/mm

  // Homing procedure
  stepper.setSpeed(-1000);  // Slow reverse speed for homing
  while (!get_homingComplete()) {
    stepper.runSpeed();
  }
  
  // Back off from switch (10mm) and reset home
  Serial.println("back off");
  stepper.moveToDistance(10);
  while (stepper.distanceToGo() != 0) {
    stepper.run();
  }
  stepper.setCurrentPosition(0);  // New home position
}

int pos = 0;
int dest = 0;
int tileWidth=26; //mm
float loaderOffset = 50; //mm after the last column (to go to loader)
int tileCount = 8; //including loader as last position


void loop() {
  // upon bytes available in the serial interface
  if(Serial.available()){
  // Set the target position:
    pos = Serial.parseInt();
    dest = (pos%tileCount) * tileWidth;
    if(pos == 7) dest += loaderOffset;
    stepper.runToNewDistance(dest);
  }
  delay(50);
}