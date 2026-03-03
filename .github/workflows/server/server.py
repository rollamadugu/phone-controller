"""
Phone Controller Server
Run this on your PC to control phones remotely
"""

from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Connected phones
connected_phones = {}

# Web interface HTML
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>📱 Phone Controller</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 500px; margin: 0 auto; }
        h1 { text-align: center; color: #00d4ff; margin-bottom: 20px; }
        .status {
            text-align: center;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 10px;
            background: #0f3460;
            font-size: 18px;
        }
        .status.online { border-left: 5px solid #00ff00; }
        .status.offline { border-left: 5px solid #ff0000; }
        .section {
            background: #0f3460;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 15px;
        }
        .section h3 {
            color: #00d4ff;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #00d4ff44;
        }
        .btn-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }
        button {
            background: linear-gradient(135deg, #e94560, #ff6b6b);
            color: white;
            border: none;
            padding: 15px 10px;
            border-radius: 10px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        button:hover { transform: scale(1.05); }
        button:active { transform: scale(0.95); }
        .btn-nav { background: linear-gradient(135deg, #00d4ff, #0099cc); color: #000; }
        .btn-power { background: linear-gradient(135deg, #ff9900, #ff6600); }
        input {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 16px;
        }
        .input-row { display: flex; gap: 10px; }
        .input-row input { flex: 1; }
        #log {
            background: #0a0a1a;
            padding: 15px;
            border-radius: 10px;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 13px;
        }
        .log-item { padding: 5px 0; border-bottom: 1px solid #1a1a3e; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Phone Controller</h1>
        
        <div class="status offline" id="status">🔴 No Phone Connected</div>
        
        <div class="section">
            <h3>📲 Apps</h3>
            <div class="btn-grid">
                <button onclick="send('camera')">📷 Camera</button>
                <button onclick="send('whatsapp')">💬 WhatsApp</button>
                <button onclick="send('chrome')">🌐 Chrome</button>
                <button onclick="send('youtube')">▶️ YouTube</button>
                <button onclick="send('instagram')">📸 Instagram</button>
                <button onclick="send('settings')">⚙️ Settings</button>
                <button onclick="send('gallery')">🖼️ Gallery</button>
                <button onclick="send('phone')">📞 Phone</button>
                <button onclick="send('messages')">💬 SMS</button>
            </div>
        </div>
        
        <div class="section">
            <h3>🎮 Navigation</h3>
            <div class="btn-grid">
                <button class="btn-nav" onclick="send('home')">🏠 Home</button>
                <button class="btn-nav" onclick="send('back')">⬅️ Back</button>
                <button class="btn-nav" onclick="send('recent')">📑 Recent</button>
            </div>
        </div>
        
        <div class="section">
            <h3>🔊 Volume</h3>
            <div class="btn-grid">
                <button class="btn-power" onclick="send('volume_up')">🔊 Up</button>
                <button class="btn-power" onclick="send('volume_down')">🔉 Down</button>
                <button class="btn-power" onclick="send('mute')">🔇 Mute</button>
            </div>
        </div>
        
        <div class="section">
            <h3>⌨️ Type Text</h3>
            <input type="text" id="textInput" placeholder="Enter text...">
            <button onclick="sendText()" style="width:100%">📝 Send Text</button>
        </div>
        
        <div class="section">
            <h3>🌐 Open URL</h3>
            <input type="url" id="urlInput" placeholder="https://example.com">
            <button onclick="sendUrl()" style="width:100%">🚀 Open URL</button>
        </div>
        
        <div class="section">
            <h3>📋 Log</h3>
            <div id="log"></div>
        </div>
    </div>
    
    <script>
        const socket = io();
        
        socket.on('phone_status', data => {
            const el = document.getElementById('status');
            if (data.online) {
                el.innerHTML = '🟢 Phone Connected: ' + data.phone_id;
                el.className = 'status online';
            } else {
                el.innerHTML = '🔴 No Phone Connected';
                el.className = 'status offline';
            }
        });
        
        socket.on('command_result', data => {
            addLog('Result: ' + data.result);
        });
        
        function send(cmd) {
            socket.emit('send_command', {cmd: cmd});
            addLog('Sent: ' + cmd);
        }
        
        function sendText() {
            const text = document.getElementById('textInput').value;
            if (text) {
                socket.emit('send_command', {cmd: 'type', text: text});
                addLog('Type: ' + text);
            }
        }
        
        function sendUrl() {
            const url = document.getElementById('urlInput').value;
            if (url) {
                socket.emit('send_command', {cmd: 'open_url', url: url});
                addLog('Open: ' + url);
            }
        }
        
        function addLog(msg) {
            const log = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            log.innerHTML = `<div class="log-item">[${time}] ${msg}</div>` + log.innerHTML;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_phones:
        del connected_phones[request.sid]
        emit('phone_status', {'online': False}, broadcast=True)

@socketio.on('phone_register')
def handle_register(data):
    phone_id = data.get('phone_id', 'Unknown')
    connected_phones[request.sid] = phone_id
    print(f"Phone registered: {phone_id}")
    emit('phone_status', {'online': True, 'phone_id': phone_id}, broadcast=True)

@socketio.on('send_command')
def handle_command(data):
    print(f"Command: {data}")
    emit('execute_command', data, broadcast=True)

@socketio.on('command_result')
def handle_result(data):
    emit('command_result', data, broadcast=True)

if __name__ == '__main__':
    print("="*50)
    print("📱 PHONE CONTROLLER SERVER")
    print("="*50)
    print("Local:   http://localhost:5000")
    print("Network: http://YOUR_PC_IP:5000")
    print("="*50)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
