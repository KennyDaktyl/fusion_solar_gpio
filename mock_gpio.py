# mock_gpio.py
class GPIO:
    BCM = "BCM"
    OUT = "OUT"
    HIGH = "HIGH"
    LOW = "LOW"

    @staticmethod
    def setmode(mode):
        print(f"GPIO setmode({mode})")

    @staticmethod
    def setup(pin, mode):
        print(f"GPIO setup(pin={pin}, mode={mode})")

    @staticmethod
    def output(pin, state):
        print(f"GPIO output(pin={pin}, state={state})")

    @staticmethod
    def cleanup():
        print("GPIO cleanup()")
