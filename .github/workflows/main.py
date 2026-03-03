"""
Phone Controller Client App
Connects to server and executes remote commands
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window

import threading
import json
import socket

# Set window size for testing on desktop
if platform != 'android':
    Window.size = (400, 700)

# Android specific imports
if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission
    
    # Android classes
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    Context = autoclass('android.content.Context')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    MediaStore = autoclass('android.provider.MediaStore')
    Settings = autoclass('android.provider.Settings')

# Socket.IO client
try:
    import socketio
except ImportError:
    socketio = None


class PhoneControllerApp(App):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sio = None
        self.server_url = ""
        self.connected = False
        self.phone_id = self.get_phone_id()
    
    def get_phone_id(self):
        """Get unique phone identifier"""
        try:
            return socket.gethostname()
        except:
            return "AndroidPhone"
    
    def build(self):
        """Build the UI"""
        
        # Request permissions on Android
        if platform == 'android':
            request_permissions([
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.CAMERA,
            ])
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Header
        header = Label(
            text='📱 Phone Controller',
            font_size='28sp',
            size_hint_y=0.08,
            bold=True
        )
        main_layout.add_widget(header)
        
        # Status indicator
        self.status_label = Label(
            text='🔴 Disconnected',
            font_size='18sp',
            size_hint_y=0.05
        )
        main_layout.add_widget(self.status_label)
        
        # Server URL section
        url_label = Label(
            text='Server URL:',
            font_size='16sp',
            size_hint_y=0.04,
            halign='left'
        )
        main_layout.add_widget(url_label)
        
        self.url_input = TextInput(
            text='http://192.168.1.100:5000',
            multiline=False,
            size_hint_y=0.08,
            font_size='16sp'
        )
        main_layout.add_widget(self.url_input)
        
        # Connect button
        self.connect_btn = Button(
            text='🔗 Connect',
            size_hint_y=0.08,
            font_size='18sp',
            background_color=(0.2, 0.8, 0.2, 1)
        )
        self.connect_btn.bind(on_press=self.toggle_connection)
        main_layout.add_widget(self.connect_btn)
        
        # Separator
        main_layout.add_widget(Label(text='─' * 50, size_hint_y=0.03))
        
        # Log section
        log_label = Label(
            text='📋 Activity Log:',
            font_size='16sp',
            size_hint_y=0.04,
            halign='left'
        )
        main_layout.add_widget(log_label)
        
        # Scrollable log
        scroll = ScrollView(size_hint_y=0.52)
        self.log_text = TextInput(
            text='Ready to connect...\n',
            multiline=True,
            readonly=True,
            font_size='14sp',
            background_color=(0.1, 0.1, 0.15, 1),
            foreground_color=(0.9, 0.9, 0.9, 1)
        )
        scroll.add_widget(self.log_text)
        main_layout.add_widget(scroll)
        
        return main_layout
    
    def toggle_connection(self, instance):
        """Connect or disconnect from server"""
        if self.connected:
            self.disconnect_from_server()
        else:
            self.connect_to_server()
    
    def connect_to_server(self):
        """Connect to the control server"""
        if socketio is None:
            self.add_log("❌ socketio not installed!")
            return
        
        self.server_url = self.url_input.text.strip()
        self.add_log(f"Connecting to {self.server_url}...")
        
        # Create socket client
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=2
        )
        
        # Register event handlers
        @self.sio.on('connect')
        def on_connect():
            Clock.schedule_once(lambda dt: self.on_connected())
        
        @self.sio.on('disconnect')
        def on_disconnect():
            Clock.schedule_once(lambda dt: self.on_disconnected())
        
        @self.sio.on('execute_command')
        def on_command(data):
            Clock.schedule_once(lambda dt: self.execute_command(data))
        
        # Connect in background thread
        threading.Thread(target=self._connect_thread, daemon=True).start()
    
    def _connect_thread(self):
        """Background thread for connection"""
        try:
            self.sio.connect(self.server_url)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.add_log(f"❌ Connection failed: {e}"))
    
    def disconnect_from_server(self):
        """Disconnect from server"""
        try:
            if self.sio:
                self.sio.disconnect()
        except:
            pass
        self.on_disconnected()
    
    def on_connected(self):
        """Called when connected to server"""
        self.connected = True
        self.status_label.text = '🟢 Connected'
        self.connect_btn.text = '❌ Disconnect'
        self.connect_btn.background_color = (0.8, 0.2, 0.2, 1)
        self.add_log("✅ Connected to server!")
        
        # Register this phone
        self.sio.emit('phone_register', {
            'phone_id': self.phone_id,
            'platform': platform
        })
    
    def on_disconnected(self):
        """Called when disconnected from server"""
        self.connected = False
        self.status_label.text = '🔴 Disconnected'
        self.connect_btn.text = '🔗 Connect'
        self.connect_btn.background_color = (0.2, 0.8, 0.2, 1)
        self.add_log("⚠️ Disconnected from server")
    
    def execute_command(self, data):
        """Execute command received from server"""
        cmd = data.get('cmd', '')
        self.add_log(f"📥 Command: {cmd}")
        
        if platform != 'android':
            self.add_log(f"⚠️ Not on Android, simulating: {cmd}")
            self.send_result(f"Simulated: {cmd}")
            return
        
        try:
            result = self._run_android_command(cmd, data)
            self.add_log(f"✅ Executed: {cmd}")
            self.send_result(f"OK: {cmd}")
        except Exception as e:
            self.add_log(f"❌ Error: {e}")
            self.send_result(f"Error: {e}")
    
    def _run_android_command(self, cmd, data):
        """Run command on Android device"""
        activity = PythonActivity.mActivity
        
        # App launching commands
        if cmd == 'camera':
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            activity.startActivity(intent)
        
        elif cmd == 'whatsapp':
            intent = activity.getPackageManager().getLaunchIntentForPackage('com.whatsapp')
            if intent:
                activity.startActivity(intent)
        
        elif cmd == 'chrome':
            intent = Intent(Intent.ACTION_VIEW, Uri.parse('https://www.google.com'))
            intent.setPackage('com.android.chrome')
            activity.startActivity(intent)
        
        elif cmd == 'youtube':
            intent = Intent(Intent.ACTION_VIEW, Uri.parse('https://www.youtube.com'))
            activity.startActivity(intent)
        
        elif cmd == 'instagram':
            intent = activity.getPackageManager().getLaunchIntentForPackage('com.instagram.android')
            if intent:
                activity.startActivity(intent)
        
        elif cmd == 'settings':
            intent = Intent(Settings.ACTION_SETTINGS)
            activity.startActivity(intent)
        
        elif cmd == 'gallery':
            intent = Intent(Intent.ACTION_VIEW)
            intent.setType('image/*')
            activity.startActivity(intent)
        
        elif cmd == 'phone':
            intent = Intent(Intent.ACTION_DIAL)
            activity.startActivity(intent)
        
        elif cmd == 'messages':
            intent = Intent(Intent.ACTION_VIEW)
            intent.setData(Uri.parse('sms:'))
            activity.startActivity(intent)
        
        # Navigation commands
        elif cmd == 'home':
            intent = Intent(Intent.ACTION_MAIN)
            intent.addCategory(Intent.CATEGORY_HOME)
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity.startActivity(intent)
        
        elif cmd == 'open_url':
            url = data.get('url', 'https://google.com')
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            activity.startActivity(intent)
        
        # Volume commands
        elif cmd == 'volume_up':
            AudioManager = autoclass('android.media.AudioManager')
            audio = activity.getSystemService(Context.AUDIO_SERVICE)
            audio.adjustVolume(AudioManager.ADJUST_RAISE, AudioManager.FLAG_SHOW_UI)
        
        elif cmd == 'volume_down':
            AudioManager = autoclass('android.media.AudioManager')
            audio = activity.getSystemService(Context.AUDIO_SERVICE)
            audio.adjustVolume(AudioManager.ADJUST_LOWER, AudioManager.FLAG_SHOW_UI)
        
        elif cmd == 'mute':
            AudioManager = autoclass('android.media.AudioManager')
            audio = activity.getSystemService(Context.AUDIO_SERVICE)
            audio.adjustVolume(AudioManager.ADJUST_MUTE, AudioManager.FLAG_SHOW_UI)
        
        return True
    
    def send_result(self, result):
        """Send command result back to server"""
        if self.sio and self.connected:
            try:
                self.sio.emit('command_result', {'result': result})
            except:
                pass
    
    def add_log(self, message):
        """Add message to log"""
        import datetime
        time_str = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_text.text = f"[{time_str}] {message}\n" + self.log_text.text


# Run the app
if __name__ == '__main__':
    PhoneControllerApp().run()
