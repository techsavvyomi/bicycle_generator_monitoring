#leaderboard.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QHeaderView
from PyQt5.QtGui import QPalette, QLinearGradient, QColor, QBrush, QFont
import pandas as pd
import warnings

class Leaderboard(QDialog):
    def __init__(self):
        super().__init__()
        self.setModal(True)
        self.setWindowTitle("🏆 Leaderboard")
        self.resize(800, 600)

        # Gradient background
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor('#e0f7fa'))
        grad.setColorAt(1, QColor('#80deea'))
        pal = QPalette()
        pal.setBrush(QPalette.Window, QBrush(grad))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

        self.full_data = pd.DataFrame()

        layout = QVBoxLayout(self)

        # Student filter combo
        self.student_cb = QComboBox()
        self.student_cb.setFont(QFont('Arial', 14))
        self.student_cb.addItem("All Students")
        self.student_cb.currentIndexChanged.connect(self.refresh_leaderboard)
        layout.addWidget(self.student_cb)

        # Leaderboard table
        self.table = QTableWidget(0, 5)
        self.table.setFont(QFont('Arial', 12))
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background: rgba(255,255,255,220); }"
            " QHeaderView::section { background: #004d40; color: white; font-size: 16px; padding: 6px; }"
            " QTableWidget::item { padding: 8px; }"
        )
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        # Suppress date parsing warnings
        warnings.filterwarnings('ignore', "Could not infer format*")
        try:
            df = pd.read_excel("log.xlsx", parse_dates=["Start", "End"])
        except Exception as e:
            print(f"[ERROR] Failed to load leaderboard data: {e}")
            self.full_data = pd.DataFrame()
            self.refresh_leaderboard()
            return

        df = df.dropna(subset=["Start", "End"])
        self.full_data = df

        # Populate student combo
        students = sorted(df['Student'].dropna().unique().tolist())
        self.student_cb.clear()
        self.student_cb.addItem("All Students")
        self.student_cb.addItems(students)

        self.refresh_leaderboard()

    def refresh_leaderboard(self):
        self.table.clearContents()
        selected = self.student_cb.currentText()

        if selected and selected != "All Students":
            # Detailed sessions view
            headers = ["Cycle", "Start", "End", "Duration (s)", "Energy (kWh)"]
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            header.setFixedHeight(40)

            records = self.full_data[self.full_data['Student'] == selected].to_dict('records')
            self.table.setRowCount(len(records))
            for i, rec in enumerate(records):
                cycle = rec.get('Cycle', '')
                start = rec['Start'].strftime('%H:%M:%S')
                end = rec['End'].strftime('%H:%M:%S')
                duration = int((rec['End'] - rec['Start']).total_seconds())
                energy = rec.get('Energy (kWh)', 0.0)
                values = [cycle, start, end, str(duration), f"{energy:.3f}"]
                for j, val in enumerate(values):
                    item = QTableWidgetItem(val)
                    item.setFont(QFont('Arial', 12))
                    self.table.setItem(i, j, item)
        else:
            # Aggregated leaderboard view
            headers = ["Student", "Total Energy (kWh)", "Sessions"]
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            header.setFixedHeight(40)

            if self.full_data.empty:
                self.table.setRowCount(0)
                return

            agg = self.full_data.groupby('Student').agg(
                Sessions=pd.NamedAgg(column='Student', aggfunc='count'),
                TotalEnergy=pd.NamedAgg(column='Energy (kWh)', aggfunc='sum')
            ).reset_index().sort_values(by='TotalEnergy', ascending=False)

            self.table.setRowCount(len(agg))
            for i, row in enumerate(agg.itertuples(index=False)):
                vals = [row.Student, f"{row.TotalEnergy:.3f}", str(row.Sessions)]
                for j, val in enumerate(vals):
                    item = QTableWidgetItem(val)
                    if j == 0:
                        item.setFont(QFont('Arial', 12, QFont.Bold))
                    self.table.setItem(i, j, item)

    def show(self):
        self.load_data()
        super().exec_()
