[app]

# (str) Title of your application
title = Golden Pulse

# (str) Package name
package.name = goldenpulse

# (str) Package domain (needed for android packaging)
package.domain = org.goldenpulse

# (str) Source files where the let's go
source.dir = .

# (list) Source files to include (let it empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,db

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy

# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk_version = 25b

# (bool) Automatically accept SDK license
android.accept_sdk_license = True

# (list) Application permissions
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (list) Supported architectures
android.archs = arm64-v8a, armeabi-v7a
