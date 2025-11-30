import os
import subprocess
import webbrowser

class AppLauncher:
    def __init__(self):
        self.apps = {
            "discord": "discord://",
            "whatsapp": "whatsapp://",
            "spotify": "spotify://",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "vscode": r"C:\Users\Hans\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "pycharm": r"C:\Program Files\JetBrains\PyCharm\bin\pycharm64.exe",
        }

    def open_app(self, app_name):
        app_name = app_name.lower()
        print("[DEBUG] App requested:", app_name)

        if app_name not in self.apps:
            print(f"[AppLauncher] App '{app_name}' not registered")
            return False

        path = self.apps[app_name]

        try:
            # ⚠ FIX → kalau path pakai protocol (discord:// / spotify:// / whatsapp://)
            if path.endswith("://"):
                webbrowser.open(path)
                print(f"[AppLauncher] Opening via protocol: {app_name}")
                return True

            # ⚠ Kalau .exe → buka normal
            subprocess.Popen(path)
            print(f"[AppLauncher] Opening exe: {app_name}")
            print("[DEBUG] Path:", path)

            return True

        except Exception as e:
            print(f"[AppLauncher] Failed: {e}")
            return False
