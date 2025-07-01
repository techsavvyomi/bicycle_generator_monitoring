import tkinter as tk
from tkinter import ttk, messagebox
import csv
from collections import defaultdict

class Leaderboard:
    def __init__(self):
        self.top = tk.Toplevel()
        self.top.title("🏆 Leaderboard")
        self.top.geometry("800x600")
        self.top.resizable(True, True)

        # Data
        self.full_data = []
        self.all_students = []

        # Load data and UI
        self.load_all_students()  # First load all known students
        self.load_session_data()  # Then load session logs
        self.create_widgets()
        self.refresh_leaderboard()

    def create_widgets(self):
        # Student Filter Combobox
        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(
            self.top,
            textvariable=self.student_var,
            values=["All Students"] + self.all_students
        )
        self.student_combo.pack(pady=10, padx=20, fill=tk.X)
        self.student_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_leaderboard())

        # Treeview Table
        self.tree = ttk.Treeview(self.top, show="headings")
        self.scrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

    def load_all_students(self):
        """Load all known students from students.csv"""
        try:
            with open("students.csv", newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.all_students = [row['Name'] for row in reader]
        except Exception as e:
            messagebox.showwarning("No Students", "Could not load student list.")
            self.all_students = []

    def load_session_data(self):
        """Load session logs from CSV"""
        try:
            with open("session_logs.csv", newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.full_data = list(reader)
        except FileNotFoundError:
            self.full_data = []

    def refresh_leaderboard(self):
        """Update table based on selected student"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        selected = self.student_var.get()

        if selected != "All Students":
            self._refresh_individual_view(selected)
        else:
            self._refresh_aggregated_view()

    def _refresh_individual_view(self, student_name):
        """Show individual session logs for one student"""
        filtered = [
            row for row in self.full_data
            if row.get('Student') == student_name
        ]

        # Set dynamic columns
        columns = ["Cycle", "Start", "End", "Duration (s)", "Energy (kWh)"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.W)

        # Insert session rows
        for row in filtered:
            start = ""
            end = ""
            duration = row.get('Duration (s)', '0')
            energy = row.get('Energy (kWh)', '0.0')

            if row.get('Start'):
                try:
                    start = row['Start'].split(" ")[1]  # Extract time part
                except IndexError:
                    start = "Invalid Time"

            if row.get('End'):
                try:
                    end = row['End'].split(" ")[1]
                except IndexError:
                    end = ""

            self.tree.insert("", tk.END, values=(
                row.get('Cycle', 'Unknown'),
                start,
                end,
                int(duration),
                float(energy)
            ))

    def _refresh_aggregated_view(self):
        """Show total energy per student, including those with zero sessions"""
        energy_map = defaultdict(float)
        session_count = defaultdict(int)

        # Aggregate energy and session count
        for row in self.full_data:
            student = row.get("Student", "Unknown")
            try:
                energy = float(row.get("Energy (kWh)", 0))
            except ValueError:
                continue
            energy_map[student] += energy
            session_count[student] += 1

        # Set dynamic columns
        columns = ["Student", "Total Energy (kWh)", "Sessions"]
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.W)

        # Add all students
        for student in sorted(self.all_students):
            energy = energy_map.get(student, 0)
            count = session_count.get(student, 0)
            self.tree.insert("", tk.END, values=(
                student,
                f"{energy:.3f}",
                count
            ))

        # Optional: sort by kWh descending
        children = self.tree.get_children('')
        try:
            sorted_children = sorted(
                children,
                key=lambda child: float(self.tree.item(child)['values'][1]),
                reverse=True
            )
            for index, child in enumerate(sorted_children):
                self.tree.move(child, '', index)
        except:
            pass  # Skip sorting if some values can't be parsed

    def show(self):
        self.top.grab_set()
        self.top.wait_window()
