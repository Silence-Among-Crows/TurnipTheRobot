#!/bin/bash
mjpg_streamer -i "input_raspicam.so -x 640 -y 480 -fps 30" -o "output_http.so -p 8085"
