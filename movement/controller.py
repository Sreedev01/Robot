# movement/controller.py

from config.settings import USE_PI

if USE_PI:
    from gpiozero import DigitalOutputDevice, PWMOutputDevice


class MovementController:
    def __init__(self):
        self.current_state = "STOP"

        if USE_PI:
            print("Initializing GPIO for TB6612FNG")

            # Motor direction pins
            self.AIN1 = DigitalOutputDevice(17)
            self.AIN2 = DigitalOutputDevice(27)
            self.BIN1 = DigitalOutputDevice(22)
            self.BIN2 = DigitalOutputDevice(23)

            # PWM pins
            self.PWMA = PWMOutputDevice(18)
            self.PWMB = PWMOutputDevice(19)

            # Standby pin
            self.STBY = DigitalOutputDevice(5)
            self.STBY.on()

        else:
            print("Running in simulation mode")

    # Helper function: convert 0–100 to 0–1 safely
    def _normalize_speed(self, speed):
        speed = max(0, min(speed, 100))  # clamp 0–100
        return speed / 100.0

    def move_forward(self, speed=50):
        if self.current_state != "FORWARD":
            print(f"[MOVEMENT] Forward | Speed: {speed}")
            self.current_state = "FORWARD"

        if USE_PI:
            pwm = self._normalize_speed(speed)

            self.AIN1.on()
            self.AIN2.off()
            self.BIN1.on()
            self.BIN2.off()

            self.PWMA.value = pwm
            self.PWMB.value = pwm
        else:
            print("Moving forward")

    def move_backward(self, speed=50):
        if self.current_state != "BACKWARD":
            print(f"[MOVEMENT] Backward | Speed: {speed}")
            self.current_state = "BACKWARD"

        if USE_PI:
            pwm = self._normalize_speed(speed)

            self.AIN1.off()
            self.AIN2.on()
            self.BIN1.off()
            self.BIN2.on()

            self.PWMA.value = pwm
            self.PWMB.value = pwm
        else:
            print("Moving backward")

    def turn_left(self, speed=50):
        if self.current_state != "LEFT":
            print(f"[MOVEMENT] Turn Left | Speed: {speed}")
            self.current_state = "LEFT"

        if USE_PI:
            pwm = self._normalize_speed(speed)

            self.AIN1.off()
            self.AIN2.on()
            self.BIN1.on()
            self.BIN2.off()

            self.PWMA.value = pwm
            self.PWMB.value = pwm
        else:
            print("Turning left")

    def turn_right(self, speed=50):
        if self.current_state != "RIGHT":
            print(f"[MOVEMENT] Turn Right | Speed: {speed}")
            self.current_state = "RIGHT"

        if USE_PI:
            pwm = self._normalize_speed(speed)

            self.AIN1.on()
            self.AIN2.off()
            self.BIN1.off()
            self.BIN2.on()

            self.PWMA.value = pwm
            self.PWMB.value = pwm
        else:
            print("Turning right")

    def stop(self):
        if self.current_state != "STOP":
            print("[MOVEMENT] Stop")
            self.current_state = "STOP"

        if USE_PI:
            self.PWMA.value = 0
            self.PWMB.value = 0
        else:
            print("Stopping")

    def cleanup(self):
        if USE_PI:
            self.STBY.off()
            print("GPIO cleaned up")