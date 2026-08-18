import serial
import time

PORT = "/dev/ttyACM0"
BAUDRATE = 115200

ser = serial.Serial(
    PORT,
    BAUDRATE,
    timeout=0.5
)

time.sleep(2)

ser.reset_input_buffer()

print("Puerto abierto")
print("Enviando R...")

ser.write(b'R')
ser.flush()

start = time.time()

while time.time() - start < 10:

    line = ser.readline()

    if line:
        print("RAW:", repr(line))

print()
print("Enviando S...")

ser.write(b'S')
ser.flush()

time.sleep(0.5)

while ser.in_waiting:
    print("RAW:", repr(ser.readline()))

ser.close()
