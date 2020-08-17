#!/bin/sh

sudo killall python3
sudo killall mjpg_streamer

sudo python3 manual-control.py
