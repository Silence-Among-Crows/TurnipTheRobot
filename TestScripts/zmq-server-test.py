import numpy as np
import imagezmq
import argparse
import cv2

imageHub = imagezmq.ImageHub()
	
# loop over all the frames
while True:
	(rpiName, frame) = imageHub.recv_image()
	imageHub.send_reply(b'OK')
	cv2.imshow("frame" ,frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break
		
# do a bit of cleanup
cv2.destroyAllWindows()
