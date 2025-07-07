import time
import os
import csv
from datetime import datetime

class SessionTracker:
    LOG_FILE = "session_logs.csv"

    def __init__(self, cycle_id):
        self.cycle_id = cycle_id
        self.running = False
        self.start_time = None
        self.current_student = None
        self.total_voltage = 0.0
        self.voltage_samples = 0

        # Ensure log file exists
        if not os.path.exists(self.LOG_FILE):
            with open(self.LOG_FILE, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Student", "Cycle", "Start", "End", "Duration (s)", "Energy (kWh)"])

    def start(self, student):
        """Start a new session for the given student"""
        self.running = True
        self.current_student = student
        self.start_time = time.time()
        self.total_voltage = 0.0
        self.voltage_samples = 0

    def update_voltage(self, voltage_mV):
        """
        Accepts real-time voltage in mV from ESP32.
        Converts to volts internally and accumulates.
        """
        if self.running:
            # Convert mV → V and accumulate
            voltage_V = voltage_mV / 1000.0
            self.total_voltage += voltage_V
            self.voltage_samples += 1

    def stop(self):
        """Stop current session and save to CSV"""
        if not self.running:
            return

        end_time = time.time()
        duration = end_time - self.start_time
        average_voltage = self.total_voltage / self.voltage_samples if self.voltage_samples else 0.0

        # kWh = average_voltage (V) * average_current (A) * duration (h)
        # For now we assume average_current = 1 A (can be improved later)
        average_current_A = 1.0  # Placeholder – can come from ESP32 later
        energy_kwh = (average_voltage * average_current_A * duration) / 3600.0  # J → Wh → kWh

        # Write session to CSV
        try:
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
        except Exception as e:
            print(f"[ERROR] Failed to write to CSV: {e}")

        # Reset tracker state
        self.running = False
        self.current_student = None
        self.total_voltage = 0.0
        self.voltage_samples = 0

    def get_live_energy_kwh(self):
        """Get current estimated energy without stopping the session"""
        if not self.running:
            return 0.0
        current_duration = time.time() - self.start_time
        average_voltage = self.total_voltage / self.voltage_samples if self.voltage_samples else 0.0
        average_current_A = 1.0  # Placeholder
        return (average_voltage * average_current_A * current_duration) / 3600.0
