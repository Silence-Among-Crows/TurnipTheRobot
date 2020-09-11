import serial
import time
from evdev import InputDevice, ecodes
import os
import socket
import pathlib
import cv2
import jetson.inference
import jetson.utils
import imagezmq
import argparse
import numpy as np

net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold = 0.6)

imageHub = imagezmq.ImageHub()

#configure socket to send commands through
ip = socket.gethostbyname("raspberrypi.local")

# Getting directory of audio files
root_dir = pathlib.Path(__file__).parent.absolute()
print(root_dir)
audio_path = os.path.join(root_dir, "Audio")
print(audio_path)

# global variables
jetsonHostName = "x-jetson"
arduinoConnected = False
BLTControllerConnected = False
drivingForward = False
manualMode = False
lastSwitchTime = 0
ser = serial.Serial()
gamepad = None
bootComplete = False
servoStep = 5
threshold = 0
inputHold = 0.2
framesSinceTarget = 1000
chaseTarget = False
target = ""

# function to play sounds
def playAudio(wavFileName, longAudio = False):
    try:
        extraDuration = 2
        filePath = os.path.join(audio_path, f"{wavFileName}.wav")
        os.system(f'omxplayer -o local {filePath} > /dev/null 2>&1 &')
        if(longAudio == True):
            time.sleep(extraDuration)
        time.sleep(2)
    except Exception as e:
        print("Audio playback failed")
        print(e)

# function to connect ot arduino slave through se  rial
def connectArduino():
    global arduinoConnected
    global ser
    for i in range(0,11):
        try:
            ser = serial.Serial(f'/dev/ttyUSB{i}', 9600)
            arduinoConnected = True
            print(f"Connected to arduino at USB{i}")
            playAudio("arduino-connected")
            break
        except:
            print(f'/dev/ttyUSB{i} failed')
            pass
    if(arduinoConnected == False):
        print("---No connection to arduino---")
        arduinoConnected = False
        time.sleep(5)

# Connect to bluetooth controller
def connectBLTController():
    global BLTControllerConnected
    global gamepad
    BLTControllerConnected = False
    try:
        for i in range(0,6):
            try:
                gamepad = InputDevice(f'/dev/input/event{i}')    
                if(("8Bitdo SN30 Pro" in str(gamepad)) == True):
                    print(f"Connected to controller at event{i}")
                    playAudio("controller-connected")
                    BLTControllerConnected = True
                    break
            except Exception as e:
                # print(e)
                continue
        if(BLTControllerConnected == False):
            print("---No connection to controller---")
            time.sleep(5)
    except:
        BLTControllerConnected = False
        time.sleep(5)

# my controller's button bindings, you should rebind them to yours, 
# or get an 8bitdo sn30 pro and use it in start+B mode
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

# manual servo movement
def executeServoControl(_servo, _angle):
        if(arduinoConnected == True):
            ser.write(f"Servo\n{_servo}\n{_angle}\n".encode('utf-8'))

# manual motor movement
def executeMovement(command):
    if(arduinoConnected == True):
        ser.write(f"FineMotor\n{command}\n".encode('utf-8'))

# reset servos to look straight ahead
def resetServo():
    global h_Angle
    global v_Angle
    h_Angle = 90
    v_Angle = 70
    executeServoControl(1, v_Angle)
    time.sleep(0.1)
    executeServoControl(0, h_Angle)
    time.sleep(0.1)

# turn off hdmi (only neccesary if power is low)if()
def KillHDMI():
    os.system("sudo /opt/vc/bin/tvservice -p > /dev/null 2>&1")
    os.system("sudo /opt/vc/bin/tvservice -o > /dev/null 2>&1")
    ser.write("Motor\nLightOFF\n".encode('utf-8'))
    print("HDMI is now OFF")

#the following functions are to look around and drive around
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

def LookLeft():
    global h_Angle
    global v_Angle
    servo = 0
    angle = h_Angle - servoStep
    if(angle <= 180 and angle >= 0 ):
        h_Angle = angle
    executeServoControl(servo, h_Angle)
    
def LookRight():
    global h_Angle
    global v_Angle
    servo = 0
    angle = h_Angle + servoStep
    if(angle <= 180 and angle >= 0 ):
        h_Angle = angle
    executeServoControl(servo, h_Angle)
    
def LookUp():
    global h_Angle
    global v_Angle
    servo = 1
    angle = v_Angle - servoStep
    if(angle <= 120 and angle >= 40 ):
        v_Angle = angle
    executeServoControl(servo, v_Angle)
    
