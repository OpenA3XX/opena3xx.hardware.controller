import time

from opena3xx.hardware.gpio_shim import GPIO

from opena3xx.models import FAULT_LED, GENERAL_LED, MESSAGING_LED


class OpenA3XXHardwareLightsService:
    """Simple LED pattern helper for basic visual feedback during init."""

    @staticmethod
    def init_pattern():
        """Flash LEDs in a brief startup pattern to indicate activity."""
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