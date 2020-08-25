from imutils.video import VideoStream
import imagezmq
import argparse
import socket
import time
import os
serverIP = "x-jetson"
os.system("sudo fuser -k 5555/tcp")
sender = imagezmq.ImageSender(connect_to=f"tcp://{serverIP}:5555")
rpiName = socket.gethostname()
vs = VideoStream(usePiCamera=True, resolution=(640, 480)).start()
time.sleep(2.0)
 
while True:
	frame = vs.read()
	sender.send_image(rpiName, frame)
