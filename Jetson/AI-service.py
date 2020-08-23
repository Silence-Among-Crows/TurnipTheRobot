import cv2
import jetson.inference
import jetson.utils
import socket
import numpy as np
import time

net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold = 0.6)

print(cv2.getBuildInformation())
vid = cv2.VideoCapture("http://raspberrypi.local:8085/?action=stream")

#configure socket to send commands through
try:
    ip = socket.gethostbyname("raspberrypi.lan")
except:
    ip = socket.gethostbyname("raspberrypi.local")

while(True):
    try:
        c_port = 4000
        theTuple = (ip, c_port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(theTuple)
        print("Connection succeeded")
        break
    except Exception as e:
        print(e)
        inputResponse = input("Retry? (y/n): ")
        if(inputResponse == "y" 
        or inputResponse == "Y" 
        or inputResponse == "yes" 
        or inputResponse == "Yes"):
            print("Ok, retrying...")
        else:
            s.close
            vid.release()
            exit()

#gather some user values for detection
target = str(input("Enter target object: "))
threshold = 0
lastNetworkRequest = 0
seenLastFrame = False
lastMovement = ""
inputHold = 0.2
framesSinceTarget = 1000
chaseTarget = False

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

# usign height of detection to get center threshold
def CentreObject(detection, width, height, timeTaken):
    global chaseTarget
    global inputHold
    global lastMovement
    global lastNetworkRequest
    recordLastRequest = True
    inputHold = 0.3
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
    
    #check to see if last movement was too quick, then send movements over scoket to pi
    if(time.time() - lastNetworkRequest > timeTaken + 1.5):
        if (x < xBoundMin):
            s.send(f"{moveType}Left".encode('utf-8'))
            time.sleep(inputHold)
            s.send("StopTurning".encode('utf-8'))
            lastMovement = f"{moveType}Left"
            
        elif (x > xBoundMax):
            s.send(f"{moveType}Right".encode('utf-8'))
            time.sleep(inputHold)
            s.send("StopTurning".encode('utf-8'))
            lastMovement = f"{moveType}Right"
        
        elif (y < yBoundMin):
            s.send("LookUp".encode('utf-8'))
            lastMovement = "LookUp"
            
        elif (y > yBoundMax):
            s.send("LookDown".encode('utf-8'))
            lastMovement = "LookDown"
        else:
            recordLastRequest = False
        if(recordLastRequest == True):
            lastNetworkRequest = time.time()

#undo over compensation
def undoMovement():
    global lastMovement
    global inputHold
    global seenLastFrame
    if(lastMovement == "TurnLeft"):
        s.send("TurnRight".encode('utf-8'))
        time.sleep(inputHold * 2)
        s.send("StopTurning".encode('utf-8'))
    elif(lastMovement == "TurnRight"):
        s.send("TurnLeft".encode('utf-8'))
        time.sleep(inputHold * 2)
        s.send("StopTurning".encode('utf-8'))
    elif(lastMovement == "LookUp"):
        s.send("LookDown".encode('utf-8'))
    elif(lastMovement == "LookDown"):
        s.send("LookUp".encode('utf-8'))
    seenLastFrame = False

while True:
    startTime = time.time()
    (grabbed, frame) = vid.read()
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
        if(framesSinceTarget > 30):
            s.send("playSound".encode('utf-8'))
            time.sleep(0.2)
            if(target == "person"):
                s.send("oh-a-person".encode('utf-8'))
            else:
                s.send("oh-its-you".encode('utf-8'))
            print(framesSinceTarget)
        framesSinceTarget = 0
        seenLastFrame = True
    elif(targetCount > 1):
        print(f"{targetCount}?? Can only follow one {target} at a time!")
    else:
        if(framesSinceTarget + 1 <= 1000):
            framesSinceTarget += 1
        if(seenLastFrame):
            undoMovement()
            
    
    # COnvert cuda image back to output image, and overlay fps, then display.
    numpyImg = jetson.utils.cudaToNumpy(input_image, width, height, 4)
    output_image = numpyImg.astype(np.uint8)
    fps = round(1000.0 / net.GetNetworkTime(), 1)
    output_image = cv2.putText(output_image, f"Turnip Cam | FPS: {fps}", (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, [150, 150, 50], 2)
    print(f"\nfps: {fps}")
    #print(f"Last movement: {lastMovement}")
    cv2.imshow('Turnip', output_image)
    print("-----------------")
    
    #if q is pressed, will stop AI mode on robot and end this program
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        s.send("EndAI".encode('utf-8'))
        break

#clean up
s.close()   
vid.release()
cv2.destroyAllWindows()
