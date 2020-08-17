# Turnip the robot
My code for creating turnip, the little robot that could!

### What you need to build turnip:
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

### Setting up your Jetson Nano:
Add the entire Jetson folder on this repo, to your Jetson's home directory.

Follow Nvidias initial setup:
https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit

Then install Jetson Inferance:
https://github.com/dusty-nv/jetson-inference/blob/master/docs/building-repo-2.md
