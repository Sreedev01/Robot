from flask import Flask, Response, request, jsonify
import cv2
import threading
import time

from hardware.camera import Camera
from movement.controller import MovementController
from vision.detector import Detector
from utils.logger import log_detection

app = Flask(__name__)

# ==============================
# GLOBAL STATES
# ==============================
mode = "AUTO"          # AUTO or MANUAL
current_command = "STOP"
frame = None           # shared frame for streaming

# ==============================
# MODULE INITIALIZATION
# ==============================
camera = Camera(source=0, width=640, height=480)
movement = MovementController()
detector = Detector()

print("Rescue Robot System Started")
print("Open browser at http://<PI_IP>:5000\n")

# ==============================
# ROBOT MOVEMENT
# ==============================
def move_robot(command):
    global current_command
    current_command = command
    print("Robot Command:", command)

    # Replace with your motor GPIO logic
    if command == "FORWARD":
        movement.move_forward(40)
    elif command == "BACKWARD":
        movement.move_backward(40)
    elif command == "LEFT":
        movement.turn_left(30)
    elif command == "RIGHT":
        movement.turn_right(30)
    elif command == "STOP":
        movement.stop()


# ==============================
# CAMERA THREAD
# ==============================
def camera_loop():
    global frame
    while True:
        ret, f = camera.read()
        if ret:
            frame = f
        time.sleep(0.02)  # ~50 FPS

threading.Thread(target=camera_loop, daemon=True).start()

# ==============================
# AUTO MODE THREAD
# ==============================
def auto_loop():
    global mode, current_command
    last_logged_state = None

    while True:
        if mode == "AUTO" and frame is not None:
            f = frame.copy()

            # Human detection
            results = detector.detect(f)
            persons = detector.get_person_detections(results)

            # Decision & Movement
            if len(persons) > 0:
                move_robot("STOP")
                if last_logged_state != "STOP":
                    print("⚠ Human Detected!")
                    log_detection(persons)
                    last_logged_state = "STOP"
            else:
                move_robot("FORWARD")
                last_logged_state = "FORWARD"

        time.sleep(0.1)

threading.Thread(target=auto_loop, daemon=True).start()

# ==============================
# VIDEO STREAM GENERATOR
# ==============================
def generate_frames():
    global frame
    while True:
        if frame is None:
            continue
        f = frame.copy()

        # Draw human detection boxes
        results = detector.detect(f)
        persons = detector.get_person_detections(results)
        for (x1, y1, x2, y2) in persons:
            cv2.rectangle(f, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(f, "HUMAN DETECTED", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Overlay mode and command
        cv2.putText(f, f"Mode: {mode}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(f, f"Cmd: {current_command}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Encode frame
        _, buffer = cv2.imencode('.jpg', f)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame_bytes + b'\r\n')


# ==============================
# FLASK ROUTES
# ==============================
@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>Rescue Robot Control</title>
        <style>
            body { text-align:center; font-family:Arial; background:#111; color:white; }
            button { width:120px; height:50px; margin:5px; font-size:16px; }
            .mode { margin:20px; }
        </style>
    </head>
    <body>
        <h1>Rescue Robot</h1>

        <img src="/video" width="640"><br>

        <div class="mode">
            <button onclick="setMode('AUTO')">AUTO</button>
            <button onclick="setMode('MANUAL')">MANUAL</button>
        </div>

        <div>
            <button onclick="sendCmd('FORWARD')">Forward</button><br>
            <button onclick="sendCmd('LEFT')">Left</button>
            <button onclick="sendCmd('STOP')">Stop</button>
            <button onclick="sendCmd('RIGHT')">Right</button><br>
            <button onclick="sendCmd('BACKWARD')">Backward</button>
        </div>

        <script>
            function sendCmd(cmd) {
                fetch('/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: cmd})
                });
            }

            function setMode(newMode) {
                fetch('/mode', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({mode: newMode})
                });
            }
        </script>
    </body>
    </html>
    """

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/command', methods=['POST'])
def command():
    global mode
    if mode == "MANUAL":
        data = request.get_json()
        move_robot(data.get("command"))
    return jsonify({"status": "ok"})

@app.route('/mode', methods=['POST'])
def change_mode():
    global mode
    data = request.get_json()
    mode = data.get("mode")
    print("Mode changed to:", mode)
    return jsonify({"status": "mode updated"})


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        print("System shutting down...")
        movement.stop()
        movement.cleanup()
        camera.release()