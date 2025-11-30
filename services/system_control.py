import os
import wmi
import pythoncom

class SystemControl:
    def __init__(self):
        # Tidak boleh simpan WMI instance di sini (threading issue)
        self.current_brightness = None

    # =============================
    # READ CURRENT BRIGHTNESS
    # =============================
    def get_brightness(self):
        pythoncom.CoInitialize()
        try:
            c = wmi.WMI(namespace='wmi')  # ← WMI per-call
            level = c.WmiMonitorBrightness()[0].CurrentBrightness
            self.current_brightness = int(level)
            return self.current_brightness
        finally:
            pythoncom.CoUninitialize()

    # =============================
    # SET BRIGHTNESS
    # =============================
    def set_brightness(self, value):
        value = max(0, min(100, int(value)))

        pythoncom.CoInitialize()
        try:
            c = wmi.WMI(namespace='wmi')
            methods = c.WmiMonitorBrightnessMethods()[0]
            methods.WmiSetBrightness(value, 0)
            self.current_brightness = value
            return True
        finally:
            pythoncom.CoUninitialize()

    # =============================
    # BRIGHTNESS DOWN (TICK)
    # =============================
    def brightness_down(self, tick=10):
        if self.current_brightness is None:
            self.get_brightness()

        new_level = self.current_brightness - tick
        self.set_brightness(new_level)
        print(f"Brightness: {self.current_brightness}%")

    # =============================
    # BRIGHTNESS UP (TICK)
    # =============================
    def brightness_up(self, tick=10):
        if self.current_brightness is None:
            self.get_brightness()

        new_level = self.current_brightness + tick
        self.set_brightness(new_level)
        print(f"Brightness: {self.current_brightness}%")

    # =============================
    # VOLUME CONTROL (NirCmd)
    # =============================
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    NIRCMD_PATH = os.path.join(BASE_DIR, "nircmd.exe")

    def volume_up(self):
        os.system(f'"{self.NIRCMD_PATH}" changesysvolume 5000')

    def volume_down(self):
        os.system(f'"{self.NIRCMD_PATH}" changesysvolume -5000')

    # =============================
    # GET VOLUME LEVEL (NO API)
    # =============================
    def get_volume(self):
        return 0
