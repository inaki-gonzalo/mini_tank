import asyncio
import logging

import aiohttp
import cv2

import RPi.GPIO as GPIO


logging.basicConfig(filename='robot_lib.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

pin_left_a = 31
pin_left_b = 33
pin_right_a = 37
pin_right_b = 35
PWM_FREQ = 70  # Hz
MIN_PWM = 12
MAX_PWM = 100

motor_offset = 0

logging.info('----------------------')
logging.info('Start of log')
logging.info('----------------------')


CAMERA_DEVICE = "/dev/video0"
CAMERA_RESOLUTION = (180, 320)

class Camera():
    def __init__(self):
        message = 'Initializing camera, camera_device={}, resolution={}'
        logging.info(message.format(CAMERA_DEVICE, CAMERA_RESOLUTION))
        self.camera = cv2.VideoCapture(0)   # 0 -> index of camera

    async def get_image(self):
        done = False
        while not done:
            done, frame = self.camera.read()
            if done:
                img = cv2.resize(frame, CAMERA_RESOLUTION, interpolation =cv2.INTER_AREA)
                return img
            else:
                await asyncio.sleep(0)

class Motor():
    def __init__(self, name, pin_a, pin_b):
        self.name = name
        message = 'Setting up motor({}) with pin_a={},pin_b={}'
        logging.info(message.format(self.name, pin_a, pin_b))
        GPIO.setup((pin_a, pin_b), GPIO.OUT)
        self.A = GPIO.PWM(pin_a, PWM_FREQ)
        self.B = GPIO.PWM(pin_b, PWM_FREQ)
        self.stop()

    def drive(self, speed):
        if speed > MIN_PWM:
            self.pwm(self.A, speed)
            self.pwm(self.B, 0)
        elif speed < -MIN_PWM:
            self.pwm(self.A, 0)
            self.pwm(self.B, -speed)
        else:
            self.pwm(self.A, 0)
            self.pwm(self.B, 0)

    def pwm(self, channel, unsafe_pwm):
        if unsafe_pwm > MAX_PWM:
            safe_pwm = MAX_PWM
        elif unsafe_pwm < MIN_PWM:
            safe_pwm = 0
        else:
            safe_pwm = unsafe_pwm
        channel.start(safe_pwm)

    def stop(self):
        self.A.stop()
        self.B.stop()

    def __del__(self):
        self.stop()

class Robot():
    def __init__(self):
        logging.info('Initializing robot')
        GPIO.setmode(GPIO.BOARD)
        self.left = Motor('left', pin_left_a, pin_left_b)
        self.right = Motor('right', pin_right_a, pin_right_b)
        self.camera = Camera()
        self.linear_speed = 0
        self.angular_velocity = 0
        self.autopilot_engaged = False
        logging.info('Robot initialized')

    def get_image(self):
        logging.info('Getting image.')
        return self.camera.get_image()

    def stop(self):
        logging.info('Stopping robot.')
        self.left.stop()
        self.right.stop()
        self.linear_speed = 0
        self.angular_velocity = 0
        logging.info('Robot stopped.')

    def drive(self, linear_speed, angular_velocity):
        self.linear_speed = linear_speed
        self.angular_velocity = angular_velocity
        self.right.drive(linear_speed + angular_velocity)
        self.left.drive(linear_speed - angular_velocity)

    def cleanup(self):
        logging.info('Clearing GPIO')
        GPIO.cleanup()
