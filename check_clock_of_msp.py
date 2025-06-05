#!/usr/bin/env python3
"""
Count rising edges on Raspberry Pi GPIO17 (BCM) for a fixed time window.
Wire MSP430 P1.5 (SMCLK ÷ 1024 toggle) → Pi pin 11 (BCM 17).

Expected result:
    ≈ 1 024 Hz  →  MSP430 SMCLK is locked at 1.048 576 MHz.
"""

import RPi.GPIO as GPIO
import time

PIN      = 17      # BCM pin number
WINDOW   = 2.0     # seconds to measure

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

edge_count = 0

def on_rising(channel):
    global edge_count
    edge_count += 1

GPIO.add_event_detect(PIN, GPIO.RISING, callback=on_rising)

time.sleep(WINDOW)               # measurement window

GPIO.remove_event_detect(PIN)
GPIO.cleanup()

frequency = edge_count / WINDOW
print(f"Observed frequency: {frequency:.2f} Hz "
      f"(edges={edge_count}, window={WINDOW}s)")
