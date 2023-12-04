import cv2
cap = cv2.VideoCapture(1)
if cap.isOpened():
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow('Test Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print("Failed to grab frame")
            break
else:
    print("Failed to open webcam.")

cap.release()
cv2.destroyAllWindows()

while cap.isOpened():
    success, image = cap.read()
    if success:
        cv2.imshow('Gesture Link', image)
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
    else:
        print("Failed to read from webcam.")