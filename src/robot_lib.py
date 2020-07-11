import asyncio
import ast
import logging

from http import HTTPStatus
import aiohttp
import cv2

import RPi.GPIO as GPIO
import communications

pin_left_a = 31
pin_left_b = 33
pin_right_a = 37
pin_right_b = 35
PWM_FREQ = 70  # Hz
MIN_PWM = 12
MAX_PWM = 100

CAMERA_DEVICE = "/dev/video0"
CAMERA_RESOLUTION = (180, 320)

INFERENCE_URL = "http://127.0.0.1"
INFERENCE_PORT = 5000
INFERENCE_SERVER = INFERENCE_URL + ':' + str(INFERENCE_PORT) + '/'

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
        self.com = None
        self.data = Data()
        logging.info('Robot initialized')
    
    def init_communications(self):
        self.com = communications.Communications()

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
    
    async def proccess_events(self):
        try:
            message_dict = await self.com.get_message()
        except Exception:
            logging.info('Lost connection')
            self.stop()
            if self.autopilot_engaged:
                logging.info('Disengaging autopilot.')
                self.autopilot_engaged = False
            await asyncio.sleep(1)
            return

        if 'engage' in message_dict:
            logging.info('Engaging autopilot.')
            self.autopilot_engaged = True
        if 'disengage' in message_dict:
            self.stop()
            logging.info('Disengaging autopilot.')
            self.autopilot_engaged = False
        if 'save' in message_dict:
            self.stop()
            logging.info('Saving data.')
            self.data.save()
        if 'erase' in message_dict:
            self.stop()
            logging.info('Clearing data.')
            self.data.delete()
        if self.autopilot_engaged:
            return
        if 'a' in message_dict and 'b' in message_dict:
            raw_a = message_dict['a']
            raw_b = message_dict['b']
            base_speed = raw_a * -100
            direction = raw_b * 60
            log_message = 'Received message, base_speed={}, direction={}'
            logging.info(log_message.format(base_speed, direction))
            self.drive(base_speed, direction)
    
    async def autopilot(self):
        logging.info('Autopilot getting image...')
        raw_image = await camera.get_image()
        logging.info('Autopilot got image.')
        success, base_speed, direction = await post_request(raw_image)
        if success:
            base_speed *= 100.0
            direction *= 60.0
            log_message = 'Received message, base_speed={}, direction={}'
            logging.info(log_message.format(base_speed, direction))
            robot.drive(base_speed, direction)
    
    async def post_request(self, raw_image, url=INFERENCE_SERVER):
        headers = {'Content-Type': 'application/octet-stream',
                   'dtype': str(raw_image.dtype),
                   'shape': str(raw_image.shape)}
        image = raw_image.tobytes()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=image, headers=headers) as resp:
                if resp.status == HTTPStatus.OK:
                    text = await resp.text()
                    base_speed, direction = ast.literal_eval(text)[0]
                    return True, base_speed, direction
                else:
                    logging.info('Bad response to HTTP POST request.')
        return False, None, None
    
    async def collect_data(self):
        logging.info('Collecting data.')
        image = await self.get_image()
        arr = np.array(image)
        x_train.append(arr)
        y_train.append([robot.linear_speed/100.0, robot.angular_velocity/60.0])
        

    def cleanup(self):
        self.stop()
        logging.info('Clearing GPIO')
        GPIO.cleanup()
        if self.com:
            self.com.cleanup()

class Data():
    def __init__(self):
        self.x_train = []
        self.y_train = []

    def delete(self):
        del self.x_train[:]
        del self.y_train[:]
    
    def save(self):
        now = datetime.datetime.now()
        dt_string = now.strftime("_%Y_%m_%d_%H_%M_%S")
        np_x_train = np.array(self.x_train)
        np.save("x_train_set" + dt_string, np_x_train)
        np_y_train = np.array(self.y_train)
        np.save("y_train_set" + dt_string, np_y_train)
        self.delete()
