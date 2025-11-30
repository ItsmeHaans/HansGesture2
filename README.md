# HansGesture2
Gesture Control AI is an innovative computer vision application that allows users to control their laptop and operate various functions entirely hands-free using simple gestures captured by the webcam. This Python-based system eliminates the need for external devices like a mouse or keyboard for basic interactions.

# Hand Gesture Control API  
A FastAPI-based backend that powers a real-time hand-gesture controlled system for Windows.  
This API handles:

- 🎥 Live webcam streaming (MJPEG)
- ✋ Hand gesture detection (MediaPipe)
- 🖱️ Cursor control & system actions  
- 🔊 Voice assistant activation via gestures  
- 🌓 System brightness & volume control  
- 🚀 App launching via hand zones

This project is designed to run as a background service, while a frontend (web/desktop/mobile) connects to its real-time video stream and endpoints.

---

## 📌 Features

### 👋 **Gesture Control**
The gesture loop runs in a separate thread and handles:

- Left/Right/Up/Down scroll  
- Click (Fist gesture)  
- Move cursor using open-hand tracking  
- Brightness up/down  
- Volume up/down  
- App launching using left-area selector  
- Specialized gestures:
  - **German Three** → Start Voice Assistant
  - **Thumbs Up** → Stop Voice Assistant

### 🎥 **Live Webcam Stream**
- MJPEG real-time stream at:  
  **`GET /video-stream`**
- Frames are captured inside the gesture loop and pushed to a buffer.

### 🎤 **Voice Assistant**
Gesture-activated assistant:

- Start: via **German_3** gesture  
- Stop: via **Thumbs Up**

Backend has endpoints:

- `POST /voice-chat`
- `POST /voice-timer`

### 💻 **System Control**
Brightness (WMI):  
- `GET /sys/brightness`  
- Uses `WmiMonitorBrightness` + `WmiMonitorBrightnessMethods`

Volume (NirCmd):  
- `GET /sys/volume` (placeholder)  
- `volume_up(), volume_down()` via NirCmd.exe

### 🚀 **App Launcher**
Point hand to left-side regions → open specific apps.

---

## 📂 Project Structure

