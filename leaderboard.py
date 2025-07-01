import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import os
from datetime import datetime


class Leaderboard:
    def __init__(self):
        self.top = tk.Toplevel()
        self.top.title("🏆 Leaderboard")
        self.top.geometry("800x600")
        self.top.resizable(True, True)

        # Data
        self.full_data = pd.DataFrame()

        # UI
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Student Filter Combobox
        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(self.top, textvariable=self.student_var)
        self.student_combo.pack(pady=10, padx=20, fill=tk.X)
        self.student_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_leaderboard())

        # Treeview Table
        columns = ("Student", "Total Energy (kWh)", "Sessions")
        self.tree = ttk.Treeview(self.top, columns=columns, show="headings", selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.W)

        self.scrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_data(self):
        try:
            log_path = "session_logs.csv"
            if not os.path.exists(log_path):
                messagebox.showinfo("Info", "No session logs found.")
                return

            self.full_data = pd.read_csv(log_path)
            self.full_data['Start'] = pd.to_datetime(self.full_data['Start'])
            self.full_data['End'] = pd.to_datetime(self.full_data['End'])

            students = ["All Students"] + sorted(self.full_data['Student'].dropna().unique().tolist())
            self.student_combo['values'] = students
            self.student_combo.current(0)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load leaderboard data:\n{e}")
            self.full_data = pd.DataFrame()

        self.refresh_leaderboard()


    def refresh_leaderboard(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        selected = self.student_var.get()

        if selected and selected != "All Students":
            filtered = self.full_data[self.full_data['Student'] == selected]
            for _, row in filtered.iterrows():
                values = (
                    row['Cycle'],
                    row['Start'].strftime('%H:%M:%S'),
                    row['End'].strftime('%H:%M:%S'),
                    int((row['End'] - row['Start']).total_seconds()),
                    f"{row['Energy (kWh)']:.3f}"
                )
                self.tree.insert("", tk.END, values=values)
        else:
            agg = self.full_data.groupby('Student').agg(
                Sessions=('Student', 'count'),
                TotalEnergy=('Energy (kWh)', 'sum')
            ).reset_index().sort_values(by='TotalEnergy', ascending=False)

            for _, row in agg.iterrows():
                self.tree.insert("", tk.END, values=(
                    row['Student'],
                    f"{row['TotalEnergy']:.3f}",
                    row['Sessions']
                ))

    def show(self):
        self.top.grab_set()
        self.top.wait_window()
