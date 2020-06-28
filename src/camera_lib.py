import logging
import json
import pygame
import pygame.camera

import asyncio
import aiohttp

import cv2

import ast

# initialize the camera




CAMERA_DEVICE = "/dev/video0"
CAMERA_RESOLUTION = (180, 320)

logging.basicConfig(filename='robot_lib.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

class Camera(object):
    def __init__(self):
        message = 'Initializing camera, camera_device={}, resolution={}'
        logging.info(message.format(CAMERA_DEVICE, CAMERA_RESOLUTION))
        #pygame.camera.init()
        
#         self.camera = pygame.camera.Camera(CAMERA_DEVICE, CAMERA_RESOLUTION)
#         self.camera.start()
        self.camera = cv2.VideoCapture(0)   # 0 -> index of camera
        #self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 360)
        #self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)

    async def get_image(self):
        #img = self.camera.get_image()
        #img = pygame.surfarray.array3d(img)
        done = False
        while not done:
            done, frame = self.camera.read()
            if done:
                img = cv2.resize(frame, CAMERA_RESOLUTION, interpolation =cv2.INTER_AREA)
                return img
            else:
                await asyncio.sleep(0)

import unittest

async def autopilot(camera):
    while True:
        raw_image = await camera.get_image()
        image = raw_image.tobytes()
        url = 'http://127.0.0.1:5000/'
        headers = {'Content-Type': 'application/octet-stream',
                   'dtype':str(raw_image.dtype),
                   'shape':str(raw_image.shape)}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=image, headers=headers) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    speed , turning_rate = ast.literal_eval(text)[0]
                    
                    print('Speed={},turning_rate={}'.format(speed,turning_rate))
        await asyncio.sleep(0.1)

async def main():
    cam = Camera()
    await autopilot(cam)

class TestAsyncCommunication(unittest.TestCase):

  def test_constructor(self):
    asyncio.run(main())

if __name__ == '__main__':
    unittest.main()