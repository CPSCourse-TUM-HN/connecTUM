/*
 Controlling a servo position using a potentiometer (variable resistor)
 by Michal Rinott <http://people.interaction-ivrea.it/m.rinott>

 modified on 8 Nov 2013
 by Scott Fitzgerald
 http://www.arduino.cc/en/Tutorial/Knob
*/

#include <Servo.h>

Servo myservo;  // create Servo object to control a servo
int pos = 0;

void setup() {
  myservo.attach(3);
}

void loop() {
  myservo.write(pos);

  if (pos == 0) {
    pos = 90;
  }
  else {
    pos = 0;
  }
  
  delay(2000);
}
