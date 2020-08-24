from imutils.video import VideoStream
import imagezmq
import argparse
import socket
import time

ap = argparse.ArgumentParser()
ap.add_argument("-s", "--server-ip", required=False, default="x-jetson")
args = vars(ap.parse_args())
sender = imagezmq.ImageSender(connect_to=f"tcp://{args['server_ip']}:5555")
rpiName = socket.gethostname()
vs = VideoStream(usePiCamera=True, resolution=(640, 480)).start()
time.sleep(2.0)
 
while True:
	frame = vs.read()
	sender.send_image(rpiName, frame)
