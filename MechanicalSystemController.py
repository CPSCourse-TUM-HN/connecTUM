import time
import board
import busio
import adafruit_pcf8574
import adafruit_vl53l0x
from adafruit_pca9685 import PCA9685
from tmc_driver.tmc_2209 import *

# Constants for hardware configuration
STEPPER_POSITIONS_N = 9
STEPPER_COLUMN_SPACING = 20  # Spacing between columns in mm

# Stepper Motor and Lead Screw Specifications
# NEMA17 stepper: 1.8° per step = 200 steps per revolution
# Reference: https://www.omc-stepperonline.com/nema-17-stepper-motor
STEPPER_DEGREES_PER_STEP = 1.8  # Standard NEMA17 step angle
STEPPER_STEPS_PER_REV = 360 / STEPPER_DEGREES_PER_STEP  # 200 steps per revolution
LEADSCREW_PITCH_MM = 2.0  # Lead screw pitch in mm per revolution (common values: 1, 2, 4, 8mm)
                          # Adjust based on your actual lead screw specification
                          # Higher pitch = faster travel, lower precision

# Calculate steps per mm for positioning
# Steps per mm = (steps per revolution) / (mm per revolution)
STEPS_PER_MM = STEPPER_STEPS_PER_REV / LEADSCREW_PITCH_MM  # With microstepping, multiply by microstepping factor

# Position calculations (all in mm from home position)
STEPPER_LOADING_OFFSETS = [0, 8]  # Column positions for loaders (first and last columns)
STEPPER_LOADER1_POSITION_MM = -10.0  # Loader 1 position in mm (negative = before column 0)
STEPPER_LOADER2_POSITION_MM = (STEPPER_POSITIONS_N - 1) * STEPPER_COLUMN_SPACING + 10.0  # Loader 2 position (after last column)

STEPPER_DEFAULT_SPEED = 200  # Steps per second (will be converted to mm/s in calculations)

# TMC2209 Configuration Constants
# Reference: https://www.trinamic.com/fileadmin/assets/Products/ICs/TMC2209_Datasheet_V103.pdf
# MKS TMC2209 v2.0 specific guide: https://github.com/makerbase-mks/MKS-TMC2209
# Additional guide: https://github.com/Chr157i4n/TMC2209_Raspberry_Pi
TMC2209_BAUDRATE = 115200  # UART communication speed - standard for MKS TMC2209 v2.0
TMC2209_DEFAULT_CURRENT = 600  # Motor current in mA (MKS v2.0 supports up to 2.8A peak)
                               # For NEMA17: typical 1.2-1.7A, start with 600-800mA
                               # MKS v2.0 current calculation: I_rms = (CS+1)/32 * Vref/(Rs*√2)
                               # Ref: MKS TMC2209 v2.0 manual section 3.2
TMC2209_HOMING_CURRENT = 300  # Reduced current for homing (50% of default)
                              # Lower current prevents damage when hitting mechanical limits
TMC2209_STALLGUARD_THRESHOLD = 63  # StallGuard sensitivity (0-255, higher = less sensitive)
                                   # MKS v2.0 recommended range: 50-100 for most steppers
                                   # Tune based on motor load and mechanical resistance
                                   # Ref: TMC2209 datasheet section 9.1
TMC2209_TCOOLTHRS = 20  # CoolStep lower threshold velocity (0-1048575)
                        # MKS v2.0: Above this velocity, CoolStep and StallGuard activate
                        # Lower values = more sensitive, but may cause false triggers
                        # Ref: TMC2209 datasheet section 6.4
TMC2209_SGTHRS = 63  # StallGuard threshold for sensorless homing (0-255)
                     # MKS v2.0: Lower values = more sensitive stall detection
                     # Start with 63, decrease if homing unreliable, increase if false triggers
                     # Must be tuned with actual load and motor characteristics
TMC2209_MICROSTEPPING = 16  # Microstepping resolution (1, 2, 4, 8, 16, 32, 64, 128, 256)
                            # MKS v2.0 supports up to 256 microsteps
                            # 16x provides good balance: smooth motion, adequate torque
                            # Higher values reduce torque but increase smoothness
                            # Ref: MKS TMC2209 v2.0 manual Table 2
TMC2209_HOMING_SPEED = 50  # Homing speed in steps/sec (adjust for microstepping)
                           # MKS v2.0: Too fast may miss stalls, too slow increases homing time
                           # With 16x microstepping: 50 steps/sec = ~3 RPM for 200-step motor
TMC2209_HOMING_OFFSET_STEPS = 50  # Steps to move away from limit after homing
                                  # MKS v2.0: Prevents continuous stall condition
                                  # Adjust based on mechanical backlash and precision needs
