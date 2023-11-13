import cv2
import mediapipe as mp
import tkinter as tk
import time
from tkinter import ttk

import pyautogui
from PIL import Image, ImageTk

# Initialize MediaPipe solutions for hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils
last_volume_up_time = 0


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
    global last_volume_up_time
    current_time = time.time()
    if current_time - last_volume_up_time >= 1:
        pyautogui.press('volumeup')
        last_volume_up_time = current_time


class GestureLinkApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Style configuration for tabs to make them larger and centered
        style = ttk.Style()
        style.configure('Large.TNotebook.Tab', font=('Arial', '12'), padding=[20, 8])

        # Change the color of the text of the selected tab to blue
        style.map('Large.TNotebook.Tab',
                  foreground=[('selected', 'blue')],
                  background=[
                      ('selected', 'grey')])  # Optional: change the background color of the selected tab as well

        # Create a tab control with the new style
        self.tabControl = ttk.Notebook(self.window, style='Large.TNotebook')

        # Create tabs
        self.tabHome = ttk.Frame(self.tabControl)
        self.tabGestures = ttk.Frame(self.tabControl)
        self.tabWebcam = ttk.Frame(self.tabControl)
        self.tabSettings = ttk.Frame(self.tabControl)
        self.tabProfiles = ttk.Frame(self.tabControl)

        # Add tabs to the tab control
        self.tabControl.add(self.tabHome, text='Home')
        self.tabControl.add(self.tabGestures, text='Gestures')
        self.tabControl.add(self.tabWebcam, text='Webcam')
        self.tabControl.add(self.tabSettings, text='Settings')
        self.tabControl.add(self.tabProfiles, text='Profiles')
        self.tabControl.pack(expand=1, fill="both")

        # Webcam feed section
        self.video_source = 0  # default webcam
        self.vid = cv2.VideoCapture(self.video_source)
        self.canvas = tk.Canvas(self.tabWebcam, width=self.vid.get(cv2.CAP_PROP_FRAME_WIDTH), height=self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.canvas.pack()

        # Start/Stop button
        self.btn_toggle_webcam = tk.Button(self.tabWebcam, text="Start", width=10, command=self.toggle_webcam, bg='green')
        self.btn_toggle_webcam.pack(pady=20)

        self.running = False
        self.update()

        self.window.mainloop()

    def toggle_webcam(self):
        if self.running:
            self.running = False
            self.btn_toggle_webcam.config(text="Start", bg='green')
            self.canvas.delete("all")  # Clear the canvas
        else:
            self.running = True
            self.btn_toggle_webcam.config(text="Stop", bg='red')

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
