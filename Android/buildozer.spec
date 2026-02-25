[app]

# (str) Title of your application
title = YTDownloader

# (str) Package name
package.name = YTDownloader

# (str) Package domain (needed for android/ios packaging)
package.domain = org.Venom120

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,models/*,controllers/*,main.py,main.kv

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
#source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 2.0.0

# (list) Application requirements
# Using youtube-dl for Android (pure Python, no compilation issues)
# For Windows/Desktop, use yt-dlp from Windows/requirements.txt
requirements = python3==3.9.19,kivy==2.1.0,youtube-dl,certifi,pillow,requests

# (str) Presplash of the application
presplash.filename = %(source.dir)s/assets/splash_screen.png

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/Youtube_icon.ico

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = ACCESS_NETWORK_STATE,INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (str) Android SDK build-tools version to use
android.build_tools_version = 34.0.0

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (bool) Accept Android SDK license automatically
android.accept_sdk_license = True

# (list) Java classes to add to the bootstrap
android.add_src =

# (str) Gradle dependencies (for additional build support)
android.gradle_dependencies =

# (bool) Enable NDK build (required for some native modules)
android.ndk_version = 25b

# (list) List of Java classes to add as Java.importClass in Python
android.add_libs_armeabi_v7a =
android.add_libs_arm64_v8a =

# (str) The format used to package the app for release mode (aab or apk or aar).
# android.release_artifact = aab

# (str) The format used to package the app for debug mode (apk or aar).
# android.debug_artifact = apk

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage
log_dir = .buildozer/logs
