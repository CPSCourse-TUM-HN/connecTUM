#include "AccelStepper.h"
#include "AccelStepperWithDistance.h"
#include <ESP32Servo.h>

#define dirPin 4
#define stepPin 2
#define limitSwitchPin 13
#define coinDispenserServoPin 26
#define coinDropperServoPin 14
#define tileWidth 26 //mm
#define loaderOffset 50 //mm after the last column (to go to loader)
#define tileCount 8 //including loader as last position
#define loaderPosition 7 // as index 
#define homeOffset 4 //mm distance between home click and actual 0 position (over 0th column)

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
static void set_homingComplete(bool val) {
  noInterrupts();
  homingComplete = val;
  interrupts();
}
// Servo
Servo coinDispenserServo;
Servo coinDropperServo;
AccelStepperWithDistance stepper(AccelStepperWithDistance::DRIVER, stepPin, dirPin);

void handleLimitSwitch() {
  if (!get_homingComplete() && digitalRead(limitSwitchPin) == LOW) {  // Confirm switch state
    stepper.stop();
    stepper.setCurrentPosition(0);          // Set home position
    set_homingComplete(true);
  }
}

void setup() {
  Serial.begin(9600);

  pinMode(limitSwitchPin, INPUT_PULLUP);
  attachInterrupt(limitSwitchPin, handleLimitSwitch, FALLING);

  coinDispenserServo.attach(coinDispenserServoPin);
  coinDispenserServo.write(170);

  coinDropperServo.attach(coinDropperServoPin);
  coinDropperServo.write(30);

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
  
  // Back off from switch to actual 0 position
  Serial.println("back off");
  stepper.runToNewDistance(homeOffset);
  stepper.setCurrentPosition(0);

  delay(50);
}

int pos = 0;
int dest = 0;

void loop() {
  // upon bytes available in the serial interface
  if(Serial.available()) {
  // Set the target position:
    pos = Serial.parseInt();

    if(pos == 100) {
      coinDispenserServo.write(80);
      delay(1500);
      coinDispenserServo.write(170);
    } else if(pos == 200) {
      coinDropperServo.write(130);
      delay(1500);
      coinDropperServo.write(30);
      delay(1000);
      stepper.runToNewDistance((loaderPosition * tileWidth) + loaderOffset); // go to loader position
    } else {
      dest = (pos%tileCount) * tileWidth;
      if(pos == 7) dest += loaderOffset;
      stepper.runToNewDistance(dest);
    }
    
  }
  delay(50);
}
