import asyncio
import unittest
import sys
from unittest.mock import Mock, patch, MagicMock
import numpy as np

sys.modules['RPi'] = Mock()
sys.modules['RPi.GPIO'] = Mock()
import robot_lib


class TestCamera(unittest.TestCase):

    @patch('robot_lib.cv2.VideoCapture')
    def setUp(self, mock_class=Mock()):
        self.camera = robot_lib.Camera()

    def tearDown(self):
        del self.camera

    def test_camera(self):
        image_shape = (*robot_lib.CAMERA_RESOLUTION[::-1], 3)
        image = np.zeros(image_shape)
        self.camera.camera.read = Mock(return_value = (True, image))
        image = asyncio.run(self.camera.get_image())
        self.assertEqual(image.shape, image_shape)
    
    def test_no_image_available(self):
        self.camera.camera.read = Mock(return_value = (False, []))
        get_image_coro = asyncio.wait_for(self.camera.get_image(), timeout=0.01)
        with self.assertRaises(asyncio.exceptions.TimeoutError):
            asyncio.run(get_image_coro)


class TestRobot(unittest.TestCase):
    @patch('robot_lib.cv2.VideoCapture')
    def setUp(self, mock_class=Mock()):
        self.robot = robot_lib.Robot()

    def tearDown(self):
        del self.robot

    def test_robot_camera(self):
        self.robot.drive(0, 0)
        self.robot.stop()
        self.robot.cleanup()
        image_shape = (*robot_lib.CAMERA_RESOLUTION[::-1], 3)
        image = np.zeros(image_shape)
        self.robot.camera.camera.read = Mock(return_value=(True, image))
        image = asyncio.run(self.robot.get_image())
        self.assertEqual(image.shape, image_shape)


class TestMotor(unittest.TestCase):
    def setUp(self):
        self.motor = robot_lib.Motor('test_motor', 1, 2)
        self.motor.A = Mock()
        self.motor.B = Mock()

    def tearDown(self):
        del self.motor

    def test_motor_stopped(self):
        self.motor.A.start = MagicMock()
        self.motor.B.start = MagicMock()
        self.motor.drive(0)
        self.motor.A.start.assert_called_with(0)
        self.motor.B.start.assert_called_with(0)

    def test_motor_max_speed(self):
        self.motor.A.start = MagicMock()
        self.motor.B.start = MagicMock()
        max_speed = robot_lib.MAX_PWM
        self.motor.drive(max_speed)
        self.motor.A.start.assert_called_once_with(max_speed)
        self.motor.B.start.assert_called_once_with(0)

    def test_motor_over_max_speed(self):
        self.motor.A.start = MagicMock()
        self.motor.B.start = MagicMock()
        max_speed = robot_lib.MAX_PWM
        self.motor.drive(max_speed + 1)
        self.motor.A.start.assert_called_once_with(max_speed)
        self.motor.B.start.assert_called_once_with(0)

    def test_motor_max_reverse(self):
        self.motor.A.start = MagicMock()
        self.motor.B.start = MagicMock()
        max_speed = robot_lib.MAX_PWM
        self.motor.drive(-max_speed)
        self.motor.A.start.assert_called_once_with(0)
        self.motor.B.start.assert_called_once_with(max_speed)

    def test_motor_over_max_reverse(self):
        self.motor.A.start = MagicMock()
        self.motor.B.start = MagicMock()
        max_speed = robot_lib.MAX_PWM
        self.motor.drive(-max_speed - 1)
        self.motor.A.start.assert_called_once_with(0)
        self.motor.B.start.assert_called_once_with(max_speed)

    def test_motor_under_max_speed(self):
        self.motor.A.start = MagicMock()
        self.motor.B.start = MagicMock()
        speed = robot_lib.MAX_PWM - 1
        self.motor.drive(speed)
        self.motor.A.start.assert_called_once_with(speed)
        self.motor.B.start.assert_called_once_with(0)

    def test_motor_under_max_reverse(self):
        self.motor.A.start = MagicMock()
        self.motor.B.start = MagicMock()
        speed = robot_lib.MAX_PWM - 1
        self.motor.drive(-speed)
        self.motor.A.start.assert_called_once_with(0)
        self.motor.B.start.assert_called_once_with(speed)

    def test_motor_under_min_speed(self):
        self.motor.A.start = MagicMock()
        self.motor.B.start = MagicMock()
        speed = robot_lib.MIN_PWM - 1
        self.motor.drive(speed)
        self.motor.A.start.assert_called_once_with(0)
        self.motor.B.start.assert_called_once_with(0)

    def test_motor_under_min_speed_reverse(self):
        self.motor.A.start = MagicMock()
        self.motor.B.start = MagicMock()
        speed = -robot_lib.MIN_PWM + 1
        self.motor.drive(speed)
        self.motor.A.start.assert_called_once_with(0)
        self.motor.B.start.assert_called_once_with(0)
