#!/bin/sh

sudo killall python3
sudo killall mjpg_streamer

sudo python3 /home/pi/Repos/TurnipTheRobot/Pi/robot-control.py
