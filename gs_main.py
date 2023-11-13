import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import threading

# Initialize MediaPipe solutions for hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils


def gesture_recognized(hand_landmarks):
    # Assuming the hand_landmarks is a single hand's landmarks

    # Thumb tip
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

    # Index finger tip
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

    # Middle finger tip
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

    # Ring finger tip
    ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]

    # Pinky tip
    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]

    # Index finger MCP (Middle joint)
    index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]

    # Check if index finger is up and other fingers are down
    is_index_up = index_tip.y < index_mcp.y
    are_other_fingers_down = (
        middle_tip.y > index_mcp.y and
        ring_tip.y > index_mcp.y and
        pinky_tip.y > index_mcp.y and
        thumb_tip.x > index_tip.x  # Assuming a right hand, adjust accordingly
    )

    return is_index_up and are_other_fingers_down


def perform_action():
    # [Your action performing logic here...]
    pass


class GestureLinkApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        self.video_source = 0  # default webcam

        self.vid = cv2.VideoCapture(self.video_source)
        self.canvas = tk.Canvas(window, width=self.vid.get(cv2.CAP_PROP_FRAME_WIDTH), height=self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.canvas.pack()

        self.btn_text = tk.StringVar()
        self.btn_text.set("Start Webcam")
        self.btn_toggle_webcam = tk.Button(window, textvariable=self.btn_text, width=50, command=self.toggle_webcam)
        self.btn_toggle_webcam.pack(anchor=tk.CENTER, expand=True)

        self.running = False
        self.update()

        self.window.mainloop()

    def toggle_webcam(self):
        if self.running:
            self.running = False
            self.btn_text.set("Start Webcam")
        else:
            self.running = True
            self.btn_text.set("Stop Webcam")

    def update(self):
        if self.running:
            ret, frame = self.vid.read()
            if ret:
                self.process_frame(frame)

        self.window.after(10, self.update)

    def process_frame(self, frame):
        # Flip and convert the image to RGB for MediaPipe processing
        frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        results = hands.process(frame)

        # Draw hand landmarks and check for gestures
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                if gesture_recognized(hand_landmarks):
                    perform_action()
                    cv2.putText(frame, 'Gesture Recognized!', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # Convert frame to PhotoImage
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)


if __name__ == "__main__":
    root = tk.Tk()
    app = GestureLinkApp(root, "Gesture Link App")
