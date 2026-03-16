from flask import Flask, Response, request, jsonify, send_from_directory
import cv2
import threading
import time
import sqlite3

from hardware.sensors import get_sensor_data
from hardware.camera import Camera
from movement.controller import MovementController
from vision.detector import Detector
from utils.logger import log_detection
from logs.writter import log_sensor_data

app = Flask(__name__)

# ==============================
# GLOBAL STATES
# ==============================
mode = "AUTO"
current_command = "STOP"
frame = None
last_detection_time = 0
DETECTION_COOLDOWN = 5

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

    if command == "BACKWARD":
        movement.move_forward(40)

    elif command == "FORWARD":
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

        time.sleep(0.02)


threading.Thread(target=camera_loop, daemon=True).start()

# ==============================
# AUTO MODE THREAD
# ==============================
def auto_loop():

    global mode, frame, last_detection_time

    while True:

        if frame is not None:

            f = frame.copy()

            results = detector.detect(f)
            persons = detector.get_person_detections(results)

            if len(persons) > 0:

                if mode == "AUTO":
                    move_robot("STOP")

                if time.time() - last_detection_time > DETECTION_COOLDOWN:

                    print("Human Detected!")

                    sensor = get_sensor_data()

                    lat = sensor.get("lat")
                    lon = sensor.get("lon")
                    temp = sensor.get("temperature")
                    gas = sensor.get("gas")

                    log_detection(frame, persons)
                    log_sensor_data(temp, gas, lat, lon)

                    last_detection_time = time.time()

            else:

                if mode == "AUTO":
                    move_robot("FORWARD")

        time.sleep(0.1)


threading.Thread(target=auto_loop, daemon=True).start()

