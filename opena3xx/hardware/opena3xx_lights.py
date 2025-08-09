import time

import RPi.GPIO as GPIO

from opena3xx.models import FAULT_LED, GENERAL_LED, MESSAGING_LED


class OpenA3XXHardwareLightsService:

    @staticmethod
    def init_pattern():
        for loop in range(0, 5):
            GPIO.output(FAULT_LED, GPIO.HIGH)
            GPIO.output(GENERAL_LED, GPIO.LOW)
            GPIO.output(MESSAGING_LED, GPIO.LOW)
            time.sleep(0.05)
            GPIO.output(FAULT_LED, GPIO.LOW)
            GPIO.output(GENERAL_LED, GPIO.HIGH)
            GPIO.output(MESSAGING_LED, GPIO.LOW)
            time.sleep(0.05)
            GPIO.output(FAULT_LED, GPIO.LOW)
            GPIO.output(GENERAL_LED, GPIO.LOW)
            GPIO.output(MESSAGING_LED, GPIO.HIGH)
            time.sleep(0.05)
            GPIO.output(FAULT_LED, GPIO.LOW)
            GPIO.output(GENERAL_LED, GPIO.LOW)
            GPIO.output(MESSAGING_LED, GPIO.LOW)
            time.sleep(0.05)
            GPIO.output(FAULT_LED, GPIO.LOW)
            GPIO.output(GENERAL_LED, GPIO.LOW)
            GPIO.output(MESSAGING_LED, GPIO.HIGH)
            time.sleep(0.05)
            GPIO.output(FAULT_LED, GPIO.LOW)
            GPIO.output(GENERAL_LED, GPIO.HIGH)
            GPIO.output(MESSAGING_LED, GPIO.LOW)
            time.sleep(0.05)
            GPIO.output(FAULT_LED, GPIO.HIGH)
            GPIO.output(GENERAL_LED, GPIO.LOW)
            GPIO.output(MESSAGING_LED, GPIO.LOW)
            time.sleep(0.05)
            GPIO.output(FAULT_LED, GPIO.LOW)
            GPIO.output(GENERAL_LED, GPIO.LOW)
            GPIO.output(MESSAGING_LED, GPIO.LOW)