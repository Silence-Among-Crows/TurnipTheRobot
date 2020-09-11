import serial
import time
from evdev import InputDevice, ecodes

ControllerConnected = False
gamepad = None

# Connect to bluetooth controller
def connect():
    global ControllerConnected
    global gamepad
    ControllerConnected = False
    try:
        gamepad = InputDevice(f'/dev/input/event5')
        print(str(gamepad))
        ControllerConnected = True
    except Exception as e:
        print(e)
        ControllerConnected = False
        time.sleep(5)
        
while (ControllerConnected == False):
        connect()
        if(ControllerConnected == False):
            print("---No connection to controller---")
            time.sleep(5)
        else:
            print("connected")
            break
