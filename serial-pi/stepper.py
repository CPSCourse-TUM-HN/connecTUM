import serial
import time
import sys

# === CONFIGURATION ===
serial_port = '/dev/ttyUSB0'
baud_rate = 9600
timeout_sec = 2

def send_integer(port, baud, number):
    try:
        with serial.Serial(port, baud, timeout=timeout_sec) as ser:
            time.sleep(2)
            ser.write((str(number)).encode('utf-8'))
            print(f"Sent integer '{number}' to ESP32 on {port}")
    except serial.SerialException as e:
        print(f"Serial error: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <integer>")
        sys.exit(1)

    try:
        serial_number = int(sys.argv[1])
    except ValueError:
        print("Error: Argument must be an integer.")
        sys.exit(1)

    send_integer(serial_port, baud_rate, serial_number)

