import aioserial
import asyncio
import json
import logging

logging.basicConfig(filename='robot_lib.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

SERIAL_DEVICE = '/dev/ttyUSB0'
BAUD_RATE = 115200

class AsyncCommunications():
    def __init__(self):
        self.ser = aioserial.AioSerial(SERIAL_DEVICE, BAUD_RATE)    # open serial port
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

    async def _get_message(self):
        try:
            raw_message = await self.ser.read_until_async(expected=b'}')
            self.raw_message += raw_message.decode()
        except UnicodeDecodeError:
            pass

        ready, message, remainder_raw = self.proccess_raw_message(
            self.raw_message)

        if ready:
            message_dict = self.proccess_message(message)
            self.raw_message = remainder_raw
            return message_dict
        else:
            return {}
        
    
    async def get_message(self, timeout=0.2):
        try:
            return await asyncio.wait_for(self._get_message(), timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception('Timed out getting message.')
        

import unittest

async def main():
    com = AsyncCommunications()
    message = {}
    while message == {}:
        message = await com.get_message()
    print(message)
    com.cleanup()
class TestAsyncCommunication(unittest.TestCase):

  def test_constructor(self):
    asyncio.run(main())

if __name__ == '__main__':
    unittest.main()