import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import time
import threading
from wifi_listener import WifiPoller
from tracker import SessionTracker
from leaderboard import Leaderboard
import csv

class EnergyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚴‍♂️ Bicycle Energy Tracker")
        self.root.geometry("1280x720")

        # Initialize models
        self.poller = WifiPoller()
        self.poller_thread = threading.Thread(target=self.poller.run, daemon=True)
        self.poller.data_received = self.handle_new_data
        self.poller_thread.start()

        self.students = self.load_students()
        self.trackers = {f"Cycle {i+1}": SessionTracker(f"Cycle {i+1}") for i in range(8)}
        self.session_logs = []

        # UI setup
        self.create_widgets()
        self.update_ui()

        # Update timer
        self.update_timer()

    def create_widgets(self):
        frame_controls = ttk.LabelFrame(self.root, text="Session Controls", padding=10)
        frame_controls.pack(pady=10, fill=tk.X)

        ttk.Label(frame_controls, text="Select Student:").grid(row=0, column=0, padx=5)
        self.student_cb = ttk.Combobox(frame_controls, values=self.students)
        self.student_cb.grid(row=0, column=1, padx=5)

        self.refresh_btn = ttk.Button(frame_controls, text="Refresh", width=10, command=self.refresh_students)
        self.refresh_btn.grid(row=0, column=2, padx=5)

        ttk.Label(frame_controls, text="Select Bicycle:").grid(row=0, column=3, padx=5)
        self.cycle_cb = ttk.Combobox(frame_controls, values=list(self.trackers.keys()))
        self.cycle_cb.grid(row=0, column=4, padx=5)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.start_btn = ttk.Button(btn_frame, text="Start", width=15, command=self.start_session)
        self.stop_btn = ttk.Button(btn_frame, text="Stop", width=15, command=self.stop_session)
        self.reset_btn = ttk.Button(btn_frame, text="Reset All", width=15, command=self.reset_all_sessions)
        self.board_btn = ttk.Button(btn_frame, text="🏆 Leaderboard", width=15, command=self.show_leaderboard)
        self.sett_btn = ttk.Button(btn_frame, text="⚙️ Settings", width=15, command=self.open_settings)

        self.start_btn.grid(row=0, column=0, padx=5)
        self.stop_btn.grid(row=0, column=1, padx=5)
        self.reset_btn.grid(row=0, column=2, padx=5)
        self.board_btn.grid(row=0, column=3, padx=5)
        self.sett_btn.grid(row=0, column=4, padx=5)

        info_label = ttk.Label(self.root, text="Click row numbers to select/unselect sessions")
        info_label.pack()

        # Table with Sr. No.
        self.table = ttk.Treeview(self.root,
                                  columns=("Sr.", "Cycle", "Student", "Start", "End", "Duration", "kWh"),
                                  show='headings')
        for col in self.table["columns"]:
            self.table.heading(col, text=col)
            self.table.column(col, width=100 if col != "Sr." else 50)
        self.table.pack(pady=10, fill=tk.BOTH, expand=True)

        self.sel_label = ttk.Label(self.root, text="Selected: None")
        self.sel_label.pack()

        self.status_bar = ttk.Label(self.root, text="Status: Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bindings
        self.cycle_cb.bind("<<ComboboxSelected>>", lambda e: self.update_buttons())
        self.student_cb.bind("<<ComboboxSelected>>", lambda e: self.update_buttons())
        self.table.bind("<ButtonRelease-1>", self.on_row_click)  # Click event

        # Set default selections
        if self.trackers:
            self.cycle_cb.current(0)
        if self.students:
            self.student_cb.current(0)

    def on_row_click(self, event):
        selected = self.table.selection()
        if not selected:
            return

        item = selected[0]
        values = self.table.item(item, 'values')

        sr = values[0]
        cycle = values[1]
        student = values[2]

        # Auto-select in comboboxes
        if cycle in self.trackers:
            self.cycle_cb.set(cycle)
        if student in self.students:
            self.student_cb.set(student)

        # Highlight selection
        self.sel_label.config(text=f"Selected: {cycle} - {student}")

        self.update_buttons()

    def update_timer(self):
        self.update_ui()
        self.root.after(1000, self.update_timer)

    def handle_new_data(self, data):
        for ch in data['channels']:
            name = ch['channel']
            voltage = ch['voltage']
            if name.startswith("C"):
                index = int(name[1:]) - 1
                if 0 <= index < 8:
                    tracker_name = f"Cycle {index + 1}"
                    self.trackers[tracker_name].update_voltage(voltage)
        self.update_ui()

    def load_students(self):
        try:
            with open("students.csv", newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return [row['Name'] for row in reader]
        except Exception as e:
            print(e)
            return []

    def save_students(self):
        with open("students.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Name"])
            for name in self.students:
                writer.writerow([name])

    def refresh_students(self):
        self.students = self.load_students()
        self.student_cb['values'] = self.students
        self.status_bar.config(text="Student list refreshed")

    def update_buttons(self):
        cyc = self.cycle_cb.get()
        if not cyc or cyc not in self.trackers:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            return

        run = self.trackers[cyc].running
        state = tk.DISABLED if run else tk.NORMAL
        self.start_btn.config(state=state)
        self.stop_btn.config(state=tk.NORMAL if run else tk.DISABLED)

    def update_ui(self):
        for item in self.table.get_children():
            self.table.delete(item)

        # Populate logs
        for idx, log in enumerate(self.session_logs, start=1):
            self.table.insert('', 'end', values=(
                idx,
                log['cycle'],
                log['student'],
                datetime.fromtimestamp(log['start']).strftime('%H:%M:%S'),
                datetime.fromtimestamp(log['end']).strftime('%H:%M:%S') if log['end'] else "",
                f"{int(log['duration'])}s",
                f"{log['kwh']:.3f}"
            ))

        # Running sessions
        for cyc, tr in self.trackers.items():
            if tr.running:
                duration = int(time.time() - tr.start_time)
                self.table.insert('', 'end', values=(
                    "",  # No serial number for active sessions
                    cyc,
                    tr.current_student,
                    datetime.fromtimestamp(tr.start_time).strftime('%H:%M:%S'),
                    "",
                    f"{duration}s",
                    f"{tr.total_voltage / 1000:.3f}"
                ), tags=('active',))

        act = sum(1 for t in self.trackers.values() if t.running)
        lg = len(self.session_logs)
        self.status_bar.config(text=f"Active: {act}; Logged: {lg}")

    def start_session(self):
        stu = self.student_cb.get()
        cyc = self.cycle_cb.get()
        if not stu:
            messagebox.showerror("Error", "Select a student")
            return
        if self.trackers[cyc].running:
            messagebox.showerror("Error", f"{cyc} already running")
            return
        if any(t.running and t.current_student == stu for t in self.trackers.values()):
            messagebox.showerror("Error", f"{stu} already cycling")
            return
        self.trackers[cyc].start(stu)
        self.update_ui()

    def stop_session(self):
        cyc = self.cycle_cb.get()
        tr = self.trackers[cyc]
        if not tr.running:
            return
        et = time.time()
        self.session_logs.append({
            'cycle': cyc,
            'student': tr.current_student,
            'start': tr.start_time,
            'end': et,
            'duration': et - tr.start_time,
            'kwh': tr.total_voltage / 1000.0
        })
        tr.stop()
        self.update_ui()

    def reset_all_sessions(self):
        for t in self.trackers.values():
            t.stop()
        self.session_logs.clear()
        self.update_ui()

    def show_leaderboard(self):
        Leaderboard().show()

    def open_settings(self):
        pwd = simpledialog.askstring("Password Required", "Enter settings password:", show='*')
        if pwd != "admin123":
            messagebox.showerror("Access Denied", "Incorrect password")
            return

        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")

        student_group = ttk.LabelFrame(settings_window, text="Student List", padding=10)
        student_group.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        listbox = tk.Listbox(student_group)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for s in self.students:
            listbox.insert(tk.END, s)

        btn_frame = ttk.Frame(student_group)
        btn_frame.pack(side=tk.RIGHT, padx=5)

        def add_student():
            name = simpledialog.askstring("Add Student", "Enter name:")
            if name and name not in self.students:
                self.students.append(name)
                listbox.insert(tk.END, name)
                self.save_students()

        def remove_student():
            selected = listbox.curselection()
            if selected:
                idx = selected[0]
                self.students.pop(idx)
                listbox.delete(idx)
                self.save_students()

        ttk.Button(btn_frame, text="Add", command=add_student).pack(pady=2)
        ttk.Button(btn_frame, text="Remove", command=remove_student).pack(pady=2)

        ttk.Button(settings_window, text="OK", command=settings_window.destroy).pack(pady=5)


# Run app
if __name__ == "__main__":
    root = tk.Tk()
    app = EnergyApp(root)
    root.mainloop()
