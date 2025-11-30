import os
import subprocess

class SmartLauncher:
    def __init__(self):
        self.search_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            os.path.expanduser(r"~\AppData\Local"),
            os.path.expanduser(r"~\AppData\Roaming"),
        ]
        self.apps = self.scan_apps()

    def scan_apps(self):
        apps = {}
        print("[Launcher] Scanning apps... (1–3 mins first time)")

        for root in self.search_paths:
            for dirpath, _, files in os.walk(root):
                for f in files:
                    if f.lower().endswith(".exe"):
                        app_name = f.lower().replace(".exe", "")
                        full_path = os.path.join(dirpath, f)
                        apps[app_name] = full_path
        print(f"[Launcher] Scan complete. {len(apps)} apps detected.")
        return apps

    def open(self, name):
        name = name.lower().strip()
        print("[Launcher] Request to open:", name)

        # kecocokan fuzzy
        for key, path in self.apps.items():
            if name in key:  # contoh: "chrome" cocok dengan "googlechrome"
                try:
                    subprocess.Popen(path)
                    print("[Launcher] Opening:", key)
                    return True
                except Exception as e:
                    print("[Launcher] Error:", e)
                    return False

        print("[Launcher] App not found:", name)
        return False
