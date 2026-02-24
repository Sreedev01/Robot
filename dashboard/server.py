# dashboard/server.py

from flask import Flask, Response
import threading

app = Flask(__name__)

def start_server(generate_frames, port=5000):
    @app.route('/')
    def video_feed():
        return Response(generate_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)).start()