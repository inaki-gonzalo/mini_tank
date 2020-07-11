import asyncio
import logging
import robot_lib


logging.basicConfig(filename='robot_lib.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

logging.info('----------------------')
logging.info('Start of log')
logging.info('----------------------')

robot = robot_lib.Robot()


async def collect_data():
    while True:
        if not robot.autopilot_engaged:
            await robot.collect_data()
        await asyncio.sleep(0.2)


async def autopilot():
    while True:
        if not robot.autopilot_engaged:
            await asyncio.sleep(0.5)
            continue
        robot.autopilot()
        await asyncio.sleep(0.1)


async def get_messages():
    robot.init_communications()
    while True:
        await robot.process_events()


async def main(loop):
    t1 = loop.create_task(get_messages())
    t2 = loop.create_task(collect_data())
    t3 = loop.create_task(autopilot())
    await t1

try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
except:
    robot.cleanup()
    loop.close()
    raise

robot.cleanup()

