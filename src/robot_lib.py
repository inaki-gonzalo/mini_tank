import RPi.GPIO as GPIO
import json
import logging

import pygame
import pygame.camera
import serial
import time

logging.basicConfig(filename='robot_lib.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s')


CAMERA_DEVICE = "/dev/video0"
CAMERA_RESOLUTION = (240, 320)

SERIAL_DEVICE = '/dev/ttyUSB0'
BAUD_RATE = 115200

pin_left_a = 31
pin_left_b = 33
pin_right_a = 37
pin_right_b = 35
PWM_FREQ = 70  # Hz
MIN_PWM = 12

motor_offset = 0

logging.info('----------------------')
logging.info('Start of log')
logging.info('----------------------')


class Motor(object):
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
            #
            # self.stop()
            #logging.warning('Motor:Invalid direction')

    def pwm(self, channel, unsafe_pwm):
        if unsafe_pwm > 100:
            safe_pwm = 100
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


class Communications():
    def __init__(self):
        self.ser = serial.Serial(
            SERIAL_DEVICE, BAUD_RATE)    # open serial port
        logging.info('Attached to serial port: {}'.format(self.ser.name))
        self.ser.write(b'B\n')         # Bypass an go into raw serial mode.
        logging.info('Entered Bypass mode')
        self.raw_message = ''

    def cleanup(self):
        logging.info('Closing serial device.')
        self.ser.close()

    def proccess_message(self, message):
        try:
            message_dict = json.loads(message)
        except ValueError:
            return {}
        return message_dict

    def proccess_raw_message(self, raw_message):
        message = ''
        remainder_raw = ''
        index = 0
        started = False
        start_index = None
        message_complete = False
        for char in raw_message:
            if not started and char == '{':
                started = True
                start_index = index
            if started and char == '}':
                message_complete = True
                end_index = index
                break
            index += 1
        if message_complete:
            message = raw_message[start_index:end_index + 1]
            remainder_raw = raw_message[end_index + 1:]
        return message_complete, message, remainder_raw

    def get_message(self, timeout=0.2):
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise Exception('Timed out getting message.')
            if self.ser.in_waiting > 0:
                count = self.ser.in_waiting
                try:
                    self.raw_message += self.ser.read(count).decode()
                except UnicodeDecodeError:
                    pass

                ready, message, remainder_raw = self.proccess_raw_message(
                    self.raw_message)

                if ready:
                    message_dict = self.proccess_message(message)
                    self.raw_message = remainder_raw
                    return message_dict
                



# class Camera(object):
#     def __init__(self):
#         message = 'Initializing camera, camera_device={}, resolution={}'
#         logging.info(message.format(CAMERA_DEVICE, CAMERA_RESOLUTION))
#         pygame.camera.init()
#         self.camera = pygame.camera.Camera(CAMERA_DEVICE, CAMERA_RESOLUTION)
#         self.camera.start()
# 
#     def get_image(self):
#         img = self.camera.get_image()
#         img = pygame.surfarray.array3d(img)
#         return img

import camera_lib

class Robot(object):
    def __init__(self):
        logging.info('Initializing robot')
        GPIO.setmode(GPIO.BOARD)
        self.left = Motor('left', pin_left_a, pin_left_b)
        self.right = Motor('right', pin_right_a, pin_right_b)
        self.camera = camera_lib.Camera()
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
