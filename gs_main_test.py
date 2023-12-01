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
options = ["volumemute", "show_desktop", "maximize_windows", "volumeup", "volumeup_x2", "alt_tab"]
gesture_action_map = {
    "closed_fist": "volumemute",
    "index_pinky_up": "show_desktop",
    "index_pinky_thumb_up": "maximize_windows",
    "L_shape": "volumeup",
    "middle_ring_up": "volumeup_x2",
    "index_middle_up": "alt_tab"
}

def gesture_recognized(hand_landmarks):
    thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip = [hand_landmarks.landmark[i] for i in [mp_hands.HandLandmark.THUMB_TIP, mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.PINKY_TIP]]
    index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]

    if thumb_tip.x < index_tip.x and thumb_tip.y < index_tip.y:
        return "L_shape"
    elif all(tip.y > index_mcp.y for tip in [index_tip, middle_tip, ring_tip, pinky_tip]):
        return "closed_fist"
    elif index_tip.y < index_mcp.y and pinky_tip.y < ring_tip.y:
        return "index_pinky_up"
    elif middle_tip.y < index_mcp.y and ring_tip.y < index_mcp.y:
        return "middle_ring_up"
    elif index_tip.y < index_mcp.y and pinky_tip.y < ring_tip.y and thumb_tip.x < index_tip.x:
        return "index_pinky_thumb_up"
    elif index_tip.y < index_mcp.y and middle_tip.y < index_mcp.y:
        return "index_middle_up"

def perform_action(gesture):
    global last_action_time
    if time.time() - last_action_time >= action_interval:
        action = gesture_action_map.get(gesture)
        if action:
            if action == "volumeup":
                pyautogui.press('volumeup')
            elif action == "volumeup_x2":
                pyautogui.press('volumeup')
                pyautogui.press('volumeup')
            elif action == "volumemute":
                pyautogui.press('volumemute')
            elif action == "show_desktop":
                pyautogui.hotkey('win', 'd')
            elif action == "maximize_windows":
                pyautogui.hotkey('win', 'shift', 'm')
            elif action == "alt_tab":
                pyautogui.hotkey('alt', 'tab')
        last_action_time = time.time()

class GestureLinkApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.resizable(False, False)
        self.window.title(window_title)
        self.main_frame = tk.Frame(window)
        self.main_frame.pack(fill='both', expand=True)

        self.video_source = 0
        self.vid = cv2.VideoCapture(self.video_source)
        self.canvas = tk.Canvas(self.main_frame, width=640, height=480, bg='grey')
        self.canvas.pack(side=tk.TOP, fill='both', expand=True)
        self.canvas.create_text(320, 240, text="Webcam feed", fill="white", font=('Arial', 20))

        self.btn_toggle_webcam = tk.Button(self.main_frame, text="Start", width=10, command=self.toggle_webcam, bg='green')
        self.btn_toggle_webcam.pack(side=tk.TOP, pady=10)

        # Initialize gesture_action_map with None for each gesture
        self.gesture_action_map = {gesture: None for gesture in ["closed_fist", "index_pinky_up", "index_pinky_thumb_up", "L_shape", "middle_ring_up", "index_middle_up"]}
        self.action_taken = {option: False for option in options}  # Track if an action is taken

        self.gesture_frame = tk.Frame(self.main_frame, bg='lightgrey')
        self.gesture_frame.pack(side=tk.BOTTOM, fill='both', expand=True)
        self.create_gestures_ui()

        self.running = False
        self.update()

    def create_gestures_ui(self):
        label_font = ('Arial', 12, 'bold')
        dropdown_font = ('Arial', 12)
        bg_color = '#f0f0f0'
        text_color = '#333'

        self.gesture_frame = tk.Frame(self.main_frame, bg=bg_color)
        self.gesture_frame.pack(side=tk.BOTTOM, fill='both', expand=True, padx=10, pady=10)

        for row, (gesture, action) in enumerate(self.gesture_action_map.items()):
            gesture_label = tk.Label(self.gesture_frame, text=gesture, bg='white', fg=text_color, font=label_font, width=20, relief='solid')
            gesture_label.grid(row=row, column=0, padx=10, pady=5, sticky='ew')

            arrow_label = tk.Label(self.gesture_frame, text='→', bg=bg_color, fg=text_color, font=label_font, width=20)
            arrow_label.grid(row=row, column=1, padx=5, pady=5)

            dropdown_var = tk.StringVar(self.gesture_frame)
            dropdown_var.set(action)  # default value
            dropdown = tk.OptionMenu(self.gesture_frame, dropdown_var, "None", *options, command=lambda value, g=gesture: self.update_gesture_action(g, value))
            dropdown.config(font=dropdown_font, anchor='w')
            dropdown.grid(row=row, column=2, padx=10, pady=5, sticky='ew')

            menu = dropdown["menu"]
            menu.delete(0, 'end')
            menu.add_command(label="None", command=tk._setit(dropdown_var, "None", lambda value="None", g=gesture: self.update_gesture_action(g, value)))
            for option in options:
                menu.add_command(label=option, command=tk._setit(dropdown_var, option, lambda value=option, g=gesture: self.update_gesture_action(g, value)))
                if self.action_taken[option] and self.gesture_action_map[gesture] != option:
                    menu.entryconfig(option, state='disabled')

    def update_gesture_action(self, gesture, new_action):
        if new_action == "None":
            new_action = None

        if self.gesture_action_map[gesture]:
            self.action_taken[self.gesture_action_map[gesture]] = False

        self.gesture_action_map[gesture] = new_action
        if new_action:
            self.action_taken[new_action] = True

        self.gesture_frame.pack_forget()
        self.gesture_frame.destroy()
        self.gesture_frame = tk.Frame(self.main_frame, bg='lightgrey')
        self.create_gestures_ui()


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
                if (gesture := gesture_recognized(hand_landmarks)):
                    perform_action(gesture)
                    cv2.putText(frame, f'Gesture Recognized: {gesture}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)))
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

if __name__ == "__main__":
    root = tk.Tk()
    app = GestureLinkApp(root, "Gesture Link App")
    root.mainloop()
