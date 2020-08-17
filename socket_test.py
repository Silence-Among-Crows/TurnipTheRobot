import socket

def client():

  try:
    ip = socket.gethostbyname("raspberrypi.lan")
  except:
    ip = socket.gethostbyname("raspberrypi.local")
  c_port = 4000  # Make sure it's within the > 1024 $$ <65535 range

  theTuple = (ip, c_port)

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect(theTuple)
  
  while(True):
    message = input('-> ')
    s.send(message.encode('utf-8'))
    if(message == "EndAI"):
      break
  s.close()

client()
exit()