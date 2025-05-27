#include "AccelStepper.h"
#include "AccelStepperWithDistance.h"
#include <Servo.h>

#define dirPin 4
#define stepPin 2
#define buttonPin 14
#define potPin 15
#define motorInterfaceType 1

#define unloadServoPin 9
#define loadServoPin 10

Servo loadServo;
Servo unloadServo;

int tileWidth=20; //mm
int tileCount = 10;

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

  loadServo.attach(loadServoPin);
  unloadServo.attach(unloadServoPin);
}

void loop() {
  
}

void play(int pos) {
  //Retreive coin
  loadServo.write(180)
  delat(250)
  loadServo.write(0)
  delay(50)

  // Go to position
  stepper.runToNewDistance((pos*tileWidth)%(tileWidth*tileCount));
  delay(50);

  // Release coin
  unloadServo.write(90)
  delay(250)
  unloadServo.write(0)
  delay(50)

  //Go back to home pos
  stepper.runToNewDistance(0);
  delay(50);
}