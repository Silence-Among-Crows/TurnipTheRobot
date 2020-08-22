#gst-launch-1.0 -v tcpclientsrc host=192.168.1.73 port=5000 ! gdpdepay ! rtph264depay ! omxh264dec ! videoconvert ! autovideosink sync=false