TMC2209_HOMING_MAX_STEPS = -10000  # Maximum steps during homing (negative for reverse)
                                   # MKS v2.0: Should exceed maximum travel distance
                                   # Safety limit to prevent infinite movement
TMC2209_HOMING_TIMEOUT = 5000  # Timeout in polling cycles (50 seconds at 0.01s intervals)
                               # MKS v2.0: Prevents infinite homing attempts
                               # Increase if mechanical system is slow
TMC2209_HOMING_SETTLE_TIME = 0.5  # Motor settle time after stall detection (seconds)
                                  # MKS v2.0: Allows mechanical vibrations to dampen
                                  # Critical for accurate position setting

# Servo Configuration Constants
# Standard servo control uses 50Hz PWM with 1-2ms pulse widths
# Reference: https://learn.adafruit.com/16-channel-pwm-servo-driver/using-the-adafruit-library
SERVO_DROP_CHANNEL = 0      # PCA9685 channel for token drop servo
SERVO_LOADER1_CHANNEL = 1   # PCA9685 channel for loader 1 servo
SERVO_LOADER2_CHANNEL = 2   # PCA9685 channel for loader 2 servo
SERVO_MIN_PULSE = 1000  # Minimum pulse width in microseconds (typically 1000-1500μs)
                        # Corresponds to 0° position for most servos
                        # Ref: https://www.servocity.com/how-does-a-servo-work
SERVO_MAX_PULSE = 2000  # Maximum pulse width in microseconds (typically 1500-2000μs)
                        # Corresponds to 180° position for most servos
SERVO_DROP_ANGLE = 90   # Angle for token drop action (degrees)
                        # Adjust based on mechanical design
SERVO_LOAD_ANGLE = 90   # Angle for loader activation (degrees)
                        # May need different values for each loader
SERVO_PWM_FREQUENCY = 50  # Standard servo frequency (50Hz = 20ms period)
                          # Most servos expect 50Hz, some can handle 100Hz
                          # Ref: PCA9685 datasheet and servo specifications
SERVO_ACTIVATION_TIME = 0.5  # Time to hold servo position (seconds)
                             # Allows mechanical action to complete

# VL53L0X ToF Sensor Constants
# Reference: https://www.st.com/en/imaging-and-photonics-solutions/vl53l0x.html
# Adafruit guide: https://learn.adafruit.com/adafruit-vl53l0x-micro-lidar-distance-sensor-breakout
VL53L0X_DEFAULT_ADDRESS = 0x29  # Factory default I2C address for VL53L0X
                                # All sensors start with this address
VL53L0X_1_XSHUT_PIN = "p0"     # Legacy pin naming (not used with new implementation)
VL53L0X_2_XSHUT_PIN = "p1"     # Legacy pin naming (not used with new implementation)
TOF1_ADDRESS = 0x30  # New I2C address for first sensor after address change
                     # Valid range: 0x08-0x77 (avoid reserved addresses)
TOF2_ADDRESS = 0x31  # New I2C address for second sensor after address change
                     # Must be different from TOF1_ADDRESS
TOF_FULL_THRESHOLD_MM = 30   # Distance indicating loader is full (millimeters)
                             # VL53L0X range: 30-2000mm (optimal: 50-1200mm)
                             # Adjust based on token size and loader geometry
TOF_EMPTY_THRESHOLD_MM = 100  # Distance indicating loader is empty (millimeters)
                              # Should be > TOF_FULL_THRESHOLD_MM + safety margin
TOF_INIT_DELAY = 0.01  # Delay during sensor initialization (seconds)
                       # Required for proper I2C communication timing
                       # Ref: VL53L0X datasheet timing requirements

# I2C Device Addresses
# Standard 7-bit I2C addresses - check with i2cdetect command
# Reference: https://learn.adafruit.com/i2c-addresses/the-list
PCF8574_ADDRESS = 0x20  # PCF8574 I2C expander address
                        # Default range: 0x20-0x27 (A0,A1,A2 pins set address)
                        # Datasheet: https://www.ti.com/lit/ds/symlink/pcf8574.pdf
PCA9685_ADDRESS = 0x40  # PCA9685 PWM driver address
                        # Default range: 0x40-0x7F (A0-A5 pins set address)
                        # Datasheet: https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf

# PCF8574 Pin Mapping
# PCF8574 has 8 I/O pins (P0-P7), all bidirectional with weak pull-ups
# Reference: PCF8574 datasheet section 7.1
PCF8574_TOF1_XSHUT_PIN = 0  # Pin P0 for ToF sensor 1 XSHUT control
                            # XSHUT pin controls sensor power/reset state
