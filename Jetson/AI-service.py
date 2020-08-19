import jetson.inference
import jetson.utils
import socket
import numpy as np
import cv2
import time

net = jetson.inference.detectNet("coco-bottle", threshold = 0.6)
vid = cv2.VideoCapture("http://raspberrypi:8080/?action=stream")

#configure socket to send commands through
try:
    ip = socket.gethostbyname("raspberrypi.lan")
except:
    ip = socket.gethostbyname("raspberrypi.local")
try:
    c_port = 4000
    theTuple = (ip, c_port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(theTuple)
except Exception as e:
    print(e)
    s.close
    vid.release()
    exit()

#gather some user values for detection
target = str(input("Enter target object: "))
threshold = 0
lastNetworkRequest = 0
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

while(True):
    try:
        print("Now we need to configure the detection delay")
        if(threshold > 0 and threshold <= 100):
            threshold = threshold / 100
            break
        else:
            print("Input percentage, 1 - 100")
    except:
        print("Invalid number")

# usign height of detection to get center threshold
def CentreObject(detection, width, height, timeTaken):
    global lastNetworkRequest
    recordLastRequest = True
    inputHold = 0.3
    xBoundMin = 0
    yBoundMin = 0
    xBoundMax = 0
    yBoundMax = 0
    x, y = detection.Center
    print(f"Target: ({round(x,1)}, {round(y,1)})")
    
    # if object height is less than half the frame's height use it as center box
    # otherwise use the frame's height / 2 as center box
    if (y < height / 2):
        xBoundMin = (width / 2) - (y / 2)
        yBoundMin = (height / 2) - (y / 2)
        xBoundMax = (width / 2) + (y / 2)
        yBoundMax = (height / 2) + (y / 2)
    else:
        xBoundMin = (width / 2) - (height / 4)
        yBoundMin = (height / 2) - (height / 4)
        xBoundMax = (width / 2) + (height / 4)
        yBoundMax = (height / 2) + (height / 4)
    
    #check to see if last movement was too quick, then send movements over scoket to pi
    if(time.time() - lastNetworkRequest > timeTaken + 0.5):
        if (x < xBoundMin):
            s.send("TurnLeft".encode('utf-8'))
            time.sleep(inputHold)
            s.send("StopTurning".encode('utf-8'))
            
        elif (x > xBoundMax):
            s.send("TurnRight".encode('utf-8'))
            time.sleep(inputHold)
            s.send("StopTurning".encode('utf-8'))
        
        elif (y < yBoundMin):
            s.send("LookDown".encode('utf-8'))
            
        elif (y > yBoundMax):
            s.send("LookUp".encode('utf-8'))
        else:
            recordLastRequest = False
        if(recordLastRequest == True):
            lastNetworkRequest = time.time()
    
while True:
    startTime = time.time()
    print("\n--- New Frame ---")
    (grabbed, frame) = vid.read()
    cv2.imshow('Original', frame)
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
        CentreObject(savedDetection, width, height, timeTaken)
    elif(targetCount > 1):
        print(f"{targetCount}?? Can only follow one {target} at a time!")
    
    # COnvert cuda image back to output image, and overlay fps, then display.
    numpyImg = jetson.utils.cudaToNumpy(input_image, width, height, 4)
    output_image = numpyImg.astype(np.uint8)
    fps = round(1000.0 / net.GetNetworkTime(), 1)
    output_image = cv2.putText(output_image, f"Turnip Cam | FPS: {fps}", (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, [150, 150, 50], 2)
    print(f"\nfps: {fps}")
    cv2.imshow('Detection', output_image)
    print("-----------------")
    
    #if q is pressed, will stop AI mode on robot and end this program
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        s.send("EndAI".encode('utf-8'))
        break

#clean up
s.close()   
vid.release()
cv2.destroyAllWindows()
