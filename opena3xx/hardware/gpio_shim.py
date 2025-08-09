import logging
import threading
import time
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class _BackendBase:
    def setup_output(self, pin: int) -> None:
        raise NotImplementedError

    def setup_input(self, pin: int, pull_up: bool = False) -> None:
        raise NotImplementedError

    def write(self, pin: int, value: int) -> None:
        raise NotImplementedError

    def read(self, pin: int) -> int:
        raise NotImplementedError

    def cleanup(self) -> None:
        pass


class _GpiodBackend(_BackendBase):
    def __init__(self):
        import gpiod
        self.gpiod = gpiod
        # Use gpiochip0
        self.chip = gpiod.Chip('gpiochip0')
        self.lines_out: Dict[int, any] = {}
        self.lines_in: Dict[int, any] = {}

    def setup_output(self, pin: int) -> None:
        if pin in self.lines_out:
            return
        line = self.chip.get_line(pin)
        line.request(consumer='opena3xx', type=self.gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
        self.lines_out[pin] = line

    def setup_input(self, pin: int, pull_up: bool = False, pull_down: bool = False) -> None:
        if pin in self.lines_in:
            return
        line = self.chip.get_line(pin)
        # Try to set bias if supported
        flags = 0
        try:
            if pull_up and hasattr(self.gpiod, 'LINE_REQ_FLAG_BIAS_PULL_UP'):
                flags |= self.gpiod.LINE_REQ_FLAG_BIAS_PULL_UP
            if pull_down and hasattr(self.gpiod, 'LINE_REQ_FLAG_BIAS_PULL_DOWN'):
                flags |= self.gpiod.LINE_REQ_FLAG_BIAS_PULL_DOWN
        except Exception:
            pass
        line.request(consumer='opena3xx', type=self.gpiod.LINE_REQ_DIR_IN, flags=flags)
        self.lines_in[pin] = line

    def write(self, pin: int, value: int) -> None:
        self.lines_out[pin].set_value(1 if value else 0)

    def read(self, pin: int) -> int:
        return 1 if self.lines_in[pin].get_value() else 0

    def cleanup(self) -> None:
        for line in list(self.lines_out.values()) + list(self.lines_in.values()):
            try:
                line.release()
            except Exception:
                pass
        self.lines_out.clear()
        self.lines_in.clear()


class _LgpioBackend(_BackendBase):
    def __init__(self):
        import lgpio
        self.lgpio = lgpio
        # Open default chip 0
        self.handle = lgpio.gpiochip_open(0)
        self.outputs: Dict[int, bool] = {}
        self.inputs: Dict[int, bool] = {}

    def setup_output(self, pin: int) -> None:
        if pin in self.outputs:
            return
        self.lgpio.gpio_claim_output(self.handle, pin, 0)
        self.outputs[pin] = True

    def setup_input(self, pin: int, pull_up: bool = False, pull_down: bool = False) -> None:
        if pin in self.inputs:
            return
        flags = 0
        # Attempt to set bias pull-up if-supported (older kernels may ignore)
        try:
            if pull_up and hasattr(self.lgpio, 'SET_BIAS_PULL_UP'):
                flags |= self.lgpio.SET_BIAS_PULL_UP
            if pull_down and hasattr(self.lgpio, 'SET_BIAS_PULL_DOWN'):
                flags |= self.lgpio.SET_BIAS_PULL_DOWN
        except Exception:
            pass
        self.lgpio.gpio_claim_input(self.handle, pin, flags)
        self.inputs[pin] = True

    def write(self, pin: int, value: int) -> None:
        self.lgpio.gpio_write(self.handle, pin, 1 if value else 0)

    def read(self, pin: int) -> int:
        return self.lgpio.gpio_read(self.handle, pin)

    def cleanup(self) -> None:
        try:
            self.lgpio.gpiochip_close(self.handle)
        except Exception:
            pass
        self.outputs.clear()
        self.inputs.clear()


class _RPiBackend(_BackendBase):
    def __init__(self):
        import RPi.GPIO as RPiGPIO
        self.GPIO = RPiGPIO
        self.GPIO.setmode(self.GPIO.BCM)

    def setup_output(self, pin: int) -> None:
        self.GPIO.setup(pin, self.GPIO.OUT)

    def setup_input(self, pin: int, pull_up: bool = False, pull_down: bool = False) -> None:
        if pull_up:
            self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        elif pull_down:
            self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_DOWN)
        else:
            self.GPIO.setup(pin, self.GPIO.IN)

    def write(self, pin: int, value: int) -> None:
        self.GPIO.output(pin, self.GPIO.HIGH if value else self.GPIO.LOW)

    def read(self, pin: int) -> int:
        return self.GPIO.input(pin)

    def cleanup(self) -> None:
        self.GPIO.cleanup()


