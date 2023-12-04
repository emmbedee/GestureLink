#DEPRECIATED CODE: ONLY HERE FOR REFERENCE!!
#DEPRECIATED CODE: ONLY HERE FOR REFERENCE!!
#DEPRECIATED CODE: ONLY HERE FOR REFERENCE!!
#DEPRECIATED CODE: ONLY HERE FOR REFERENCE!!



import cv2
import mediapipe as mp
import tkinter as tk
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
options = ["None", "Volume Mute", "Show Desktop", "Maximize Windows", "Volume Up", "Volume Up x2", "Alt+Tab"]
gesture_action_map = {
    "Closed Fist": "None",
    "Index Pinky Up": "None",
    "Index Pinky Thumb Up": "None",
    "L Shape": "None",
    "Middle Ring Up": "None",
    "Index Middle Up": "None"
}

def gesture_recognized(hand_landmarks):
    # Gesture recognition logic here...
    thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip = [hand_landmarks.landmark[i] for i in [mp_hands.HandLandmark.THUMB_TIP, mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.PINKY_TIP]]
    index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]

    if thumb_tip.x < index_tip.x and thumb_tip.y < index_tip.y:
        return "L Shape"
    elif all(tip.y > index_mcp.y for tip in [index_tip, middle_tip, ring_tip, pinky_tip]):
        return "Closed Fist"
    elif index_tip.y < index_mcp.y and pinky_tip.y < ring_tip.y:
        return "Index Pinky Up"
    elif middle_tip.y < index_mcp.y and ring_tip.y < index_mcp.y:
        return "Middle Ring Up"
    elif index_tip.y < index_mcp.y and pinky_tip.y < ring_tip.y and thumb_tip.x < index_tip.x:
        return "Index Pinky Thumb Up"
    elif index_tip.y < index_mcp.y and middle_tip.y < index_mcp.y:
        return "Index Middle Up"

def perform_action(action):
    global last_action_time
    if time.time() - last_action_time >= action_interval:
        if action == "Volume Up":
            pyautogui.press('volumeup')
        elif action == "Volume Up x2":
            pyautogui.press('volumeup')
            pyautogui.press('volumeup')
        elif action == "Volume Mute":
            pyautogui.press('volumemute')
        elif action == "Show Desktop":
            pyautogui.hotkey('win', 'd')
        elif action == "Maximize Windows":
            pyautogui.hotkey('win', 'shift', 'm')
        elif action == "Alt+Tab":
            pyautogui.hotkey('alt', 'tab')
        last_action_time = time.time()

class GestureLinkApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.main_frame = tk.Frame(window)
        self.main_frame.pack(fill='both', expand=True)
        self.window.minsize(800, 800)

        self.video_source = 0
        self.vid = cv2.VideoCapture(self.video_source)
        self.canvas = tk.Canvas(self.main_frame, width=640, height=480, bg='black')  # Changed canvas background color
        self.canvas.pack(side=tk.TOP, fill='both', expand=True)
        self.canvas.create_text(320, 240, text="Webcam feed", fill="white", font=('Arial', 20))

        self.btn_toggle_webcam = tk.Button(self.main_frame, text="Start", width=10, command=self.toggle_webcam, bg='green')
        self.btn_toggle_webcam.pack(side=tk.TOP, pady=10)

        self.gesture_action_map = {gesture: tk.StringVar(value=action) for gesture, action in gesture_action_map.items()}

        self.gesture_frame = tk.Frame(self.main_frame, bg='white')  # Changed background color
        self.gesture_frame.pack(side=tk.BOTTOM, fill='both', expand=True, padx=10, pady=10)

        self.create_gestures_ui()
        self.running = False
        self.update()

    def create_gestures_ui(self):
        label_font = ('Arial', 12, 'bold')
        dropdown_font = ('Arial', 12)

        for row, (gesture, action_var) in enumerate(self.gesture_action_map.items()):
            gesture_label = tk.Label(self.gesture_frame, text=gesture, bg='white', font=label_font, width=20, relief='solid')
            gesture_label.grid(row=row, column=0, padx=10, pady=5, sticky='ew')

            arrow_label = tk.Label(self.gesture_frame, text='→', bg='white', font=label_font, width=5)  # Changed background color
            arrow_label.grid(row=row, column=1, padx=5, pady=5)

            dropdown = tk.OptionMenu(self.gesture_frame, action_var, *options)
            dropdown.config(font=dropdown_font, anchor='w')
            dropdown.grid(row=row, column=2, padx=10, pady=5, sticky='ew')

    def toggle_webcam(self):
        self.running = not self.running
        self.btn_toggle_webcam.config(text="Stop" if self.running else "Start", bg='red' if self.running else 'green')
        if not self.running:
            self.canvas.delete("all")

    def update(self):
        if self.running:
            ret, frame = self.vid.read()
            if ret:
                self.process_frame(frame)
        else:
            self.canvas.delete("all")
            self.canvas.create_text(320, 240, text="Webcam feed", fill="white", font=('Arial', 20))
        self.window.after(10, self.update)

    def process_frame(self, frame):
        frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        results = hands.process(frame)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                if gesture := gesture_recognized(hand_landmarks):
                    action = self.gesture_action_map.get(gesture).get()
                    if action and action != "None":
                        perform_action(action)
                        cv2.putText(frame, f'Gesture Recognized: {gesture}', (10, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                        cv2.putText(frame, f'Action: {action}', (10, 100),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)))
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

if __name__ == "__main__":
    root = tk.Tk()
    app = GestureLinkApp(root, "Gesture Link App")
    root.mainloop()
