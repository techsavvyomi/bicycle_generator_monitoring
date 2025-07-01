import csv
import time
import os
from datetime import datetime

class SessionTracker:
    LOG_FILE = "session_logs.csv"

    def __init__(self, cycle_id):
        self.cycle_id = cycle_id
        self.running = False
        self.start_time = None
        self.current_student = None
        self.total_voltage = 0

        # Create CSV file if it doesn't exist
        if not os.path.exists(self.LOG_FILE):
            with open(self.LOG_FILE, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Student", "Cycle", "Start", "End", "Duration (s)", "Energy (kWh)"])

    def start(self, student):
        self.running = True
        self.start_time = time.time()
        self.current_student = student
        self.total_voltage = 0

    def update_voltage(self, voltage):
        if self.running:
            self.total_voltage += voltage

    def stop(self):
        if not self.running:
            return

        end_time = time.time()
        duration = end_time - self.start_time
        energy_kwh = self.total_voltage / 1000.0

        # Write to CSV
        with open(self.LOG_FILE, "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                self.current_student,
                self.cycle_id,
                datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S"),
                datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S"),
                int(duration),
                f"{energy_kwh:.3f}"
            ])

        # Reset state
        self.running = False
        self.current_student = None
        self.total_voltage = 0
