import sys
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QGridLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
import mediapipe as mp
import time
import pyautogui

# Initialize MediaPipe solutions for hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# Global variables for action timing
last_action_time = 0
action_interval = 1
gesture_action_map = {
    "closed_fist": None,
    "index_pinky_up": None,
    "index_pinky_thumb_up": None,
    "L_shape": None,
    "middle_ring_up": None,
    "index_middle_up": None
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
        self.webcam_label = QLabel("Webcam feed")
        self.webcam_label.setAlignment(Qt.AlignCenter)
        self.webcam_label.setStyleSheet("border: 1px solid #ddd; padding: 10px;")
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
        self.setup_gesture_ui()

    def setup_gesture_ui(self):
        gesture_labels = {
            "closed_fist": "Closed Fist",
            "index_pinky_up": "Index Pinky Up",
            "index_pinky_thumb_up": "Index Pinky Thumb Up",
            "L_shape": "L Shape",
            "middle_ring_up": "Middle Ring Up",
            "index_middle_up": "Index Middle Up"
        }
        self.comboboxes = {}
        for i, (gesture_key, gesture_name) in enumerate(gesture_labels.items()):
            label = QLabel(gesture_name)
            self.gesture_layout.addWidget(label, i, 0)
            combobox = QComboBox()
            combobox.addItems(["None", "volumemute", "show_desktop", "maximize_windows", "volumeup", "volumeup_x2", "alt_tab"])
            combobox.setCurrentIndex(0)  # Set "None" as default
            combobox.currentIndexChanged.connect(lambda index, key=gesture_key, box=combobox: self.update_gesture_action_map(key, box))
            self.gesture_layout.addWidget(combobox, i, 1)
            self.comboboxes[gesture_key] = combobox

    def update_gesture_action_map(self, gesture, combobox):
        gesture_action_map[gesture] = combobox.currentText() if combobox.currentText() != "None" else None
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
            # Hand tracking and gesture recognition logic
            results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    gesture = gesture_recognized(hand_landmarks)
                    perform_action(gesture)
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
            self.webcam_label.setPixmap(QPixmap.fromImage(image))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = GestureLinkApp()
    mainWin.show()
    sys.exit(app.exec_())
