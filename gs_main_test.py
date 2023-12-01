import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import ttk
import time
import pyautogui
from PIL import Image, ImageTk

# Initialize MediaPipe solutions for hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# Global variables for action timing
last_action_time = 0
action_interval = 1
options = ["volumemute", "show_desktop", "maximize_windows", "volumeup_1", "volumeup_2", "alt_tab"]
# Gesture to action mapping
gesture_action_map = {
    "closed_fist": "volumemute",
    "index_pinky_up": "show_desktop",
    "index_pinky_thumb_up": "maximize_windows",
    "L_shape": "volumeup_1",
    "middle_ring_up": "volumeup_2",
    "index_middle_up": "alt_tab"
}


def gesture_recognized(hand_landmarks):
    # Existing landmark definitions
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
    index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]

    # Gestures detection logic
    if thumb_tip.x < index_tip.x and thumb_tip.y < index_tip.y:  # L shape
        return "L_shape"
    elif all(tip.y > index_mcp.y for tip in [index_tip, middle_tip, ring_tip, pinky_tip]):  # Closed fist
        return "closed_fist"
    elif index_tip.y < index_mcp.y and pinky_tip.y < ring_tip.y:  # Index and pinky up
        return "index_pinky_up"
    elif middle_tip.y < index_mcp.y and ring_tip.y < index_mcp.y:  # Middle and ring finger up
        return "middle_ring_up"
    elif index_tip.y < index_mcp.y and pinky_tip.y < ring_tip.y and thumb_tip.x < index_tip.x:  # Index, pinky, and thumb up
        return "index_pinky_thumb_up"
    elif index_tip.y < index_mcp.y and middle_tip.y < index_mcp.y:  # Index and middle finger up
        return "index_middle_up"

    return None


def perform_action(gesture):
    global last_action_time
    current_time = time.time()

    if current_time - last_action_time >= action_interval:
        action = gesture_action_map.get(gesture)

        if action == "volumemute":
            pyautogui.press('volumemute')
        elif action == "show_desktop":
            pyautogui.hotkey('win', 'd')
        elif action == "maximize_windows":
            pyautogui.hotkey('win', 'shift', 'm')
        elif action == "volumeup_1":
            pyautogui.press('volumeup')
        elif action == "volumeup_2":
            pyautogui.press('volumeup')
            pyautogui.press('volumeup')
        elif action == "alt_tab":
            pyautogui.hotkey('alt', 'tab')

        last_action_time = current_time


class GestureLinkApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Main frame
        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(fill='both', expand=True)

        # Webcam feed section
        self.video_source = 0  # default webcam
        self.vid = cv2.VideoCapture(self.video_source)
        self.canvas = tk.Canvas(self.main_frame, width=self.vid.get(cv2.CAP_PROP_FRAME_WIDTH), height=self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT), bg='grey')
        self.canvas.pack(side=tk.TOP, fill='both', expand=True)
        self.canvas.create_text(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)//2, self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)//2, text="webcam feed", fill="white", font=('Arial', 20))

        # Start/Stop button
        self.btn_toggle_webcam = tk.Button(self.main_frame, text="Start", width=10, command=self.toggle_webcam, bg='green')
        self.btn_toggle_webcam.pack(side=tk.TOP, pady=10)

        # Gesture-action mappings section
        self.create_gestures_ui()

        self.running = False
        self.update()
        self.window.mainloop()

    def create_gestures_ui(self):
        # Frame for the gesture-action mappings
        self.gesture_frame = tk.Frame(self.main_frame, bg='lightgrey')
        self.gesture_frame.pack(side=tk.BOTTOM, fill='both', expand=True)

        self.dropdown_vars = {}

        row = 0
        for gesture, action in gesture_action_map.items():
            # Label for the gesture
            tk.Label(self.gesture_frame, text=gesture, bg='white', width=20, relief='solid').grid(row=row, column=0, padx=5, pady=5, sticky='ew')

            # Arrow label
            arrow_label = tk.Label(self.gesture_frame, text='→', bg='lightgrey', font=('Arial', 16))
            arrow_label.grid(row=row, column=1, padx=5, pady=5)

            # Drop-down for the action
            variable = tk.StringVar(self.gesture_frame)
            variable.set(action)  # default value
            self.dropdown_vars[gesture] = variable
            dropdown = tk.OptionMenu(self.gesture_frame, variable, *options, command=lambda value, g=gesture: self.update_gesture_action(g, value))
            dropdown.config(width=20, anchor='w')
            dropdown.grid(row=row, column=2, padx=5, pady=5, sticky='ew')

            row += 1

    def update_gesture_action(self, gesture, new_action):
        gesture_action_map[gesture] = new_action

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
                gesture = gesture_recognized(hand_landmarks)
                if gesture:
                    perform_action(gesture)
                    cv2.putText(frame, f'Gesture Recognized: {gesture}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 255, 0), 2, cv2.LINE_AA)

        # Convert frame to PhotoImage
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)


if __name__ == "__main__":
    root = tk.Tk()
    app = GestureLinkApp(root, "Gesture Link App")
