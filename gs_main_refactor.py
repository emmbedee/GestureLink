import sys
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QHBoxLayout, QGridLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
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

class GestureLinkApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gesture Link App")
        self.setGeometry(100, 100, 800, 600)  # Set initial size and position of the window

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Webcam feed
        self.webcam_label = QLabel("Webcam feed")
        self.layout.addWidget(self.webcam_label)

        # Toggle webcam button
        self.toggle_webcam_button = QPushButton("Start Webcam")
        self.toggle_webcam_button.clicked.connect(self.toggle_webcam)
        self.layout.addWidget(self.toggle_webcam_button)

        # Gesture-action mapping UI
        self.gesture_frame = QWidget()
        self.gesture_layout = QGridLayout()
        self.gesture_frame.setLayout(self.gesture_layout)
        self.layout.addWidget(self.gesture_frame)
        self.setup_gesture_ui()

        self.video_source = 0
        self.vid = cv2.VideoCapture(self.video_source)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def setup_gesture_ui(self):
        for i, gesture in enumerate(["closed_fist", "index_pinky_up", "index_pinky_thumb_up", "L_shape", "middle_ring_up", "index_middle_up"]):
            label = QLabel(gesture)
            self.gesture_layout.addWidget(label, i, 0)
            combobox = QComboBox()
            combobox.addItems(["None", "volumemute", "show_desktop", "maximize_windows", "volumeup", "volumeup_x2", "alt_tab"])
            self.gesture_layout.addWidget(combobox, i, 1)

    def toggle_webcam(self):
        if self.timer.isActive():
            self.timer.stop()
            self.toggle_webcam_button.setText("Start Webcam")
        else:
            self.timer.start(20)  # Update frame every 20 ms
            self.toggle_webcam_button.setText("Stop Webcam")

    def update_frame(self):
        ret, frame = self.vid.read()
        if ret:
            frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            # ... [rest of the frame processing logic]
            image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.webcam_label.setPixmap(QPixmap.fromImage(image))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = GestureLinkApp()
    mainWin.show()
    sys.exit(app.exec_())