class GPIO:
    HIGH = 1
    LOW = 0
    IN = 0
    OUT = 1
    FALLING = 0
    BCM = 0
    PUD_OFF = 0
    PUD_UP = 1
    PUD_DOWN = 2

    _backend: _BackendBase = None  # type: ignore
    _event_threads: Dict[int, threading.Thread] = {}
    _event_stop_flags: Dict[int, bool] = {}
    _event_callbacks: Dict[int, Callable[[int], None]] = {}
    _event_bounce_ms: Dict[int, int] = {}

    @classmethod
    def _ensure_backend(cls):
        if cls._backend is not None:
            return
        try:
            cls._backend = _LgpioBackend()
            logger.info("GPIO shim using lgpio backend")
            return
        except Exception:
            pass
        try:
            cls._backend = _GpiodBackend()
            logger.info("GPIO shim using gpiod backend")
            return
        except Exception:
            pass
        cls._backend = _RPiBackend()
        logger.info("GPIO shim using RPi.GPIO backend")

    @classmethod
    def setmode(cls, _mode):
        cls._ensure_backend()

    @classmethod
    def setup(cls, pin: int, direction: int, pull_up_down: Optional[int] = None):
        cls._ensure_backend()
        if direction == cls.OUT:
            cls._backend.setup_output(pin)
        else:
            pull_up = pull_up_down == cls.PUD_UP
            pull_down = pull_up_down == cls.PUD_DOWN
            # type: ignore[attr-defined]
            try:
                cls._backend.setup_input(pin, pull_up=pull_up, pull_down=pull_down)  # type: ignore[misc]
            except TypeError:
                # Backcompat for backends without pull_down param
                cls._backend.setup_input(pin, pull_up=pull_up)

    @classmethod
    def output(cls, pin: int, value: int):
        cls._ensure_backend()
        cls._backend.write(pin, value)

    @classmethod
    def input(cls, pin: int) -> int:
        cls._ensure_backend()
        return cls._backend.read(pin)

    @classmethod
    def add_event_detect(cls, pin: int, edge: int, callback: Callable[[int], None], bouncetime: int = 10):
        cls._ensure_backend()
        # Software edge detection loop (falling edge)
        if pin in cls._event_threads:
            return
        cls._event_callbacks[pin] = callback
        cls._event_bounce_ms[pin] = max(0, bouncetime)
        cls._event_stop_flags[pin] = False

        def _loop():
            last = cls._backend.read(pin)
            last_time = 0.0
            while not cls._event_stop_flags.get(pin, False):
                val = cls._backend.read(pin)
                now = time.monotonic()
                if edge == cls.FALLING and last == 1 and val == 0:
                    if (now - last_time) * 1000.0 >= cls._event_bounce_ms[pin]:
                        try:
                            cls._event_callbacks[pin](pin)
                        except Exception as ex:
                            logger.exception(ex)
                        last_time = now
                last = val
                time.sleep(0.001)

        t = threading.Thread(target=_loop, daemon=True)
        cls._event_threads[pin] = t
        t.start()

    @classmethod
    def remove_event_detect(cls, pin: int):
        if pin in cls._event_threads:
            cls._event_stop_flags[pin] = True
            try:
                cls._event_threads[pin].join(timeout=0.5)
            except Exception:
                pass
            cls._event_threads.pop(pin, None)
            cls._event_callbacks.pop(pin, None)
            cls._event_bounce_ms.pop(pin, None)
            cls._event_stop_flags.pop(pin, None)

    @classmethod
    def cleanup(cls):
        for pin in list(cls._event_threads.keys()):
            cls.remove_event_detect(pin)
        if cls._backend is not None:
            cls._backend.cleanup()


