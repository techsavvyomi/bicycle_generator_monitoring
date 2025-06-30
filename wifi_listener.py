# wifi_listener.py
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import requests
import time


class WifiPoller(QObject):
    data_received = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            try:
                response = requests.get("http://192.168.4.1/", timeout=2)
                if response.status_code == 200:
                    json_data = response.json()
                    self.data_received.emit(json_data)
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(1)
