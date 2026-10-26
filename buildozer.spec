[app]
title = Golden Pulse - بئر علي حسين
package.name = goldenpulse
package.domain = org.goldenpulse
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,db
source.exclude_dirs = .git,.github,bin,__pycache__
version = 0.2.0
requirements = python3,kivy,arabic-reshaper,python-bidi,pyjnius
orientation = portrait
fullscreen = 0

# Include the Arabic font beside main.py; required for consistent Arabic glyphs.
source.include_patterns = *.py,*.ttf,*.json

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
