import asyncio
import os
import pty
import unittest

import communications

class TestCommunications(unittest.TestCase):
    def setUp(self):
        self.primary, self.secondary = pty.openpty()
        s_name = os.ttyname(self.secondary)
        self.comm = communications.Communications(serial_device=s_name)

    def tearDown(self):
        self.comm.cleanup()
        del self.comm

    def test_bypass_commands_sent(self):
        raw_read = os.read(self.primary, 10)
        self.assertEqual(raw_read, communications.BYPASS_COMMAND)
    
    def test_message_received(self):
        os.write(self.primary, b'{"a":1,"b":2}')
        message = asyncio.run(self.comm.get_message())
        self.assertEqual(message, {"a": 1, "b": 2})
    
    def test_bad_message_received(self):
        os.write(self.primary, b'{:1,"b":2}')
        message = asyncio.run(self.comm.get_message())
        self.assertEqual(message, {})
    
    def test_bad_char_received(self):
        os.write(self.primary, b'{\xff\xff:1,"b":2}')
        message = asyncio.run(self.comm.get_message())
        self.assertEqual(message, {})
    
    def test_timeout(self):
        with self.assertRaises(Exception):
            message = asyncio.run(self.comm.get_message())

class TestMessageParser(unittest.TestCase):
    def setUp(self):
        self.parser = communications.MessageParser()

    def tearDown(self):
        del self.parser     

    def test_not_ready(self):
        current_message = ""
        raw_message = ""
        ready, message, remainder_raw = self.parser.proccess_raw_message(
            raw_message)
        self.assertFalse(ready)

    def test_not_ready_with_buffer(self):
        current_message = ""
        raw_message = "{"
        ready, message, remainder_raw = self.parser.proccess_raw_message(
            raw_message)
        self.assertFalse(ready)

    def test_ready(self):
        current_message = ""
        raw_message = "{hello}"
        ready, message, remainder_raw = self.parser.proccess_raw_message(
            raw_message)
        self.assertTrue(ready)
        self.assertEqual(message, raw_message)

    def test_ready_with_buffer(self):
        current_message = ""
        raw_message = "{hello}{"
        ready, message, remainder_raw = self.parser.proccess_raw_message(
            raw_message)
        self.assertTrue(ready)
        self.assertEqual(message, '{hello}')
        self.assertEqual(remainder_raw, '{')

    def test_ready_two_messages(self):
        current_message = ""
        raw_message = "{hello}{hello2}"
        ready, message, remainder_raw = self.parser.proccess_raw_message(
            raw_message)
        self.assertTrue(ready)
        self.assertEqual(message, '{hello}')
        raw_message = remainder_raw
        ready, message, remainder_raw = self.parser.proccess_raw_message(
            raw_message)
        self.assertTrue(ready)
        self.assertEqual(message, '{hello2}')
        self.assertEqual(remainder_raw, '')

    def test_parse_message(self):
        message = '{"a":1.0,"b":2}'
        message_dict = self.parser.proccess_message(message)
        self.assertEqual(message_dict['a'], 1.0)
        self.assertEqual(message_dict['b'], 2)

