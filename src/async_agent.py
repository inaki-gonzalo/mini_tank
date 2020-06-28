import ast
import asyncio
import datetime
import json
import logging
import time
import unittest

import aiohttp

import async_communications
import numpy as np
import robot_lib


logging.basicConfig(filename='robot_lib.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s')


x_train = []
y_train = []


def delete_current_data():
    del x_train[:]
    del y_train[:]

# Save training data to disk


def save_trainning_data():
    now = datetime.datetime.now()
    dt_string = now.strftime("_%Y_%m_%d_%H_%M_%S")
    np_x_train = np.array(x_train)
    np.save("x_train_set" + dt_string, np_x_train)
    np_y_train = np.array(y_train)
    np.save("y_train_set" + dt_string, np_y_train)
    delete_current_data()


def cleanup():
    robot.stop()
    robot.cleanup()
    com.cleanup()


start_time = time.time()
robot = robot_lib.Robot()
com = async_communications.AsyncCommunications()


async def collect_data():
    while True:
        if not robot.autopilot_engaged:
            logging.info('Collecting data.')
            image = await robot.get_image()
            arr = np.array(image)
            x_train.append(arr)
            y_train.append([robot.linear_speed/100.0, robot.angular_velocity/60.0])
        await asyncio.sleep(0.2)


async def autopilot():
    camera = robot.camera
    while True:
        if not robot.autopilot_engaged:
            await asyncio.sleep(0.5)
            continue
        logging.info('Autopilot getting image...')
        raw_image = await camera.get_image()
        logging.info('Autopilot got image.')
        image = raw_image.tobytes()
        url = 'http://127.0.0.1:5000/'
        headers = {'Content-Type': 'application/octet-stream',
                   'dtype': str(raw_image.dtype),
                   'shape': str(raw_image.shape)}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=image, headers=headers) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    print(str(text))
                    base_speed, direction = ast.literal_eval(text)[0]
                    base_speed *= 100.0
                    direction *= 60.0
                    log_message = 'Received message, base_speed={}, direction={}'
                    logging.info(log_message.format(base_speed, direction))
                    robot.drive(base_speed, direction)
                else:
                    logging.info('Inference request returned invalid status response.')
        await asyncio.sleep(0.1)


async def get_messages():
    while True:
        try:
            message_dict = await com.get_message()
        except Exception:
            logging.info('Lost connection')
            robot.stop()
            if robot.autopilot_engaged:
                logging.info('Disengaging autopilot.')
                robot.autopilot_engaged = False
            await asyncio.sleep(1)
            continue

        if 'engage' in message_dict:
            logging.info('Engaging autopilot.')
            robot.autopilot_engaged = True
        if 'disengage' in message_dict:
            robot.stop()
            logging.info('Disengaging autopilot.')
            robot.autopilot_engaged = False
        if 'save' in message_dict:
            robot.stop()
            logging.info('Saving data.')
            save_trainning_data()
        if 'erase' in message_dict:
            robot.stop()
            logging.info('Clearing data.')
            delete_current_data()
        if robot.autopilot_engaged:
            continue
        if 'a' in message_dict and 'b' in message_dict:
            raw_a = message_dict['a']
            raw_b = message_dict['b']
            base_speed = raw_a * -100
            direction = raw_b * 60
            log_message = 'Received message, base_speed={}, direction={}'
            logging.info(log_message.format(base_speed, direction))
            robot.drive(base_speed, direction)


async def main(loop):
    t1 = loop.create_task(get_messages())
    t2 = loop.create_task(collect_data())
    t3 = loop.create_task(autopilot())
    await t1

try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
except:
    cleanup()
    loop.close()
    raise

cleanup()


# for message in out_queue:
#  send(message)



class TestStringMethods(unittest.TestCase):

    def test_not_ready(self):
        current_message = ""
        raw_message = ""
        ready, message, remainder_raw = proccess_raw_message(raw_message)
        self.assertFalse(ready)

    def test_not_ready_with_buffer(self):
        current_message = ""
        raw_message = "{"
        ready, message, remainder_raw = proccess_raw_message(raw_message)
        self.assertFalse(ready)

    def test_ready(self):
        current_message = ""
        raw_message = "{hello}"
        ready, message, remainder_raw = proccess_raw_message(raw_message)
        self.assertTrue(ready)
        self.assertEqual(message, raw_message)

    def test_ready_with_buffer(self):
        current_message = ""
        raw_message = "{hello}{"
        ready, message, remainder_raw = proccess_raw_message(raw_message)
        self.assertTrue(ready)
        self.assertEqual(message, '{hello}')
        self.assertEqual(remainder_raw, '{')

    def test_ready_two_messages(self):
        current_message = ""
        raw_message = "{hello}{hello2}"
        ready, message, remainder_raw = proccess_raw_message(raw_message)
        self.assertTrue(ready)
        self.assertEqual(message, '{hello}')
        raw_message = remainder_raw
        ready, message, remainder_raw = proccess_raw_message(raw_message)
        self.assertTrue(ready)
        self.assertEqual(message, '{hello2}')
        self.assertEqual(remainder_raw, '')

    def test_parse_message(self):
        message = '{"a":1.0,"b":2}'
        message_dict = proccess_message(message)
        self.assertEqual(message_dict['a'], 1.0)
        self.assertEqual(message_dict['b'], 2)


# if __name__ == '__main__':
        # unittest.main()
