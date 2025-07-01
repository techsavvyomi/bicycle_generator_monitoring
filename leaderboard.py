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
        self.columns = ("Student", "Total Energy (kWh)", "Sessions")
        self.tree = ttk.Treeview(self.top, columns=self.columns, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.W)

        self.scrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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

        self.tree["columns"] = ["Cycle", "Start", "End", "Duration (s)", "Energy (kWh)"]
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.W)

        for row in filtered:
            start = row['Start'].split(' ')[1]  # HH:MM:SS
            end = row['End'].split(' ')[1] if row['End'] else ""
            self.tree.insert("", tk.END, values=(
                row['Cycle'],
                start,
                end,
                int(row['Duration (s)']),
                float(row['Energy (kWh)'])
            ))

    def _refresh_aggregated_view(self):
        """Show total energy per student, including those with zero"""
        energy_map = defaultdict(float)
        session_count = defaultdict(int)

        # Count energy and sessions
        for row in self.full_data:
            student = row.get('Student', 'Unknown')
            energy = float(row.get('Energy (kWh)', 0))
            energy_map[student] += energy
            session_count[student] += 1

        # Ensure all students appear, even with zero energy
        for student in sorted(self.all_students):
            energy = energy_map.get(student, 0)
            count = session_count.get(student, 0)
            self.tree.insert("", tk.END, values=(
                student,
                f"{energy:.3f}",
                count
            ))

        # Optional: sort by energy descending
        children = self.tree.get_children('')
        sorted_children = sorted(
            children,
            key=lambda child: float(self.tree.item(child)['values'][1]),
            reverse=True
        )
        for index, child in enumerate(sorted_children):
            self.tree.move(child, '', index)