# ==============================
# VIDEO STREAM
# ==============================
def generate_frames():

    global frame

    while True:

        if frame is None:
            continue

        f = frame.copy()

        results = detector.detect(f)
        persons = detector.get_person_detections(results)

        for (x1, y1, x2, y2) in persons:

            cv2.rectangle(f, (x1, y1), (x2, y2), (0,255,0), 2)

            cv2.putText(
                f,
                "HUMAN DETECTED",
                (x1, y1-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0,255,0),
                2
            )

        cv2.putText(
            f,
            f"Mode: {mode}",
            (20,40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2
        )

        cv2.putText(
            f,
            f"Cmd: {current_command}",
            (20,80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2
        )

        ret, buffer = cv2.imencode('.jpg', f)
        frame_bytes = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame_bytes +
            b'\r\n'
        )


# ==============================
# DASHBOARD
# ==============================
@app.route('/')
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rescue Robot Control</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#070d14;--surface:#0d1825;--surface2:#112030;
  --border:#1a3a55;--accent:#00e5ff;--accent2:#39ff14;
  --warn:#ff6b35;--text:#cce8f4;--muted:#5a8aaa;
  --mono:'Share Tech Mono',monospace;--sans:'Exo 2',sans-serif;
}
body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;overflow-x:hidden;}
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(0,229,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,255,0.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0;}
.shell{position:relative;z-index:1;}
header{display:flex;align-items:center;justify-content:space-between;padding:14px 28px;border-bottom:1px solid var(--border);background:rgba(7,13,20,0.95);position:sticky;top:0;z-index:100;}
.logo{display:flex;align-items:center;gap:10px;}
.logo-icon{width:32px;height:32px;border:2px solid var(--accent);border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:16px;}
.logo-text{font-family:var(--mono);font-size:14px;color:var(--accent);letter-spacing:2px;}
.logo-sub{font-size:10px;color:var(--muted);letter-spacing:1px;margin-top:1px;}
nav a{color:var(--muted);text-decoration:none;font-size:12px;letter-spacing:1px;text-transform:uppercase;padding-bottom:2px;border-bottom:1px solid transparent;transition:all .2s;margin-left:24px;}
nav a:hover,nav a.on{color:var(--accent);border-color:var(--accent);}
.pill{display:flex;align-items:center;gap:7px;padding:5px 12px;border-radius:999px;border:1px solid var(--border);font-family:var(--mono);font-size:11px;background:var(--surface);}
.dot{width:7px;height:7px;border-radius:50%;background:var(--accent2);animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.main{display:grid;grid-template-columns:1fr 300px;gap:16px;padding:20px 28px;max-width:1400px;margin:0 auto;}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.ph{display:flex;align-items:center;justify-content:space-between;padding:9px 14px;border-bottom:1px solid var(--border);background:rgba(0,229,255,0.03);}
.pt{font-family:var(--mono);font-size:10px;color:var(--accent);letter-spacing:2px;text-transform:uppercase;}
.pb{font-family:var(--mono);font-size:10px;color:var(--muted);background:var(--surface2);padding:2px 8px;border-radius:4px;border:1px solid var(--border);}
.vwrap{padding:12px;position:relative;}
.vwrap img{width:100%;border-radius:6px;border:1px solid var(--border);display:block;}
.vo{position:absolute;top:20px;left:20px;right:20px;bottom:20px;pointer-events:none;}
.c{position:absolute;width:14px;height:14px;border-color:var(--accent);border-style:solid;opacity:.7;}
.tl{top:0;left:0;border-width:2px 0 0 2px;border-radius:3px 0 0 0;}
.tr{top:0;right:0;border-width:2px 2px 0 0;border-radius:0 3px 0 0;}
.bl{bottom:0;left:0;border-width:0 0 2px 2px;border-radius:0 0 0 3px;}
.br{bottom:0;right:0;border-width:0 2px 2px 0;border-radius:0 0 3px 0;}
.vtag{position:absolute;top:6px;right:6px;font-family:var(--mono);font-size:9px;background:rgba(7,13,20,.85);color:var(--accent2);padding:2px 7px;border-radius:3px;}
.strip{display:flex;align-items:center;gap:14px;padding:8px 14px;border-top:1px solid var(--border);font-family:var(--mono);font-size:11px;}
.si{color:var(--muted);}
.si span{color:var(--accent);font-weight:600;}
.sensors{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:12px;}
.sc{background:var(--surface2);border:1px solid var(--border);border-radius:7px;padding:10px 12px;text-align:center;}
.sl{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;font-family:var(--mono);}
.sv{font-size:20px;font-weight:600;color:var(--accent);font-family:var(--mono);}
.su{font-size:10px;color:var(--muted);margin-left:2px;}
.sidebar{display:flex;flex-direction:column;gap:12px;}
.ms{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:12px;}
.mb{padding:10px;border-radius:7px;border:1px solid var(--border);background:var(--surface2);color:var(--muted);font-family:var(--mono);font-size:12px;letter-spacing:2px;cursor:pointer;text-align:center;transition:all .2s;}
.mb:hover{border-color:var(--accent);color:var(--accent);}
.mb.ma{background:rgba(57,255,20,.1);border-color:var(--accent2);color:var(--accent2);}
.mb.mm{background:rgba(0,229,255,.1);border-color:var(--accent);color:var(--accent);}
.dpad-wrap{padding:12px 12px 8px;display:flex;flex-direction:column;align-items:center;}
.dpad{display:grid;grid-template-columns:repeat(3,64px);grid-template-rows:repeat(3,64px);gap:5px;}
.db{background:var(--surface2);border:1px solid var(--border);border-radius:7px;color:var(--muted);font-size:20px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .15s;user-select:none;}
.db:hover{background:rgba(0,229,255,.1);border-color:var(--accent);color:var(--accent);}
.db:active,.db.pr{background:rgba(0,229,255,.2);border-color:var(--accent);color:var(--accent);transform:scale(.93);}
.db.sb{background:rgba(255,107,53,.1);border-color:var(--warn);color:var(--warn);font-size:11px;font-family:var(--mono);letter-spacing:1px;}
.db.sb:hover{background:rgba(255,107,53,.25);}
.db.em{background:transparent;border:none;cursor:default;pointer-events:none;}
.kh{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;padding:4px 12px 12px;}
.k{font-family:var(--mono);font-size:10px;color:var(--muted);background:var(--surface2);border:1px solid var(--border);border-radius:3px;padding:2px 6px;}
.feed{padding:10px 14px;display:flex;flex-direction:column;gap:0;max-height:160px;overflow-y:auto;}
.fi{display:flex;align-items:flex-start;gap:8px;font-size:11px;font-family:var(--mono);padding:5px 0;border-bottom:1px solid rgba(26,58,85,.4);animation:fin .3s ease;}
@keyframes fin{from{opacity:0;transform:translateY(-3px)}to{opacity:1;transform:translateY(0)}}
.ft{color:var(--muted);min-width:60px;font-size:10px;}
.fx{color:var(--text);flex:1;}
.fx.ok{color:var(--accent2);}
.fx.info{color:var(--accent);}
.fx.warn{color:var(--warn);}
.dl{display:block;margin:0 14px 14px;padding:9px;text-align:center;border:1px solid var(--border);border-radius:7px;color:var(--muted);text-decoration:none;font-family:var(--mono);font-size:11px;letter-spacing:1px;text-transform:uppercase;transition:all .2s;background:var(--surface2);}
.dl:hover{border-color:var(--accent);color:var(--accent);}
::-webkit-scrollbar{width:3px}::-webkit-scrollbar-track{background:var(--surface2)}::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
</style>
</head>
<body>
<div class="shell">

<header>
  <div class="logo">
    <div class="logo-icon">&#x1F916;</div>
    <div>
      <div class="logo-text">RESCUE-BOT</div>
      <div class="logo-sub">Control Interface</div>
    </div>
  </div>
  <nav>
    <a href="/" class="on">Dashboard</a>
    <a href="/detections">Detections</a>
  </nav>
  <div class="pill"><div class="dot"></div>SYSTEM ONLINE</div>
</header>

<div class="main">

  <div style="display:flex;flex-direction:column;gap:14px;">

    <div class="panel">
      <div class="ph">
        <span class="pt">&#x25A6; Live Camera Feed</span>
        <span class="pb">640 x 480</span>
      </div>
      <div class="vwrap">
        <img src="/video" alt="Live Feed">
        <div class="vo">
          <div class="c tl"></div><div class="c tr"></div>
          <div class="c bl"></div><div class="c br"></div>
          <div class="vtag">&#x25CF; REC</div>
        </div>
      </div>
      <div class="strip">
        <div class="si">MODE: <span id="mode-disp">AUTO</span></div>
        <div class="si">CMD: <span id="cmd-disp">STOP</span></div>
      </div>
    </div>

    <div class="panel">
      <div class="ph">
        <span class="pt">&#x25C6; Sensor Telemetry</span>
        <span class="pb" id="s-time">--:--:--</span>
      </div>
      <div class="sensors">
        <div class="sc">
          <div class="sl">Temperature</div>
          <div class="sv" id="s-temp">--<span class="su">&#xB0;C</span></div>
        </div>
        <div class="sc">
          <div class="sl">Gas Level</div>
          <div class="sv" id="s-gas">--<span class="su">ppm</span></div>
        </div>
        <div class="sc">
          <div class="sl">GPS</div>
          <div class="sv" style="font-size:12px;" id="s-gps">--</div>
        </div>
      </div>
    </div>

  </div>

  <div class="sidebar">

    <div class="panel">
      <div class="ph"><span class="pt">&#x25B6; Mode</span></div>
      <div class="ms">
        <button class="mb ma" id="btn-auto" onclick="setMode('AUTO')">AUTO</button>
        <button class="mb" id="btn-manual" onclick="setMode('MANUAL')">MANUAL</button>
      </div>
    </div>

    <div class="panel">
      <div class="ph">
        <span class="pt">&#x25A4; Controls</span>
        <span class="pb" id="ctrl-status">LOCKED</span>
      </div>
      <div class="dpad-wrap">
        <div class="dpad">
          <div class="db em"></div>
          <div class="db" id="db-f" onclick="sendCmd('FORWARD')">&#x2191;</div>
          <div class="db em"></div>
          <div class="db" id="db-l" onclick="sendCmd('LEFT')">&#x2190;</div>
          <div class="db sb" id="db-s" onclick="sendCmd('STOP')">STOP</div>
          <div class="db" id="db-r" onclick="sendCmd('RIGHT')">&#x2192;</div>
          <div class="db em"></div>
          <div class="db" id="db-b" onclick="sendCmd('BACKWARD')">&#x2193;</div>
          <div class="db em"></div>
        </div>
      </div>
      <div class="kh">
        <span class="k">W</span>
        <span class="k">A</span>
        <span class="k">S</span>
        <span class="k">D</span>
        <span class="k">SPACE=STOP</span>
      </div>
    </div>

    <div class="panel" style="flex:1;">
      <div class="ph">
        <span class="pt">&#x25AA; Event Log</span>
        <span class="pb" id="log-ct">0 events</span>
      </div>
      <div class="feed" id="log"></div>
      <a href="/detections" class="dl">&#x1F4C2; View All Detections</a>
    </div>

  </div>
</div>
</div>

<script>
var lc=0;
function ts(){return new Date().toLocaleTimeString('en-GB');}
function addLog(msg,type){
  lc++;
  document.getElementById('log-ct').textContent=lc+' events';
  var f=document.getElementById('log');
  var d=document.createElement('div');
  d.className='fi';
  d.innerHTML='<span class="ft">'+ts()+'</span><span class="fx '+type+'">'+msg+'</span>';
  f.insertBefore(d,f.firstChild);
  document.getElementById('s-time').textContent=ts();
}
function sendCmd(cmd){
  document.getElementById('cmd-disp').textContent=cmd;
  addLog('CMD \u2192 '+cmd, cmd==='STOP'?'warn':'info');
  var m={FORWARD:'db-f',BACKWARD:'db-b',LEFT:'db-l',RIGHT:'db-r',STOP:'db-s'};
  var b=document.getElementById(m[cmd]);
  if(b){b.classList.add('pr');setTimeout(function(){b.classList.remove('pr');},200);}
  fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd})});
}
function setMode(m){
  document.getElementById('mode-disp').textContent=m;
  document.getElementById('btn-auto').className='mb'+(m==='AUTO'?' ma':'');
  document.getElementById('btn-manual').className='mb'+(m==='MANUAL'?' mm':'');
  document.getElementById('ctrl-status').textContent=m==='MANUAL'?'ACTIVE':'LOCKED';
  addLog('Mode \u2192 '+m, m==='AUTO'?'ok':'info');
  fetch('/mode',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:m})});
}
var km={'w':'FORWARD','arrowup':'FORWARD','s':'BACKWARD','arrowdown':'BACKWARD','a':'LEFT','arrowleft':'LEFT','d':'RIGHT','arrowright':'RIGHT',' ':'STOP'};
document.addEventListener('keydown',function(e){
  var c=km[e.key.toLowerCase()];
  if(c){e.preventDefault();sendCmd(c);}
});
// Fetch real mode from server on load
fetch('/get_mode').then(r=>r.json()).then(data=>{
  var m=data.mode;
  document.getElementById('mode-disp').textContent=m;
  document.getElementById('btn-auto').className='mb'+(m==='AUTO'?' ma':'');
  document.getElementById('btn-manual').className='mb'+(m==='MANUAL'?' mm':'');
  document.getElementById('ctrl-status').textContent=m==='MANUAL'?'ACTIVE':'LOCKED';
});
addLog('System initialized','ok');
addLog('Camera stream active','info');
</script>
</body>
</html>"""


@app.route('/video')
def video():

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# ==============================
# SERVE DETECTION IMAGES
# ==============================
@app.route('/detections/<path:filename>')
def serve_detection_image(filename):
    return send_from_directory('detections', filename)


# ==============================
# DETECTION DATABASE PAGE
# ==============================
@app.route('/detections')
def detections():

    conn = sqlite3.connect("detections.db")
    c = conn.cursor()

    c.execute("SELECT timestamp, image_path FROM detections ORDER BY id DESC")

    rows = c.fetchall()

    conn.close()

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Detections - Rescue Robot</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#070d14;--surface:#0d1825;--surface2:#112030;--border:#1a3a55;--accent:#00e5ff;--accent2:#39ff14;--text:#cce8f4;--muted:#5a8aaa;--mono:'Share Tech Mono',monospace;--sans:'Exo 2',sans-serif;}
body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;}
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(0,229,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,255,0.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0;}
header{display:flex;align-items:center;justify-content:space-between;padding:14px 28px;border-bottom:1px solid var(--border);background:rgba(7,13,20,0.95);position:sticky;top:0;z-index:100;}
.logo{display:flex;align-items:center;gap:10px;}
.logo-icon{width:32px;height:32px;border:2px solid var(--accent);border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:16px;}
.logo-text{font-family:var(--mono);font-size:14px;color:var(--accent);letter-spacing:2px;}
.logo-sub{font-size:10px;color:var(--muted);letter-spacing:1px;margin-top:1px;}
nav a{color:var(--muted);text-decoration:none;font-size:12px;letter-spacing:1px;text-transform:uppercase;padding-bottom:2px;border-bottom:1px solid transparent;transition:all .2s;margin-left:24px;}
nav a:hover,nav a.on{color:var(--accent);border-color:var(--accent);}
.pill{display:flex;align-items:center;gap:7px;padding:5px 12px;border-radius:999px;border:1px solid var(--border);font-family:var(--mono);font-size:11px;background:var(--surface);}
.dot{width:7px;height:7px;border-radius:50%;background:var(--accent2);animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.body{max-width:1200px;margin:0 auto;padding:28px;position:relative;z-index:1;}
.pt{font-family:var(--mono);font-size:18px;color:var(--accent);letter-spacing:3px;margin-bottom:6px;}
.ps{color:var(--muted);font-size:13px;margin-bottom:28px;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;transition:border-color .2s;}
.card:hover{border-color:var(--accent);}
.card img{width:100%;display:block;border-bottom:1px solid var(--border);}
.cb{padding:14px;}
.ct{font-family:var(--mono);font-size:11px;color:var(--accent);margin-bottom:10px;}
.cm{display:grid;grid-template-columns:1fr 1fr;gap:7px;}
.mi{background:var(--surface2);border-radius:6px;padding:7px 10px;}
.ml{font-size:9px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;}
.mv{font-family:var(--mono);font-size:12px;color:var(--text);}
.empty{text-align:center;padding:80px 20px;color:var(--muted);font-family:var(--mono);font-size:14px;}
</style>
</head>
<body>
<header>
  <div class="logo">
    <div class="logo-icon">&#x1F916;</div>
    <div>
      <div class="logo-text">RESCUE-BOT</div>
      <div class="logo-sub">Detection Archive</div>
    </div>
  </div>
  <nav>
    <a href="/">Dashboard</a>
    <a href="/detections" class="on">Detections</a>
  </nav>
  <div class="pill"><div class="dot"></div>SYSTEM ONLINE</div>
</header>
<div class="body">
  <div class="pt">&#x25C6; HUMAN DETECTIONS</div>
  <div class="ps">All logged detection events &mdash; sorted by most recent</div>
  <div class="grid">"""

    if not rows:
        html += '<div class="empty">&#x25A6; No detections recorded yet</div>'

    for r in rows:

        t, img = r

        filename = img.split("/")[-1]

        html += f"""
    <div class="card">
      <img src="/detections/{filename}" alt="Detection">
      <div class="cb">
        <div class="ct">&#x25AA; {t}</div>
      </div>
    </div>"""

    html += """
  </div>
</div>
</body>
</html>"""

    return html


@app.route('/get_mode')
def get_mode():
    return jsonify({"mode": mode})


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