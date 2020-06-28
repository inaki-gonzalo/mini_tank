import time
import robot_lib
import numpy as np
import logging
import datetime

logging.basicConfig(filename='robot_lib.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s')


x_train = []
y_train = []


def delete_current_data():
    del x_train[:]
    del y_train[:]

#Save training data to disk


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
com = robot_lib.Communications()
autopilot_engaged = False
try:
    while True:
        try:
            message_dict = com.get_message()
        except Exception:
            logging.info('Lost connection')
            robot.stop()
            time.sleep(1)
            continue
        if 'engage' in message_dict:
            logging.info('Engaging autopilot.')
            autopilot_engaged = True
        if 'disengage' in message_dict:
            logging.info('Disengaging autopilot.')
            autopilot_engaged = False
        if 'save' in message_dict:
            robot.stop()
            logging.info('Saving data.')
            save_trainning_data()
        if 'erase' in message_dict:
            robot.stop()
            logging.info('Clearing data.')
            delete_current_data()
        if 'quit' in message_dict:
            break
        if 'a' in message_dict and 'b' in message_dict:
            raw_a = message_dict['a']
            raw_b = message_dict['b']
            base_speed = raw_a * -100
            direction = raw_b * 60
            log_message = 'Received message, base_speed={}, direction={}'
            logging.info(log_message.format(base_speed, direction))
            robot.drive(base_speed, direction)
            if time.time() - start_time > 0.5:
                image = robot.get_image()
                start_time = time.time()
                
                arr = np.array(image)
                x_train.append(arr)
                y_train.append([raw_a, raw_b])
except:
  cleanup()
  raise
  # close port

cleanup()


#for message in out_queue:
#  send(message)

import unittest


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