PCF8574_TOF2_XSHUT_PIN = 1  # Pin P1 for ToF sensor 2 XSHUT control
                            # HIGH = sensor active, LOW = sensor in reset

# Timing Constants
# Fine-tuned for reliable operation and responsiveness
MOVEMENT_POLL_INTERVAL = 0.01  # Polling interval for movement completion (seconds)
                               # Balance between responsiveness and CPU usage
                               # Too fast = high CPU load, too slow = delayed response
EMERGENCY_STOP_DELAY = 0.1     # Delay after emergency stop (seconds)
                               # Allows motor driver to process stop command

class MechanicalSystemController:
    """
    Controls the mechanical subsystem: stepper, servos, and ToF sensors.
    """
    def __init__(self, i2c_bus=None, stepper_uart_port="/dev/serial0", stepper_address=0):
        try:
            self.i2c = i2c_bus or busio.I2C(board.SCL, board.SDA)
            
            # Initialize TMC2209 stepper driver using Chr157i4n library
            self.stepper = Tmc2209(stepper_uart_port, TMC2209_BAUDRATE, stepper_address)
            
            # Configure TMC2209 settings
            self.stepper.set_direction_reg(False)
            self.stepper.set_current(TMC2209_DEFAULT_CURRENT)
            self.stepper.set_interpolation(True)
            self.stepper.set_spreadcycle(False)
            self.stepper.set_microstepping_resolution(TMC2209_MICROSTEPPING)
            
            # Configure stallGuard for sensorless homing
            self.stepper.set_stallguard_threshold(TMC2209_STALLGUARD_THRESHOLD)
            self.stepper.set_tcoolthrs(TMC2209_TCOOLTHRS)
            self.stepper.set_sgthrs(TMC2209_SGTHRS)
            
            self.stepper.set_motor_enabled(True)
            
            # Initialize PCF8574 with Adafruit library
            self.pcf = adafruit_pcf8574.PCF8574(self.i2c, address=PCF8574_ADDRESS)
            
            # Hold both sensors in reset to assign addresses
            self.pcf[PCF8574_TOF1_XSHUT_PIN].value = False
            self.pcf[PCF8574_TOF2_XSHUT_PIN].value = False
            time.sleep(TOF_INIT_DELAY)

            # Power up sensor 1 only, assign new address
            self.pcf[PCF8574_TOF1_XSHUT_PIN].value = True
            time.sleep(TOF_INIT_DELAY)
            vl53_1 = adafruit_vl53l0x.VL53L0X(self.i2c)
            vl53_1.set_address(TOF1_ADDRESS)
            time.sleep(TOF_INIT_DELAY)

            # Power up sensor 2 only, assign new address
            self.pcf[PCF8574_TOF2_XSHUT_PIN].value = True
            time.sleep(TOF_INIT_DELAY)
            vl53_2 = adafruit_vl53l0x.VL53L0X(self.i2c)
            vl53_2.set_address(TOF2_ADDRESS)
            time.sleep(TOF_INIT_DELAY)

            # Re-initialize both sensors at their new addresses
            self.tof1 = adafruit_vl53l0x.VL53L0X(self.i2c, address=TOF1_ADDRESS)
            self.tof2 = adafruit_vl53l0x.VL53L0X(self.i2c, address=TOF2_ADDRESS)

            # Initialize PCA9685 for servo control
            self.pca = PCA9685(self.i2c, address=PCA9685_ADDRESS)
            self.pca.frequency = SERVO_PWM_FREQUENCY

            # Calculate actual steps per mm including microstepping
            self.steps_per_mm = STEPS_PER_MM * TMC2209_MICROSTEPPING
            print(f"Calculated steps per mm: {self.steps_per_mm}")
            
            # Track stepper position
            self.current_position = 0
            self.stepper_steps_from_home = 0
            self.is_homed = False
            
        except Exception as e:
            raise RuntimeError(f"Initialization failed: {e}")

    def _mm_to_steps(self, distance_mm):
        """
        Convert millimeter distance to motor steps.
        
        Args:
            distance_mm (float): Distance in millimeters
            
        Returns:
            int: Number of steps required
        """
        return int(distance_mm * self.steps_per_mm)

    def _column_to_mm(self, column):
        """
        Convert column number to millimeter position.
        
        Args:
            column (int): Column number (0-8)
            
        Returns:
            float: Position in millimeters from home
        """
        if column in STEPPER_LOADING_OFFSETS:
            if column == 0:
                return STEPPER_LOADER1_POSITION_MM
            elif column == 8:
                return STEPPER_LOADER2_POSITION_MM
        else:
            # Regular column position
            return column * STEPPER_COLUMN_SPACING
        
        raise ValueError(f"Invalid column number: {column}")

    # --- Stepper Motor Control ---

    def home_stepper(self):
        """
        Home the stepper motor using stallGuard sensorless homing.
        Drives to the mechanical limit until stall is detected via DIAG pin.
        """
        try:
            print("Starting sensorless homing...")
            
            # Set lower current for homing to reduce impact
            self.stepper.set_current(TMC2209_HOMING_CURRENT)
            
            # Enable stallGuard for homing
            self.stepper.set_stallguard_threshold(TMC2209_STALLGUARD_THRESHOLD)
            
            # Set homing speed
            self.stepper.set_max_speed(TMC2209_HOMING_SPEED)
            
            # Move towards home position
            self.stepper.set_movement_abs_rel(MovementAbsRel.relative)
            
            # Start moving towards limit
            self.stepper.run_to_position_steps(TMC2209_HOMING_MAX_STEPS)
            
            # Monitor stallGuard result until stall is detected
            stall_detected = False
            timeout_counter = 0
            
            while not stall_detected and timeout_counter < TMC2209_HOMING_TIMEOUT:
                sg_result = self.stepper.get_stallguard_result()
                if sg_result == 0:  # StallGuard triggered (stall detected)
                    stall_detected = True
                    self.stepper.stop()
                    print("Stall detected - home position found")
                    break
                    
                time.sleep(MOVEMENT_POLL_INTERVAL)
                timeout_counter += 1
            
            if not stall_detected:
                raise RuntimeError("Homing timeout - no stall detected")
            
            # Stop and wait for motor to settle
            time.sleep(TMC2209_HOMING_SETTLE_TIME)
            
            # Reset position counter to zero (this is now home)
            self.stepper.set_actual_position(0)
            
            # Move slightly away from the limit to avoid continuous stall
            self.stepper.run_to_position_steps(TMC2209_HOMING_OFFSET_STEPS)
            while not self.stepper.is_movement_finished():
                time.sleep(MOVEMENT_POLL_INTERVAL)
            
            # Reset position to zero after offset
            self.stepper.set_actual_position(0)
            
            # Restore original current and speed
            self.stepper.set_current(TMC2209_DEFAULT_CURRENT)
            self.stepper.set_max_speed(STEPPER_DEFAULT_SPEED)
            
            # Update internal tracking
            self.current_position = 0
            self.stepper_steps_from_home = 0
            self.is_homed = True
            
            print("Sensorless homing completed successfully")
            
        except Exception as e:
            print(f"Stepper homing error: {e}")
            self.is_homed = False
            # Restore original settings even on error
            try:
                self.stepper.set_current(TMC2209_DEFAULT_CURRENT)
                self.stepper.set_max_speed(STEPPER_DEFAULT_SPEED)
            except:
                pass

    def move_stepper_to(self, position):
        """
        Move the stepper to one of 9 positions (0-8).
        Positions 0 and 8 are loader offsets; 1-7 are board columns.
        Calculates actual mm position and converts to steps.
        """
        if not (0 <= position < STEPPER_POSITIONS_N):
            raise ValueError("Invalid stepper position")
        
        if not self.is_homed:
            print("Warning: Stepper not homed. Attempting to home first.")
            self.home_stepper()
            if not self.is_homed:
                raise RuntimeError("Cannot move stepper - homing failed")
        
        try:
            # Convert column number to mm position
            target_position_mm = self._column_to_mm(position)
            
            # Convert mm to steps
            target_steps = self._mm_to_steps(target_position_mm)
            
            print(f"Moving to column {position}: {target_position_mm}mm = {target_steps} steps")

            # Set movement speed
            self.stepper.set_movement_abs_rel(MovementAbsRel.absolute)
            self.stepper.set_max_speed(STEPPER_DEFAULT_SPEED)
            
            # Move to absolute position
            self.stepper.run_to_position_steps(target_steps)
            
            # Wait for movement to complete
            while not self.stepper.is_movement_finished():
                time.sleep(MOVEMENT_POLL_INTERVAL)

            self.current_position = position
            self.stepper_steps_from_home = target_steps
            print(f"Stepper moved to position {position} ({target_position_mm}mm)")
            
        except Exception as e:
            print(f"Stepper move error: {e}")
            raise

    def get_current_position_mm(self):
        """
        Get the current position in millimeters.
        
        Returns:
            float: Current position in mm from home
        """
        return self.stepper_steps_from_home / self.steps_per_mm

    def get_stepper_position(self):
        """
        Get the current logical position of the stepper motor.
        """
        return self.current_position

    def stop_stepper(self):
        """
        Emergency stop for the stepper motor.
        """
        try:
            self.stepper.stop()
            time.sleep(EMERGENCY_STOP_DELAY)
        except Exception as e:
            print(f"Stepper stop error: {e}")

    # --- Servo Control ---

    def drop_token(self):
        """
        Rotate the drop servo to drop a token, then reset.
        """
        try:
            self._set_servo_angle(SERVO_DROP_CHANNEL, SERVO_DROP_ANGLE)
            time.sleep(SERVO_ACTIVATION_TIME)
            self._set_servo_angle(SERVO_DROP_CHANNEL, 0)
        except Exception as e:
            print(f"Drop servo error: {e}")

    def activate_loader(self, loader_num):
        """
        Activate one of the two loader servos (1 or 2).
        """
        if loader_num not in [1, 2]:
            raise ValueError("Loader number must be 1 or 2")
        channel = SERVO_LOADER1_CHANNEL if loader_num == 1 else SERVO_LOADER2_CHANNEL
        try:
            self._set_servo_angle(channel, SERVO_LOAD_ANGLE)
            time.sleep(SERVO_ACTIVATION_TIME)
            self._set_servo_angle(channel, 0)
        except Exception as e:
            print(f"Loader servo error: {e}")

    def _set_servo_angle(self, channel, angle):
        """
        Set servo to a specific angle (0-90 degrees).
        Converts angle to pulse width and sets PWM.
        """
        pulse = SERVO_MIN_PULSE + (SERVO_MAX_PULSE - SERVO_MIN_PULSE) * angle / 180
        duty = int((pulse / 1000000 * self.pca.frequency) * 0xFFFF)
        self.pca.channels[channel].duty_cycle = duty

    # --- ToF Sensor Queries ---

    def is_loader_full(self, loader_num):
        """
        Returns True if the specified loader (1 or 2) is full, based on ToF sensor.
        """
        sensor = self.tof1 if loader_num == 1 else self.tof2
        try:
            distance = sensor.range
            return distance < TOF_FULL_THRESHOLD_MM
        except Exception as e:
            print(f"ToF sensor error: {e}")
            return False

    def is_loader_empty(self, loader_num):
        """
        Returns True if the specified loader (1 or 2) is empty, based on ToF sensor.
        """
        sensor = self.tof1 if loader_num == 1 else self.tof2
        try:
            distance = sensor.range
            return distance > TOF_EMPTY_THRESHOLD_MM
        except Exception as e:
            print(f"ToF sensor error: {e}")
            return True

    # --- Lifecycle Management ---

    def shutdown(self):
        """
        Safely shutdown all hardware (servos off, stepper disabled, etc.).
        """
        try:
            # Disable stepper motor
            self.stepper.set_motor_enabled(False)
            
            # Shutdown PCA9685
            self.pca.deinit()
            
            print("Hardware shutdown complete")
        except Exception as e:
            print(f"Shutdown error: {e}")





