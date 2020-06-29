import asyncio
import json
import logging

import aioserial


SERIAL_DEVICE = '/dev/ttyUSB0'
BAUD_RATE = 115200
BYPASS_COMMAND = b'B\n'


class MessageParser():
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


class Communications():
    def __init__(self, serial_device=SERIAL_DEVICE, baud=BAUD_RATE):
        self.ser = aioserial.AioSerial(
            serial_device, baud)    # open serial port
        logging.info('Attached to serial port: {}'.format(self.ser.name))
        # Bypass an go into raw serial mode.
        self.ser.write(BYPASS_COMMAND)
        logging.info('Entered Bypass mode')
        self.raw_message = ''
        self.parser = MessageParser()

    def cleanup(self):
        logging.info('Closing serial device.')
        self.ser.close()

    async def _get_message(self):
        try:
            raw_message = await self.ser.read_until_async(expected=b'}')
            self.raw_message += raw_message.decode()
        except UnicodeDecodeError:
            pass

        ready, message, remainder_raw = self.parser.proccess_raw_message(
            self.raw_message)

        if ready:
            message_dict = self.parser.proccess_message(message)
            self.raw_message = remainder_raw
            return message_dict
        else:
            return {}

    async def get_message(self, timeout=0.2):
        try:
            return await asyncio.wait_for(self._get_message(), timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception('Timed out getting message.')
