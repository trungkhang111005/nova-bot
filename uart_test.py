import serial
import time
import binascii
# Open serial port (adjust /dev/ttyAMA0 if needed)
ser = serial.Serial('/dev/ttyAMA0', baudrate=9600, timeout=1)
time.sleep(2)  # Let MSP430 boot and settle

# Send the test string
test = b"good"
ser.write(test)
print("Sent (hex):", binascii.hexlify(test).decode())

echo = ser.read(len(test))
print("Echoed (hex):", binascii.hexlify(echo).decode())
ser.close()