def LookDown():
    global h_Angle
    global v_Angle
    servo = 1
    angle = v_Angle + servoStep
    if(angle <= 120 and angle >= 40 ):
        v_Angle = angle
    executeServoControl(servo, v_Angle)

# this makes sure we dont try some impossible servo movement
def SetAngle(servo, angle):
    global h_Angle
    global v_Angle
    if (servo == 0):
        if(angle <= 180 and angle >= 0 ):
            h_Angle = angle
            executeServoControl(servo, angle)
        elif(angle > 180):
            h_Angle = 180
            executeServoControl(servo, 180)
        elif(angle < 0):
            h_Angle = 0
            executeServoControl(servo, 0)
    if (servo == 1):
        v_Angle = angle
        if(angle <= 120 and angle >= 0 ):
            v_Angle = angle
            executeServoControl(servo, angle)
        elif(angle > 120):
            v_Angle = 120
            executeServoControl(servo, 120)
        elif(angle < 0):
            v_Angle = 0
            executeServoControl(servo, 0)

# usign height of detection to get center threshold
def CentreObject(detection, width, height, timeTaken):
    global chaseTarget
    global inputHold
    inputHold = 0.2
    xBoundMin = 0
    yBoundMin = 0
    xBoundMax = 0
    yBoundMax = 0
    moveType = "Look"
    
    if(chaseTarget == True):
        moveType = "Turn"
    
    x, y = detection.Center
    print(f"Target: ({round(x,1)}, {round(y,1)})")
    median = (x + y)/2
    # if object xy median is less than half the frame's height use it as center box
    # otherwise use the frame's height / 2 as center box
    if (median < height / 2):
        xBoundMin = (width / 2) - (median / 2)
        yBoundMin = (height / 2) - (median / 3)
        xBoundMax = (width / 2) + (median / 2)
        yBoundMax = (height / 2) + (median / 3)
    else:
        xBoundMin = (width / 2) - (height / 4)
        yBoundMin = (height / 2) - (height / 6)
        xBoundMax = (width / 2) + (height / 4)
        yBoundMax = (height / 2) + (height / 6)
    
    if(chaseTarget == True):
        if(detection.Height < height / 2 or detection.Width < width / 3):
            Forward()
        else:
            Stop()
    if (x < xBoundMin):
        if(moveType == "Look"):
            LookLeft()
        else:
            TurnLeft()
        time.sleep(inputHold)
        if(drivingForward  == True):
            Forward()
        else:
            Stop()
    elif (x > xBoundMax):
        if(moveType == "Look"):
            LookRight()
        else:
            TurnRight()
        time.sleep(inputHold)
        if(drivingForward  == True):
            Forward()
        else:
            Stop()
        
    time.sleep(0.1)
        
    if (y < yBoundMin or (detection.Top == 0 and detection.Bottom <= height and y < yBoundMax)):
        LookUp()
    elif (y > yBoundMax or (detection.Bottom >= height and detection.Top > 0 and y > yBoundMin)):
        LookDown()

