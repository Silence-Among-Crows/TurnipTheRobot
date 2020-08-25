# Turnip the robot

My code for creating turnip, the little robot that could!

Turnip is an open source robot that makes use of the jetson nano to follow an object. I am using ssd-mobilenet-v2 and OpenCV to detect objects and then deciding based on the given data on what to do with it. Theres a manual mode too!

---

## What you need to build turnip:

- A Jetson Nano (or other jetson development board)
- Raspberry Pi (Preferably 3b or newer), with a case
- Mechanoid G15 KS kit
  This may seem like an odd chice... because it is. However I was als able to build turnip's body out of this kit. It comes with a great set of motors, a battery holder (4x C cells) and 4x servos powerful enough to hold up a raspberry pi 3b and camera
- Raspberry Pi Camera and holder
 (I am using v1.3) I used a Raspberry pi Zero case that had a built in camera holder. Case was from Vilros and you can find it on amazon.
- Arduino Uno
- 2x Relays
- Half size bread board
- plenty of jumper leads
- Battery bank (I am using xiaomi power bank 3 10,000mAh)
  This is to power up Pi and Arduino

---

## Setting up your Jetson Nano:

[Follow Nvidias initial setup](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit)

[Then install Jetson Inferance](https://github.com/dusty-nv/jetson-inference/blob/master/docs/building-repo-2.md) Make sure the **ssd-mobile-net-v2** model gets installed

cd into your home folder (`cd ~`) and create a folder called Repos: `mkdir Repos`. Now cd into Repos: `cd Repos`, and clone this repo: `git clone https://github.com/Silence-Among-Crows/TurnipTheRobot.git`. open TurnipTheRobot and then the jetson folder: `cd TurnipTheRobot/Jetson`. This will be where you run the ai script. I suggest setting up remote sharing ([credit to this form thread](https://forums.developer.nvidia.com/t/jetson-nano-vnc-headless-connections/77399)) for your jetson so you may connect remotely and launch this script from a laptop or seperate computer:

``` bash
sudo apt update
sudo apt install vino

export DISPLAY=:0

gsettings set org.gnome.Vino enabled true
gsettings set org.gnome.Vino prompt-enabled false
gsettings set org.gnome.Vino require-encryption false

sudo reboot
```

Now you need to note down your IP address. Get this by looking typing this command in: `ifconfig` and look for `inet x.x.x.x` under wlan0 if you are on wifi, or eth0 if you are on ethernet. the `x.x.x.x` will be your IP address.

---

## Setting up your Raspberry Pi:

Follow this initial Raspberry Pi setup, being sure to use the **Raspberry Pi OS (32-bit) with desktop** download, **NOT** the one with recommended software. It's unnesesary clutter.

cd into your home folder: `cd ~` and create a folder called Repos: `mkdir Repos`. Now cd into Repos (`cd Repos`), and clone this repo: `git clone https://github.com/Silence-Among-Crows/TurnipTheRobot.git`. open TurnipTheRobot and then the pi folder: `cd TurnipTheRobot/Pi`. This will be where you run the robot script.

Alright lets install some dependancies. 

``` bash
sudo apt-get install libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get install libxvidcore-dev libx264-dev
sudo apt-get install libgtk2.0-dev libgtk-3-dev
sudo apt-get install libatlas-base-dev gfortran
sudo apt-get install python2.7-dev python3-dev
pip3 install opencv-python
pip3 install imagezmq
```

this will take a while, especially the installation of opencv. If you ever encounter issues of missing modules, look up the entire exception, I am pretty sure everything you need is included here but you never know.

Alright we need to install the rpi camera (v1.3 or v2). slide in the camera ribbon cable into the pi with the blue side facing the black plastic. now we need to enable the camera, go into the config: `sudo raspi-config`, open interfacing options and enable the following:

- camra
- ssh
- vnc

select finish once they are selected. You can now ssh into your pi too! this makes it a bit easier and quicker to setup the robot. from your jetson, run `ssh raspberrypi.local`, trust it, as it is your raspberry pi. Default password is raspbian. If that all works hooray you're done for now. if this does not work, you can ssh in via the ip. from the pi's terminal run `ipconfig` and look for `inet x.x.x.x` under wlan0 if you are on wifi, or eth0 if you are on ethernet. the `x.x.x.x` will be your IP address. Now try ssh in from your jetson with `ssh x.x.x.x` where `x.x.x.x` is your ip address.

---

## More about Turnip

Turnip has two methods of running. The first method is for where your jetson nano is running remotely. This was how I first made turnip, then I later figured out how I could safely mount power and connect the jetson directly on turnip. I then connected a short lan cable to reduce latency and after finishing method 1, I realized I no longer needed the arduino, since the jetson has a breakout board. I thus also didnt need to run the main python script on the pi anymore, all the pi needs to do now is send video to the jetson. The meccanoid servos have propriatary drivers to run on arduino. So I would then need to write my own python library for it. (I am writing all of this before actually doing method 2, and I am basically documenting as I speak haha). But all in all, method 2 completely removes the need for the arduino (in theory).

**Note to self: update this if method 2 fails haha**

---

## Running turnip

Alright, time to start this puppy up! If you are running your jetson nano remotely, follow **Method 1**, if you have your jetson directly bolted on to the nano, follow **Method 2**

### *Method 1*

Ok, I lied, there is one more thing to setup, your bluetooh controller. I highly reccomend using the 8BitDo SN30 pro, as you will not need to rebind buttons. if you do need to rebind buttons, open the robot-control script and between lines 95 - 112 you will find the binding codes. watch [this video](https://www.youtube.com/watch?v=F5-dV6ULeg8) to connect bluetooth controller from terminal. Alternatively connect through rpi gui.

In the raspberry pi, go into the pi folder in my repo: `cd ~/TurnipTheRobot/Pi` and run the start-stream script: `python3 start-stream.sh &` . The `&` makes it run in the background. Now open up the robot-control script and we are going to replace my jetson host name with your jetson ip address you noted down earlier: `sudo nano robot-control.py` you are looking for `jetsonHostName`, it is on line 15:

``` python
import serial
import time
from evdev import InputDevice, ecodes
import os
import socket
import pathlib

# Getting directory of audio files
root_dir = pathlib.Path(__file__).parent.absolute()
print(root_dir)
audio_path = os.path.join(root_dir, "Audio")
print(audio_path)

# global variables
jetsonHostName = "x-jetson" #replace x-jetson with your ip or hostname
...
```

save with `ctrl+x`, `y`, enter. Now run the script: `sudo python3 robot-control.py`. If you have a speaker connected to the pi via aux jack, you will hear turnip speaking. Otherwise, just observe the terminal update to know it's status.

When robot declares it is in manual mode, you can start using it.

Manual Commands:

- DPad: move "head" of robot
- Right Trigger: Turn right
- Left Trigger: Turn Left
- Start: Disables HDMI port, saving roughly (20 - 40) mA
- Home: Shuts down robot
- A: Forward
- B: Force Stop
- X: Centre "head" of robot
- Y: Enter "AI Mode" (will not accept controller input anymore)

AI usage:

Once in AI mode, run the AI-Service script on your jetson nano, it should handle connecting to the pi for you based on the default hostname. Follow the prompt requests, list of available class labels [here](https://gist.github.com/AruniRC/7b3dadd004da04c80198557db5da4bda). next is whether you want robot to just look at you, or turn and chase you / the specefied object. And finally the confidence percentage, too confident will result in less frames seeing the object, where as if the confidence is too low, the robot may chase some invalid detections. Sweet-spot is generally 65% - 80%. Now a preview will appear with what the robot is seeing. Neat! to quit AI mode, simply type `q` on the preview window. robot will go back to manual mode.

### *Method 2*

Not yet implimented.
