import serial
import time
from evdev import InputDevice, ecodes
import os
import asyncio
import socket

def StartStream(kill = False):
    # > /dev/null 2>&1
    if(kill == True):
        os.system("killall mjpg_streamer > /dev/null 2>&1")
    os.system("mjpg_streamer -i \"input_raspicam.so -x 640 -y 480 -fps 30\" -o output_http.so > /dev/null 2>&1 &")
    
arduinoConnected = False
BLTControllerConnected = False
drivingForward = False
manualMode = True

lastSwitchTime = 0
ser = serial.Serial()
gamepad = None

def connectArduino():
    global arduinoConnected
    global ser
    for i in range(0,4):
        try:
            ser = serial.Serial(f'/dev/ttyUSB{i}', 9600)
            arduinoConnected = True
            print(f"Connected to arduino at USB{i}")
        except:
            pass
    if(arduinoConnected == False):
        print("---No connection to arduino---")
        arduinoConnected = False
        time.sleep(5)

def connectBLTController():
    global BLTControllerConnected
    global gamepad
    try:
        for i in range(0,5):
            gamepad = InputDevice(f'/dev/input/event{i}')    
            if(("8Bitdo SN30 Pro" in str(gamepad)) == True):
                print(f"Connected to controller at event{i}")
                BLTControllerConnected = True
                break
        if(BLTControllerConnected == False):
            print("---No connection to controller---")
    except:
        print("---No connection to controller---")
        BLTControllerConnected = False
        time.sleep(5)

a_Btn = 304
b_Btn = 305
x_Btn = 307
y_Btn = 308

select = 314
start = 315

L_Trigger = 312
R_Trigger = 313

H_Dpad = 16
V_Dpad = 17

h_Angle = 90
v_Angle = 70

def executeServoControl(_servo, _angle):
        if(arduinoConnected == True):
            ser.write(f"Servo\n{_servo}\n{_angle}\n".encode('utf-8'))

def executeMovement(command):
    if(arduinoConnected == True):
        ser.write(f"FineMotor\n{command}\n".encode('utf-8'))

def resetServo():
    global h_Angle
    global v_Angle
    h_Angle = 90
    v_Angle = 70
    executeServoControl(1, v_Angle)
    executeServoControl(0, h_Angle)

def Forward():
    ser.write("Motor\nForward\n".encode('utf-8'))

def Stop():
    ser.write("Motor\nStop\n".encode('utf-8'))

def TurnLeft():
    executeMovement("Right_Go")
    executeMovement("Left_Stop")
    
def TurnRight():
    executeMovement("Right_Stop")
    executeMovement("Left_Go")
    
def aiControl():
    global manualMode
    host = ''
    port = 4000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)
    conn, addr = s.accept()
    print("Robot is now controlled by AI")
    print('Connected to:', addr)
    while (True):
        data = conn.recv(1024)
        data = data.decode('utf-8')
        print(f"From AI: {data}")
        if(data == "Forward"):
            Forward()
            drivingForward = True
        elif(data == "Stop"):
            Stop()
            drivingForward = False
        elif(data == "TurnLeft"):
            TurnLeft()
        elif(data == "TurnRight"):
            TurnRight()
        elif(data == "StopTurning"):
            if(drivingForward  == True):
                Forward()
            else:
                Stop()
        elif(data == "EndAI"):
            s.close()
            manualMode = True
            break

def manualControl():
    global gamepad
    global manualMode
    global drivingForward
    global lastSwitchTime
    global h_Angle
    global v_Angle
    
    a_Btn = 304
    b_Btn = 305
    x_Btn = 307
    y_Btn = 308
    select = 314
    start = 315
    L_Trigger = 312
    R_Trigger = 313
    H_Dpad = 16
    V_Dpad = 17
    
    print("Robot is now controlled manually")
    for event in gamepad.read_loop():
        if(event.type == ecodes.EV_KEY):
            if(event.code == start and event.sec > lastSwitchTime):
                lastSwitchTime = event.sec
                manualMode = False
                break
            if(event.code == R_Trigger):
                if(event.value == 0):
                    if(drivingForward == True):
                        Forward()
                    else:
                        Stop()
                if(event.value == 1):
                    TurnRight()
            if(event.code == L_Trigger):
                if(event.value == 0):
                    if(drivingForward  == True):
                        Forward()
                    else:
                        Stop()
                if(event.value == 1):
                    TurnLeft()
            if(event.code == a_Btn):
                if(event.value == 1):
                    Forward()
                    drivingForward = True
                if(event.value == 0):
                    Stop()
                    drivingForward = False
            if(event.code == b_Btn):
                if(event.value == 1):
                    Stop()
                    drivingForward = False
            if(event.code == x_Btn):
                if(event.value == 1):
                    resetServo()
            if(event.code == y_Btn):
                if(event.value == 1):
                    executeServoControl(0, 90)
                    executeServoControl(1, 140)
                    os.system("./end-robot.sh && shutdown now")
                    
        elif(event.type == ecodes.EV_ABS
             and event.value != 0):
            if(event.code == H_Dpad):
                servo = 0
                if(h_Angle + event.value * 10 <= 180
                   and h_Angle + event.value >= 0 ):
                    h_Angle += event.value * 10
                executeServoControl(servo, h_Angle)
            elif(event.code == V_Dpad):
                servo = 1
                if(v_Angle + event.value * 10 <= 120
                   and v_Angle + event.value >= 0 ):
                    v_Angle += event.value * 10
                executeServoControl(servo, v_Angle)

print("---Booting up Turnip---")
StartStream()
print("---Stream running---")
while(True):
    if(arduinoConnected == False):
        connectArduino()
    elif(BLTControllerConnected == False):
        connectBLTController()
    else: 
        resetServo()
        try:
            if (manualMode == True):
                manualControl()
                print("Manual mode ending...")
            else:
                aiControl()
                print("Ai mode ending...")
        except Exception as e:
            print(e)
            try:
                ser.write("Clean\n".encode('utf-8'))
            except:
                if(arduinoConnected == True):
                    arduinoConnected = False
                    print("Arduino has disconnected")
            try:
                gamepad.active_keys(verbose = True)
            except:
                if(BLTControllerConnected == True):
                    BLTControllerConnected = False
                    print("contoller has disconnected")
            time.sleep(2)