# Example usage and testing function
def test_system():
    """
    Test function to verify all components work correctly.
    """
    try:
        # Initialize the system
        controller = MechanicalSystemController()
        
        # Home the stepper
        controller.home_stepper()
        
        # Test stepper movement
        for pos in range(STEPPER_POSITIONS_N):
            print(f"Moving to position {pos}")
            controller.move_stepper_to(pos)
            time.sleep(1)
        
        # Test ToF sensors
        print(f"Loader 1 full: {controller.is_loader_full(1)}")
        print(f"Loader 2 full: {controller.is_loader_full(2)}")
        
        # Test servos
        controller.drop_token()
        controller.activate_loader(1)
        controller.activate_loader(2)
        
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        controller.shutdown()





# Example usage and testing function
def test_system():
    """
    Test function to verify all components work correctly.
    """
    try:
        # Initialize the system
        controller = MechanicalSystemController()
        
        # Home the stepper
        controller.home_stepper()
        
        # Test stepper movement
        for pos in range(STEPPER_POSITIONS_N):
            print(f"Moving to position {pos}")
            controller.move_stepper_to(pos)
            time.sleep(1)
        
        # Test ToF sensors
        print(f"Loader 1 full: {controller.is_loader_full(1)}")
        print(f"Loader 2 full: {controller.is_loader_full(2)}")
        
        # Test servos
        controller.drop_token()
        controller.activate_loader(1)
        controller.activate_loader(2)
        
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        controller.shutdown()

if __name__ == "__main__":
    test_system()
