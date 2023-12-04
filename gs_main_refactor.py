import sys
import time
import cv2
import os
import json
import pygame
import pyautogui
import mediapipe as mp
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QStatusBar,
)

# Initialize MediaPipe solutions for hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# Initialize pygame for audio feedback
pygame.init()
pygame.mixer.init()
chime_sound = pygame.mixer.Sound("chime.wav")

# Global variables for action timing
last_action_time = 0
action_interval = 1

# Map of recognized gestures to corresponding actions
gesture_action_map = {
    "closed_fist": None,
    "index_finger_up": None,
    "index_middle_finger_up": None,
    "index_middle_ring_finger_up": None,
    "index_middle_ring_pinky_finger_up": None,
    "index_pinky_up": None,
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, 'gesture_settings.json')


# Function to load gesture settings from a JSON file
def load_gesture_settings():
    try:
        with open('gesture_settings.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


# Function to save gesture settings to a JSON file
def save_gesture_settings():
    with open('gesture_settings.json', 'w') as file:
        json.dump(gesture_action_map, file)


# Function to recognize gestures based on hand landmarks
def gesture_recognized(hand_landmarks):
    thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip = [hand_landmarks.landmark[i] for i in [mp_hands.HandLandmark.THUMB_TIP, mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.PINKY_TIP]]
    index_mcp, middle_mcp, ring_mcp, pinky_mcp = [hand_landmarks.landmark[i] for i in [mp_hands.HandLandmark.INDEX_FINGER_MCP, mp_hands.HandLandmark.MIDDLE_FINGER_MCP, mp_hands.HandLandmark.RING_FINGER_MCP, mp_hands.HandLandmark.PINKY_MCP]]

    if all(tip.y > index_mcp.y for tip in [index_tip, middle_tip, ring_tip, pinky_tip]):
        return "closed_fist"
    elif index_tip.y < index_mcp.y and all(tip.y > index_mcp.y for tip in [middle_tip, ring_tip, pinky_tip]):
        return "index_finger_up"
    elif all(tip.y < index_mcp.y for tip in [index_tip, middle_tip]) and all(tip.y > index_mcp.y for tip in [ring_tip, pinky_tip]):
        return "index_middle_finger_up"
    elif all(tip.y < index_mcp.y for tip in [index_tip, middle_tip, ring_tip]) and pinky_tip.y > index_mcp.y:
        return "index_middle_ring_finger_up"
    elif all(tip.y < index_mcp.y for tip in [index_tip, middle_tip, ring_tip, pinky_tip]):
        return "index_middle_ring_pinky_finger_up"
    elif index_tip.y < index_mcp.y and pinky_tip.y < pinky_mcp.y and all(tip.y > mcp.y for tip, mcp in [(middle_tip, middle_mcp), (ring_tip, ring_mcp)]):
        return "index_pinky_up"


# Function to perform actions based on recognized gestures
def perform_action(gesture):
    global last_action_time
    if time.time() - last_action_time >= action_interval:
        action = gesture_action_map.get(gesture)
        if action:
            if action == "volume_up":
                pyautogui.press('volumeup')
                chime_sound.play()
            elif action == "volume_down":
                pyautogui.press('volumedown')
                chime_sound.play()
            elif action == "mute":
                pyautogui.press('volumemute')
                chime_sound.play()
            elif action == "show_desktop":
                pyautogui.hotkey('win', 'd')
                chime_sound.play()
            elif action == "play_pause_media":
                pyautogui.press('playpause')
                chime_sound.play()
            elif action == "alt_tab":
                pyautogui.hotkey('alt', 'tab')
                chime_sound.play()
        last_action_time = time.time()


# Main application window
class GestureLinkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gesture Link App")
        self.setGeometry(100, 100, 800, 600)

        # Load saved gesture settings
        loaded_settings = load_gesture_settings()
        if loaded_settings is not None:
            global gesture_action_map
            gesture_action_map.update(loaded_settings)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.gesture_recognition_active = False

        # Set styles for the widgets
        self.central_widget.setStyleSheet("""
            QWidget { font-family: 'Arial'; background-color: #f2f2f2; }
            QLabel { color: #555; font-size: 14px; }
            QPushButton { 
                border-radius: 10px; 
                background-color: #4CAF50; 
                color: white; 
                padding: 10px; 
                font-size: 14px; 
                margin: 10px 0; 
            }
            QPushButton:hover { background-color: #45a049; }
            QComboBox { 
                border-radius: 5px; 
                padding: 5px; 
                margin: 5px 0; 
                background-color: white;
                selection-background-color: #4CAF50;
            }
        """)

        # Webcam feed label
        self.webcam_label = QLabel("Press the start webcam button to activate.")
        self.webcam_label.setAlignment(Qt.AlignCenter)
        self.webcam_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 10px;  /* Rounded edges */
                background-color: white; /* Background color */
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2); /* Drop shadow */
                padding: 10px;
            }
        """)

        # Set the initial size of the webcam feed (adjust width and height as needed)
        initial_webcam_width = 640
        initial_webcam_height = 480
        self.webcam_label.setFixedSize(initial_webcam_width, initial_webcam_height)

        # Center the webcam feed in the window
        self.layout.addWidget(self.webcam_label, alignment=Qt.AlignCenter)

        # Toggle webcam button
        self.toggle_webcam_button = QPushButton("Start Webcam")
        self.toggle_webcam_button.clicked.connect(self.toggle_webcam)
        self.toggle_webcam_button.setToolTip("Click to start or stop the webcam")
        button_layout.addWidget(self.toggle_webcam_button)

        spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        button_layout.addItem(spacer)

        # Toggle gesture recognition button
        self.toggle_gesture_recognition_button = QPushButton("Activate Gesture Recognition")
        self.toggle_gesture_recognition_button.clicked.connect(self.toggle_gesture_recognition)
        self.toggle_gesture_recognition_button.setToolTip("Click to activate or deactivate gesture recognition")
        button_layout.addWidget(self.toggle_gesture_recognition_button)

        self.layout.addLayout(button_layout)

        # Gesture-action mapping UI
        self.gesture_frame = QWidget()
        self.gesture_layout = QGridLayout()
        self.gesture_frame.setLayout(self.gesture_layout)
        self.layout.addWidget(self.gesture_frame)
        self.setup_gesture_ui()
        self.update_comboboxes()

        self.video_source = 0
        self.vid = cv2.VideoCapture(self.video_source)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def setup_gesture_ui(self):
        gesture_labels = {
            "closed_fist": "Closed Fist",
            "index_finger_up": "Index Finger Up",
            "index_middle_finger_up": "Index Middle Finger Up",
            "index_middle_ring_finger_up": "Index Middle Ring Finger Up",
            "index_middle_ring_pinky_finger_up": "Index Middle Ring Pinky Finger Up",
            "index_pinky_up": "Index and Pinky Up",
        }
        self.comboboxes = {}
        for i, (gesture_key, gesture_name) in enumerate(gesture_labels.items()):
            label = QLabel(gesture_name)
            self.gesture_layout.addWidget(label, i, 0)
            combobox = QComboBox()
            combobox.addItems(["None", "volume_up", "volume_down", "mute", "show_desktop", "play_pause_media", "alt_tab"])
            combobox.setCurrentIndex(0)
            combobox.currentIndexChanged.connect(lambda index, key=gesture_key, box=combobox: self.update_gesture_action_map(key, box))
            self.gesture_layout.addWidget(combobox, i, 1)
            self.comboboxes[gesture_key] = combobox
        self.update_comboboxes()

    def update_gesture_action_map(self, gesture, combobox):
        gesture_action_map[gesture] = combobox.currentText() if combobox.currentText() != "None" else None
        save_gesture_settings()
        self.update_comboboxes()

    def update_comboboxes(self):
        for gesture, combobox in self.comboboxes.items():
            action = gesture_action_map.get(gesture)
            if action:
                index = combobox.findText(action)
                if index >= 0:
                    combobox.setCurrentIndex(index)
            else:
                combobox.setCurrentIndex(0)

            current_action = combobox.currentText()
            selected_actions = set(gesture_action_map.values())
            for i in range(combobox.count()):
                action = combobox.itemText(i)
                combobox.model().item(i).setEnabled(
                    action == "None" or
                    action not in selected_actions or
                    action == current_action
                )

    def toggle_webcam(self):
        if self.timer.isActive():
            self.timer.stop()
            self.toggle_webcam_button.setText("Start Webcam")
            self.toggle_webcam_button.setStyleSheet("background-color: #4CAF50;")
            self.statusBar.showMessage("Webcam is now stopped.")
        else:
            self.timer.start(20)
            self.toggle_webcam_button.setText("Stop Webcam")
            self.toggle_webcam_button.setStyleSheet("background-color: #f44336;")
            self.statusBar.showMessage("Webcam is now active.")

    def toggle_gesture_recognition(self):
        self.gesture_recognition_active = not self.gesture_recognition_active
        if self.gesture_recognition_active:
            self.toggle_gesture_recognition_button.setText("Deactivate Gesture Recognition")
            self.toggle_gesture_recognition_button.setStyleSheet("background-color: #f44336;")
            self.statusBar.showMessage("Gesture recognition is now active.")
        else:
            self.toggle_gesture_recognition_button.setText("Activate Gesture Recognition")
            self.toggle_gesture_recognition_button.setStyleSheet("background-color: #4CAF50;")
            self.statusBar.showMessage("Gesture recognition is now deactivated.")

    def update_frame(self):
        ret, frame = self.vid.read()
        if ret:
            frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            if self.gesture_recognition_active:
                results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        gesture = gesture_recognized(hand_landmarks)
                        action = gesture_action_map.get(gesture, "No action")
                        perform_action(gesture)
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                        cv2.putText(frame, f"Gesture Recognized: {gesture}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        cv2.putText(frame, f"Action: {action}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.webcam_label.setPixmap(QPixmap.fromImage(convert_to_Qt_format))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = GestureLinkApp()
    mainWin.show()
    sys.exit(app.exec_())
