import threading
import time
import requests

class WifiPoller:
    def __init__(self, ip="192.168.4.1", port=80):
        self.ip = ip
        self.port = port
        self.running = True
        self.poll_interval = 1  # seconds
        self.data_received_callback = None  # Will be set by the main app

    def start(self):
        """Start polling in a background thread"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()

    def run(self):
        """Background thread loop to poll ESP32 or device"""
        while self.running:
            try:
                url = f"http://{self.ip}:{self.port}/"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        if self.data_received_callback:
                            self.data_received_callback(json_data)
                    except ValueError:
                        print("Failed to parse JSON from response")
            except requests.exceptions.RequestException as e:
                # Optional: suppress errors if you don't want logs every second
                pass  # You can remove this line to see connection issues

            time.sleep(self.poll_interval)

    def stop(self):
        self.running = False
