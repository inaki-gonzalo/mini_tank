import serial
import pygame
import time

pygame.init()
clock = pygame.time.Clock()
pygame.joystick.init()
VERTICAL_AXIS_ID=1
HORIZONTAL_AXIS_ID=3
BUTTON_INDEX_X = 0
BUTTON_INDEX_A = 1
BUTTON_INDEX_B = 2
BUTTON_INDEX_y = 3

def get_joystick_axes():
    for event in pygame.event.get(): # User did something.
        continue
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    base_speed = joystick.get_axis(VERTICAL_AXIS_ID)
    rotation = joystick.get_axis(HORIZONTAL_AXIS_ID)
    button_a = joystick.get_button(BUTTON_INDEX_A)
    button_y = joystick.get_button(BUTTON_INDEX_y)
    button_x = joystick.get_button(BUTTON_INDEX_X)
    button_b = joystick.get_button(BUTTON_INDEX_B)
    return  (base_speed, rotation, button_a, button_y, button_x, button_b)

ser = serial.Serial('/dev/ttyUSB0', 115200)  # open serial port
ser.write(b'B\n')     # Bypass an go into raw serial mode.
print(ser.name)         # check which port was really used
button_a_state = 0
button_y_state = 0
button_x_state = 0
button_b_state = 0
while True:

    base_speed, rotation, button_a, button_y, button_x, button_b = get_joystick_axes()
    append_message = ""
    if button_x == 0:
      button_x_state = 0
    if button_x == 1 and button_x_state == 0:
      button_x_state = 1
      append_message += ',"engage":'+str(button_x)
    if button_b == 0:
      button_b_state = 0
    if button_b == 1 and button_b_state == 0:
      button_b_state = 1
      append_message += ',"disengage":'+str(button_b)
    
    if button_a == 0:
      button_a_state = 0
    if button_a == 1 and button_a_state == 0:
      button_a_state = 1
      append_message += ',"save":'+str(button_a)
    if button_y == 0:
      button_y_state = 0
    if button_y == 1 and button_y_state == 0:
      button_y_state = 1
      append_message += ',"erase":'+str(button_a)

    message = '{"a":'+str(base_speed)+',"b":'+str(rotation)+ append_message + '}'
      
    ser.write(message.encode())     # write a string
    time.sleep(0.05)
ser.close()       
