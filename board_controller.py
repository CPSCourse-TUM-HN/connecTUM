#!/usr/bin/env python3
import time
import RPi.GPIO as GPIO
from gpiozero import Servo
from RpiMotorLib import RpiMotorLib

 # Pin configuration
DIR_PIN = 4
STEP_PIN = 2
BUTTON_PIN = 14

UNLOAD_SERVO_PIN = 9
LOAD_SERVO_PIN = 10

TILE_WIDTH = 20  # mm
TILE_COUNT = 10

# Stepper motor config
STEPS_PER_REV = 200 * 16  # 1.8 deg motor with 1/16 microstepping
DIST_PER_REV = 8  # mm per revolution
STEPS_PER_MM = STEPS_PER_REV / DIST_PER_REV

class BoardController:
    def __init__(self):
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)

        # Global current position (in mm)
        self.current_distance = 0

        # Setup servos (Note: gpiozero.Servo expects pins with PWM support)
        self.load_servo = Servo(LOAD_SERVO_PIN)
        self.unload_servo = Servo(UNLOAD_SERVO_PIN)

        # Setup stepper motor (using RpiMotorLib)
        self.stepper = RpiMotorLib.A4988Nema(DIR_PIN, STEP_PIN, (-1, -1, -1), "A4988")  # MS pins unused

    def move_to_distance(self, new_distance):
        delta = new_distance - self.current_distance
        steps = int(delta * STEPS_PER_MM)
        direction = True if steps >= 0 else False
        self.stepper.motor_go(direction, "Full", abs(steps), 0.0002, False, 0.05)
        self.current_distance = new_distance

        time.sleep(0.05)


    def drop_coin(self):
        self.unload_servo.value = 0  # Middle (90 degrees)
        time.sleep(0.25)
        self.unload_servo.min()  # Reset
        time.sleep(0.05)

    def load_coin(self):
        self.load_servo.max()  # Equivalent to write(180)
        time.sleep(0.25)
        self.load_servo.min()  # Equivalent to write(0)
        time.sleep(0.05)

    def play(self, pos):
        # Retrieve coin
        self.load_coin()

        # Move to position
        target_pos_mm = (pos * TILE_WIDTH) % (TILE_WIDTH * TILE_COUNT)
        self.move_to_distance(target_pos_mm)

        # Release coin
        self.drop_coin()

        # Return to home
        self.move_to_distance(0)


# Example use
if __name__ == "__main__":
    try:
        board = BoardController()
        while True:
            if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                board.play(3)  # For example, drop coin at position 3
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Interrupted by user")

    finally:
        GPIO.cleanup()