# connects to jetson and handles incomming commands over socket
def aiControl():
    global manualMode
    global drivingForward
    global target
    global chaseTarget
    global threshold
    global inputHold
    global framesSinceTarget

    print("AI mode starting...")
    playAudio("ai-mode")
    target = str(input("Enter target object: "))

    inputResponse = input(f"Chase {target}? (y/n): ")
    if(inputResponse == "y" 
    or inputResponse == "Y" 
    or inputResponse == "yes" 
    or inputResponse == "Yes"):
        print("Ok, Turnip will chase target")
        chaseTarget = True
    else:
        print("Turnip will follow target with head")

    while(True):
        try:
            threshold = float(input("Enter target threshold (__%): "))
            if(threshold > 0 and threshold <= 100):
                threshold = threshold / 100
                print(f"threshold set to {threshold} (x100)")
                break
            else:
                print("Input percentage, 1 - 100")
        except:
            print("Invalid number")

    retryCount = 0
    while (True):
        if(manualMode):
            break
        try:
            startTime = time.time()
            (rpiName, frame) = imageHub.recv_image()
            imageHub.send_reply(b'OK')
            # Grabbing frame from video feed, converting to cuda image
            # then fetching collection of detections from image
            width = frame.shape[1]
            height = frame.shape[0]
            #print(f"width: {width}, height: {height}")
            input_image = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA).astype(np.float32)
            input_image = jetson.utils.cudaFromNumpy(input_image)
            detections = net.Detect(input_image, width, height)
            endTime = time.time()
            timeTaken = endTime - startTime
            print("\n--- New Frame ---")
            print(f"Net completed in {round(timeTaken, 1)} seconds")
            # Getting valid detections for tracking, if more than one, do not persue
            targetCount = 0
            savedDetection = None
            for detection in detections:
                #print(detection)
                detectedObject = net.GetClassDesc(detection.ClassID)
                if(detectedObject == target and detection.Confidence >= threshold):
                    targetCount += 1
                    savedDetection = detection
                print(f"{net.GetClassDesc(detection.ClassID)}, {round(detection.Confidence, 3)} ")
            if(targetCount == 1):
                print(f"A single {target}!")
                CentreObject(savedDetection, width, height, timeTaken)
                if(framesSinceTarget > 15):
                    if(target == "person"):
                        playAudio("oh-a-person")
                    else:
                        playAudio("oh-its-you")
                    print(framesSinceTarget)
                framesSinceTarget = 0
            elif(targetCount > 1):
                framesSinceTarget = 0
                Stop()
                drivingForward = False
                print(f"{targetCount}?? Can only follow one {target} at a time!")
            else:
                if(framesSinceTarget + 1 <= 1000):
                    framesSinceTarget += 1
                if(framesSinceTarget >= 20):
                    Stop()
                    drivingForward = False
            
            # COnvert cuda image back to output image, and overlay fps, then display.
            numpyImg = jetson.utils.cudaToNumpy(input_image, width, height, 4)
            output_image = numpyImg.astype(np.uint8)
            fps = round(1000.0 / net.GetNetworkTime(), 1)
            output_image = cv2.putText(output_image, f"Turnip Cam | FPS: {fps}", (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, [150, 150, 50], 2)
            print(f"\nfps: {fps}")
            cv2.imshow('Turnip', output_image)
            print("-----------------")
            
            #if q is pressed, will stop AI mode on robot and end this program
            if cv2.waitKey(1) & 0xFF == ord('q'): 
                manualMode = True
                break
        except Exception as e:
            print(e)
            print("Abandoning AI mode...")
            playAudio("ai-exception", True)
            manualMode = True
            break

    cv2.destroyAllWindows()
    resetServo()


# manual control form controller feedback
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
    home = 306
    L_Trigger = 312
    R_Trigger = 313
    H_Dpad = 16
    V_Dpad = 17
    
    print("Robot is now controlled manually")
    playAudio("manual-mode")
    for event in gamepad.read_loop():
        if(event.type == ecodes.EV_KEY):
            #print(event.codey_Btn
            if(event.code == y_Btn and event.sec > lastSwitchTime):
                lastSwitchTime = event.sec
                manualMode = False
                break
            if(event.code == start and event.value == 1):
                KillHDMI()
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
            if(event.code == home):
                if(event.value == 1):
                    executeServoControl(0, 90)
                    executeServoControl(1, 140)
                    playAudio("shutting-down")
                    quit()
                    
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
                   and v_Angle + event.value >= 40 ):
                    v_Angle += event.value * 10
                executeServoControl(servo, v_Angle)

print("---Booting up Turnip---")
playAudio("turnip-is-alive", True)
# main loop
while(True):
    try:
        if(arduinoConnected == False):
            connectArduino()
        elif(BLTControllerConnected == False):
            connectBLTController()
        elif(bootComplete == False and BLTControllerConnected == True):
            playAudio("boot-complete")
            bootComplete = True
        else: 
            ser.write("Clean\n".encode('utf-8'))
            gamepad.active_keys(verbose = True)
            resetServo()
            if (manualMode == True):
                manualControl()
                print("Manual mode ending...")
                playAudio("exiting-manual-mode")
            else:
                aiControl()
                print("Ai mode ending...")
                playAudio("exiting-ai-mode")
    except Exception as e:
        ignoreException = False
        manualMode = True
        try:
            ser.write("Clean\n".encode('utf-8'))
        except:
            if(arduinoConnected == True):
                arduinoConnected = False
                print("Arduino has disconnected")
                playAudio("arduino-disconnected")
                ignoreException = True
        try:
            gamepad.active_keys(verbose = True)
        except:
            if(BLTControllerConnected == True):
                BLTControllerConnected = False
                print("contoller has disconnected")
                playAudio("controller-disconnected")
                ignoreException = True
        if (ignoreException == False):
            print(e)
            playAudio("exception")
