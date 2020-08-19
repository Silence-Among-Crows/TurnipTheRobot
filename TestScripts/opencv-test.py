import cv2

cap = cv2.VideoCapture("http://raspberrypi:8080/?action=stream")
 
while(True):
    ret, frame = cap.read()
    gray = cv2.putText(frame, "rpi", (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255, 2)
 
    cv2.imshow('frame',gray)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
