[app]

# (str) Title of your application
title = Golden Pulse

# (str) Package name
package.name = goldenpulse

# (str) Package domain (needed for android packaging)
package.domain = org.goldenpulse

# (str) Source files where the let's go
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,db

# (list) Application requirements
requirements = python3,kivy

# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (str) Version of the application
version = 0.1.0

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android NDK version to use
android.ndk_version = 25b

# (str) Android build tools version
android.build_tools_version = 33.0.2

# (list) Application permissions
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (list) Supported architectures
android.archs = arm64-v8a, armeabi-v7a
