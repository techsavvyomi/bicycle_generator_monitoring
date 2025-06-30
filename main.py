# bike_energy_app/main.py
from PyQt5.QtWidgets import QApplication
import sys
from ui import EnergyApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EnergyApp()
    window.show()
    sys.exit(app.exec_())