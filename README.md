# Turnip the robot

My code for creating turnip, the little robot that could!

## What you need to build turnip:

- A Jetson Nano (or other jetson development board)
- Raspberry Pi (Preferably 3b or newer), with a case
- Mechanoid G15 KS kit
  This may seem like an odd chice... because it is. However
  I was also able to build turnip's body out of this kit.
  It comes with a great set of motors, a battery holder (4x C cells)
  and 4x servos powerful enough to hold up a raspberry pi 3b and camera
- Raspberry Pi Camera and holder (I am using v1.3)
  I used a Raspberry Pi Zero case that had a built in camera holder.
  Case was from Vilros and you can find it on amazon.
- Arduino Uno
- 2x Relays
- Half size bread board
- plenty of jumper leads
- Battery bank (I am using xiaomi power bank 3 10,000mAh)
  This is to power up Pi and Arduino

---

## Setting up your Jetson Nano:

[Follow Nvidias initial setup](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit)

[Then install Jetson Inferance](https://github.com/dusty-nv/jetson-inference/blob/master/docs/building-repo-2.md)

cd into your home folder (`cd ~`) and create a folder called Repos (`mkdir Repos`). Now cd into Repos (`cd Repos`), and clone this repo! (`git clone https://github.com/Silence-Among-Crows/TurnipTheRobot.git`). open TurnipTheRobot and then the jetson folder (`cd TurnipTheRobot/Jetson`). This will be where you run the ai script. I suggest setting up remote sharing ([credit to this form thread](https://forums.developer.nvidia.com/t/jetson-nano-vnc-headless-connections/77399)) for your jetson so you may connect remotely and launch this script from a laptop or seperate computer:

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

Follow this initial Raspberry Pi setup, being sure to use the `Raspberry Pi OS (32-bit) with desktop` download, NOT the one with reccommended software. It's unnesesary clutter.

cd into your home folder (`cd ~`) and create a folder called Repos (`mkdir Repos`). Now cd into Repos (`cd Repos`), and clone this repo! (`git clone https://github.com/Silence-Among-Crows/TurnipTheRobot.git`). open TurnipTheRobot and then the pi folder (`cd TurnipTheRobot/Pi`). This will be where you run the robot script.

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

this will take a while, especially the installation of opencv.
If you ever encounter issues of missing modules, look up the entire exception, I am pretty sure everything you need is included here but you never know.

Alright we need to install the rpi camera (v1.3 or v2). slide in the camera ribbon cable into the pi with the blue side facing the black plastic. now we need to enable the camera, go into the config: `sudo raspi-config`, open interfacing options and enable the following:

- camra
- ssh
- vnc

---