import jetson.inference
import jetson.utils
import numpy as np
import cv2

net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold = 0.4)
vid = cv2.VideoCapture("http://raspberrypi:8080/?action=stream")

while True:
    print("\n--- New Frame ---")
    (grabbed, frame) = vid.read()
    frame = cv2.putText(frame, "Object detection - Xavier Burger", (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, [150, 150, 50], 2)
    width = frame.shape[1]
    height = frame.shape[0]
    print(f"width: ${width}, height: ${height}")
    input_image = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA).astype(np.float32)
    # move the image to CUDA:
    input_image = jetson.utils.cudaFromNumpy(input_image)
    detections = net.Detect(input_image, width, height)
    for detection in detections:
        print(detection)

    net.PrintProfilerTimes()
    numpyImg = jetson.utils.cudaToNumpy(input_image, width, height, 4)
    output_image = numpyImg.astype(np.uint8)
    fps = 1000.0 / net.GetNetworkTime()
    print(f"\nfps: {fps}")
    cv2.imshow('frame', output_image)
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break
    print("-----------------")
vid.release()
cv2.destroyAllWindows()
