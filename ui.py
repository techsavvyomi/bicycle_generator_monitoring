from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox,
    QDialog, QListWidget, QLineEdit, QFormLayout, QGroupBox, QDialogButtonBox,
    QStatusBar, QHeaderView, QInputDialog
)
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QItemSelection, QItemSelectionModel
from PyQt5.QtGui import QBrush, QColor, QPalette, QLinearGradient
import pandas as pd
import time
from datetime import datetime
from wifi_listener import WifiPoller
from PyQt5.QtCore import QThread
from tracker import SessionTracker
from leaderboard import Leaderboard

class EnergyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚴‍♂️ Bicycle Energy Tracker")
        self.resize(1280, 720)
        self.poller_thread = QThread()
        self.poller = WifiPoller()
        self.poller.moveToThread(self.poller_thread)
        self.poller_thread.started.connect(self.poller.run)
        self.poller.data_received.connect(self.handle_new_data)
        self.poller_thread.start()
        # Fade-in animation
        self.setWindowOpacity(0)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(800)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()

        # Gradient background
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor('#e0f7fa'))
        grad.setColorAt(1, QColor('#80deea'))
        pal = QPalette()
        pal.setBrush(QPalette.Window, grad)
        self.setAutoFillBackground(True)
        self.setPalette(pal)

        # Data
        self.students = self.load_students()
        self.trackers = {f"Cycle {i+1}": SessionTracker(f"Cycle {i+1}") for i in range(8)}
        self.session_logs = []

        # wifi json reader


        # UI
        self.setup_ui()
        self.update_ui()

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
            df = pd.read_excel("config.xlsx")
            return df['Name'].tolist()
        except:
            return []

    def save_students(self):
        pd.DataFrame({'Name': self.students}).to_excel("config.xlsx", index=False)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15,15,15,15)
        layout.setSpacing(12)

        # Controls
        grp = QGroupBox("Session Controls")
        grp.setStyleSheet("QGroupBox{font-size:20px;color:#00796b;} QLabel{font-size:18px;} QComboBox{font-size:18px;padding:6px;border:1px solid #004d40;}")
        h = QHBoxLayout(grp)
        h.setSpacing(20)
        h.addWidget(QLabel("Select Student:"))
        self.student_cb = QComboBox(); self.student_cb.addItems(self.students)
        h.addWidget(self.student_cb)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedHeight(30)
        self.refresh_btn.setStyleSheet("background:#0288d1; color:white; border-radius:4px; font-size:14px;")
        self.refresh_btn.clicked.connect(self.refresh_students)
        h.addWidget(self.refresh_btn)
        h.addWidget(QLabel("Select Bicycle:"))
        self.cycle_cb = QComboBox(); self.cycle_cb.addItems(list(self.trackers.keys()))
        h.addWidget(self.cycle_cb)
        layout.addWidget(grp)

        # Buttons
        btns = QWidget(); hb = QHBoxLayout(btns); hb.setSpacing(15)
        self.start_btn = QPushButton("Start"); hb.addWidget(self.start_btn)
        self.stop_btn  = QPushButton("Stop");  hb.addWidget(self.stop_btn)
        self.reset_btn = QPushButton("Reset All"); hb.addWidget(self.reset_btn)
        self.board_btn = QPushButton("🏆 Leaderboard"); hb.addWidget(self.board_btn)
        self.sett_btn  = QPushButton("⚙️ Settings");  hb.addWidget(self.sett_btn)
        for btn,color,fn in [
            (self.start_btn, '#388e3c', self.start_session),
            (self.stop_btn,  '#d32f2f', self.stop_session),
            (self.reset_btn,'#1976d2', self.reset_all_sessions),
            (self.board_btn,"#AC7F0F", self.show_leaderboard),
            (self.sett_btn, '#7b1fa2', self.open_settings)
        ]:
            btn.setMinimumHeight(45)
            btn.setStyleSheet(f"QPushButton{{background:{color};color:white;border-radius:6px;font-size:16px;}} QPushButton:hover{{background:#fff;color:{color};}}")
            btn.clicked.connect(fn)
            btn.pressed.connect(lambda b=btn: self.animate_button(b))
        layout.addWidget(btns)

                # Label before table
        lbl = QLabel("Click the left side numbers to select and unselect the session")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size:18px; color:#004d40; padding:2px;")
        layout.addWidget(lbl)




        # Table
        self.live_table = QTableWidget(0,6)
        self.live_table.setHorizontalHeaderLabels([
            "Cycle","Student","Start","End","Duration","kWh"
        ])
        self.live_table.setAlternatingRowColors(True)
        self.live_table.setStyleSheet(
            "QTableWidget { font-size:15px; background: rgba(255,255,255,204); }"
            " QHeaderView::section { background: #004d40; color: white; padding:4px; }"
        )
        hdr = self.live_table.horizontalHeader()
        for i in range(6): hdr.setSectionResizeMode(i, QHeaderView.Stretch)
        self.live_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.live_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.live_table.cellClicked.connect(self.on_cell_clicked)
        self.live_table.itemSelectionChanged.connect(self.on_table_selection)
        layout.addWidget(self.live_table)
        # Selection info
        self.sel_label = QLabel("Selected: None"); self.sel_label.setStyleSheet("font-size:16px;color:#004d40;")
        layout.addWidget(self.sel_label)

        # Status bar
        self.status = QStatusBar(); self.status.setStyleSheet("font-size:14px;background:#004d40;color:white;")
        layout.addWidget(self.status)

        # Timer
        self.timer = QTimer(self); self.timer.timeout.connect(self.update_ui); self.timer.start(1000)

        # Triggers
        self.cycle_cb.currentTextChanged.connect(self.update_buttons)
        self.student_cb.currentTextChanged.connect(self.update_buttons)
        self.live_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.live_table.setSelectionBehavior(QAbstractItemView.SelectItems)

        self.live_table.cellClicked.connect(self.on_cell_clicked)
        self.update_buttons()

    def refresh_students(self):
        self.students = self.load_students()
        self.student_cb.clear()
        self.student_cb.addItems(self.students)
        self.status.showMessage("Student list refreshed", 3000)

    def on_cell_clicked(self, row, col):
        model = self.live_table.selectionModel()
        table_model = self.live_table.model()

        # Build the selection range for this row
        first_index = table_model.index(row, 0)
        last_index = table_model.index(row, self.live_table.columnCount() - 1)
        selRange = QItemSelection(first_index, last_index)

        # Check if this row is already selected
        is_selected = all(model.isSelected(table_model.index(row, c))
                          for c in range(self.live_table.columnCount()))

        if is_selected:
            model.select(selRange, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
        else:
            # Clear previous selection and select this row
            model.clearSelection()
            model.select(selRange, QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def on_table_selection(self):
        rows = sorted(set(idx.row() for idx in self.live_table.selectedIndexes()))
        if not rows:
            self.sel_label.setText("Selected: None")
            return
        info = []
        for r in rows:
            c = self.live_table.item(r, 0).text()
            s = self.live_table.item(r, 1).text()
            info.append(f"{c}:{s}")
        self.sel_label.setText("Selected: " + ", ".join(info))
        last = rows[-1]
        self.cycle_cb.setCurrentText(self.live_table.item(last, 0).text())
        self.student_cb.setCurrentText(self.live_table.item(last, 1).text())

    def animate_button(self, btn):
        anim = QPropertyAnimation(btn, b"geometry", self)
        r = btn.geometry()
        anim.setDuration(150)
        anim.setStartValue(r)
        anim.setKeyValueAt(0.5, r.adjusted(2,2,-2,-2))
        anim.setEndValue(r)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()

    def update_all_trackers(self, data):
        for cyc, tr in self.trackers.items():
            if cyc in data:
                tr.update_voltage(data)

    def update_buttons(self):
        cyc = self.cycle_cb.currentText()
        run = self.trackers[cyc].running
        self.start_btn.setEnabled(not run)
        self.stop_btn.setEnabled(run)

    def update_ui(self):
        preserved = [
            (self.live_table.item(r, 0).text(), self.live_table.item(r, 1).text())
            for r in set(idx.row() for idx in self.live_table.selectedIndexes())
        ]
        self.live_table.setRowCount(0)
        for log in self.session_logs:
            r = self.live_table.rowCount()
            self.live_table.insertRow(r)
            vals = [
                log['cycle'], log['student'],
                datetime.fromtimestamp(log['start']).strftime('%H:%M:%S'),
                datetime.fromtimestamp(log['end']).strftime('%H:%M:%S'),
                f"{int(log['duration'])}s", f"{log['kwh']:.3f}"
            ]
            for i, v in enumerate(vals):
                self.live_table.setItem(r, i, QTableWidgetItem(v))
        for cyc, tr in self.trackers.items():
            if tr.running:
                r = self.live_table.rowCount()
                self.live_table.insertRow(r)
                vals = [
                    cyc, tr.current_student,
                    datetime.fromtimestamp(tr.start_time).strftime('%H:%M:%S'),
                    "", f"{int(time.time() - tr.start_time)}s", f"{tr.total_voltage/1000:.3f}"
                ]
                for i, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    it.setBackground(QBrush(QColor(255,255,200)))
                    self.live_table.setItem(r, i, it)
        for row in range(self.live_table.rowCount()):
            key = (
                self.live_table.item(row, 0).text(),
                self.live_table.item(row, 1).text()
            )
            if key in preserved:
                self.live_table.selectRow(row)
        act = sum(1 for t in self.trackers.values() if t.running)
        lg = len(self.session_logs)
        self.status.showMessage(f"Active: {act}; Logged: {lg}")
        self.update_buttons()

    def start_session(self):
        stu = self.student_cb.currentText()
        cyc = self.cycle_cb.currentText()
        if not stu:
            QMessageBox.critical(self, "Error", "Select a student")
            return
        if self.trackers[cyc].running:
            QMessageBox.critical(self, "Error", f"{cyc} already running")
            return
        if any(t.running and t.current_student == stu for t in self.trackers.values()):
            QMessageBox.critical(self, "Error", f"{stu} already cycling")
            return
        self.trackers[cyc].start(stu)
        self.update_ui()

    def stop_session(self):
        cyc = self.cycle_cb.currentText()
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
        text, ok = QInputDialog.getText(
            self, "Password Required", "Enter settings password:", QLineEdit.Password
        )
        if not ok or text != "admin123":
            QMessageBox.critical(self, "Access Denied", "Incorrect password")
            return
        d = QDialog(self)
        d.setWindowTitle("Settings")
        l = QVBoxLayout(d)
        sg = QGroupBox("Student List")
        sl = QVBoxLayout()
        lst = QListWidget()
        lst.addItems(self.students)
        sl.addWidget(lst)
        def add():
            t, ok = QInputDialog.getText(d, "Add Student", "Name:")
            if ok and t and t not in self.students:
                self.students.append(t)
                lst.addItem(t)
                self.save_students()
        def rem():
            i = lst.currentRow()
            if i >= 0:
                self.students.pop(i)
                lst.takeItem(i)
                self.save_students()
        hb = QHBoxLayout()
        pb = QPushButton("Add")
        rb = QPushButton("Remove")
        pb.clicked.connect(add)
        rb.clicked.connect(rem)
        hb.addWidget(pb)
        hb.addWidget(rb)
        sl.addLayout(hb)
        sg.setLayout(sl)
        l.addWidget(sg)
        serg = QGroupBox("wifi Settings")
        serf = QFormLayout(serg)
        pi = QLineEdit()
        bi = QLineEdit()
        serf.addRow("IP:", pi)
        serf.addRow("Port:", bi)
        l.addWidget(serg)
        bb = QDialogButtonBox(QDialogButtonBox.Ok)
        bb.accepted.connect(lambda: d.accept())
        l.addWidget(bb)
        d.exec_()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = EnergyApp()
    w.show()
    sys.exit(app.exec_())
