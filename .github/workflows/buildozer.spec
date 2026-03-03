[app]

# App name
title = Phone Controller

# Package name
package.name = phonecontroller

# Package domain
package.domain = org.phonecontroller

# Source code directory
source.dir = .

# Source files to include
source.include_exts = py,png,jpg,kv,atlas

# Main script
source.main = main.py

# Application version
version = 1.0

# Requirements
requirements = python3,kivy,pyjnius,android,python-socketio,websocket-client

# Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO

# Android API
android.api = 33

# Minimum API
android.minapi = 21

# NDK API
android.ndk_api = 21

# SDK version
android.sdk = 33

# NDK version
android.ndk = 25b

# Architecture
android.archs = arm64-v8a,armeabi-v7a

# Allow backup
android.allow_backup = True

# Orientation
orientation = portrait

# Fullscreen
fullscreen = 0

# Icon (optional)
# icon.filename = %(source.dir)s/icon.png

# Presplash color
android.presplash_color = #1a1a2e

# Features
android.features = android.hardware.camera

[buildozer]

# Log level
log_level = 2

# Warn on root
warn_on_root = 1
