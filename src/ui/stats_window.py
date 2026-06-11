import ctypes
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QCalendarWidget, QFrame, QTabWidget, QPushButton, 
                               QToolButton, QMenu, QGridLayout, QWidgetAction,
                               QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextCharFormat, QColor, QCursor
from config import Config
from .styles import BASECAMP_QSS

class StatsWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        
        self.setWindowTitle("Basecamp Tracking History")
        self.setFixedSize(620, 450) # Increased size for better list visibility
        self.setObjectName("stats_main_window") 
        self.setStyleSheet(BASECAMP_QSS)

        self.setup_ui()
        self.update_stats(QDate.currentDate())
        
        # Force Windows Native Title Bar to Dark Mode
        try:
            hwnd = int(self.winId())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
        except Exception:
            pass

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # --- TAB 1: STATS ---
        self.setup_stats_tab()
        
        # --- TAB 2: EXERCISE ---
        self.setup_exercise_tab()

    def setup_stats_tab(self):
        self.stats_tab = QWidget()
        self.stats_tab_layout = QHBoxLayout(self.stats_tab)
        self.stats_tab_layout.setContentsMargins(15, 15, 15, 15)
        self.stats_tab_layout.setSpacing(20)
        
        self.tabs.addTab(self.stats_tab, "Stats")

        # Left Side (Calendar)
        self.left_panel = QVBoxLayout()
        self.left_panel.setSpacing(10)

        self.header_layout = QHBoxLayout()
        self.btn_prev = QToolButton(); self.btn_prev.setText("<"); self.btn_prev.clicked.connect(self.prev_month)
        self.btn_month = QPushButton("Month"); self.btn_month.setObjectName("header_dropdown"); self.btn_month.clicked.connect(self.show_month_menu)
        self.lbl_sep = QLabel("|"); self.lbl_sep.setAlignment(Qt.AlignCenter)
        self.btn_year = QPushButton("Year"); self.btn_year.setObjectName("header_dropdown"); self.btn_year.clicked.connect(self.show_year_menu)
        self.btn_next = QToolButton(); self.btn_next.setText(">"); self.btn_next.clicked.connect(self.next_month)

        self.header_layout.addWidget(self.btn_prev); self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_month); self.header_layout.addWidget(self.lbl_sep)
        self.header_layout.addWidget(self.btn_year); self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_next)
        self.left_panel.addLayout(self.header_layout)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True); self.calendar.setNavigationBarVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        
        std_fmt = QTextCharFormat(); std_fmt.setForeground(QColor("#e0e0e0"))
        for d in [Qt.Monday, Qt.Tuesday, Qt.Wednesday, Qt.Thursday, Qt.Friday, Qt.Saturday]:
            self.calendar.setWeekdayTextFormat(d, std_fmt)
        sun_fmt = QTextCharFormat(); sun_fmt.setForeground(QColor("#ff4a4a"))
        self.calendar.setWeekdayTextFormat(Qt.Sunday, sun_fmt)

        self.calendar.selectionChanged.connect(self.on_date_selected)
        self.calendar.currentPageChanged.connect(self.update_header_labels)
        self.left_panel.addWidget(self.calendar)

        self.btn_today = QPushButton("Jump to Today"); self.btn_today.setObjectName("btn_today")
        self.btn_today.clicked.connect(self.jump_to_today)
        self.left_panel.addWidget(self.btn_today)
        self.stats_tab_layout.addLayout(self.left_panel)

        # Right Side (Stat Cards)
        self.stats_frame = QFrame(); self.stats_frame.setObjectName("bg_frame")
        self.stats_f_layout = QVBoxLayout(self.stats_frame); self.stats_f_layout.setSpacing(15)
        self.date_label = QLabel("Loading..."); self.date_label.setObjectName("header_text")
        self.water_label = QLabel("💧 Water: 0ml"); self.water_label.setObjectName("task_text")
        self.screen_label = QLabel("⏱️ Screen Time: 0h 0m"); self.screen_label.setObjectName("task_text")
        self.exercise_label = QLabel("🏃‍♂️ Exercises: 0"); self.exercise_label.setObjectName("task_text")
        self.stats_f_layout.addWidget(self.date_label); self.stats_f_layout.addWidget(self.water_label)
        self.stats_f_layout.addWidget(self.screen_label); self.stats_f_layout.addWidget(self.exercise_label)
        self.stats_f_layout.addStretch()
        self.stats_tab_layout.addWidget(self.stats_frame)
        self.update_header_labels(self.calendar.yearShown(), self.calendar.monthShown())

    def setup_exercise_tab(self):
        """Builds the Dual-List Exercise Manager."""
        self.exercise_tab = QWidget()
        self.ex_layout = QHBoxLayout(self.exercise_tab)
        self.ex_layout.setContentsMargins(20, 20, 20, 20)
        self.ex_layout.setSpacing(15)

        # 1. Left List: Available Pool
        self.pool_layout = QVBoxLayout()
        self.pool_layout.addWidget(QLabel("AVAILABLE POOL"))
        self.available_list = QListWidget()
        # Seed with sample exercises
        exercises = ["Squats", "Lunges", "Calf Raises", "Plank", "Pushups", "Burpees", "Mountain Climbers"]
        self.available_list.addItems(exercises)
        self.pool_layout.addWidget(self.available_list)
        self.ex_layout.addLayout(self.pool_layout)

        # 2. Middle: Add/Remove Buttons
        self.mid_layout = QVBoxLayout()
        self.mid_layout.addStretch()
        self.btn_add = QPushButton(" >> ")
        self.btn_add.setToolTip("Add to active rotation")
        self.btn_add.clicked.connect(self.move_to_selected)
        
        self.btn_remove = QPushButton(" << ")
        self.btn_remove.setToolTip("Remove from rotation")
        self.btn_remove.clicked.connect(self.move_to_available)
        
        self.mid_layout.addWidget(self.btn_add)
        self.mid_layout.addWidget(self.btn_remove)
        self.mid_layout.addStretch()
        self.ex_layout.addLayout(self.mid_layout)

        # 3. Right List: Selected Rotation
        self.selected_layout = QVBoxLayout()
        self.selected_layout.addWidget(QLabel("ACTIVE ROTATION"))
        self.selected_list = QListWidget()
        self.selected_layout.addWidget(self.selected_list)
        self.ex_layout.addLayout(self.selected_layout)

        self.tabs.addTab(self.exercise_tab, "Exercise")

    # --- Exercise Logic ---
    def move_to_selected(self):
        for item in self.available_list.selectedItems():
            self.selected_list.addItem(item.text())
            self.available_list.takeItem(self.available_list.row(item))

    def move_to_available(self):
        for item in self.selected_list.selectedItems():
            self.available_list.addItem(item.text())
            self.selected_list.takeItem(self.selected_list.row(item))

    # --- Standard Interaction Logic ---
    def update_header_labels(self, y, m):
        self.btn_month.setText(QDate(y, m, 1).toString("MMMM"))
        self.btn_year.setText(str(y))

    def prev_month(self): self.calendar.showPreviousMonth()
    def next_month(self): self.calendar.showNextMonth()
    def jump_to_today(self):
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.showSelectedDate()

    def on_date_selected(self): self.update_stats(self.calendar.selectedDate())

    def show_month_menu(self):
        m = QMenu(self); m.setObjectName("grid_menu"); w = QWidget(); l = QGridLayout(w)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for i, ms in enumerate(months):
            b = QPushButton(ms); b.setObjectName("grid_btn")
            b.clicked.connect(lambda checked=False, x=i+1: self.set_calendar_month(x, m))
            l.addWidget(b, i // 3, i % 3)
        a = QWidgetAction(m); a.setDefaultWidget(w); m.addAction(a); m.exec(QCursor.pos())

    def show_year_menu(self):
        m = QMenu(self); m.setObjectName("grid_menu"); w = QWidget(); l = QGridLayout(w)
        cy = self.calendar.yearShown()
        years = [cy + i for i in range(-4, 5)]
        for i, y in enumerate(years):
            b = QPushButton(str(y)); b.setObjectName("grid_btn")
            b.clicked.connect(lambda checked=False, x=y: self.set_calendar_year(x, m))
            l.addWidget(b, i // 3, i % 3)
        a = QWidgetAction(m); a.setDefaultWidget(w); m.addAction(a); m.exec(QCursor.pos())

    def set_calendar_month(self, m, menu): self.calendar.setCurrentPage(self.calendar.yearShown(), m); menu.close()
    def set_calendar_year(self, y, menu): self.calendar.setCurrentPage(y, self.calendar.monthShown()); menu.close()

    def update_stats(self, qdate):
        d_str = qdate.toString("yyyy-MM-dd") 
        self.date_label.setText(f"STATS FOR: {d_str}")
        stats = self.db.get_stats_for_date(d_str)
        if stats:
            w, s, e = stats['water_ml'], stats['screen_time_sec'], stats['exercises_completed']
            self.water_label.setText(f"💧 Water: {w}ml / {Config.DAILY_WATER_TARGET_ML}ml")
            self.screen_label.setText(f"⏱️ Screen Time: {s//3600}h {(s%3600)//60}m")
            self.exercise_label.setText(f"🏃‍♂️ Exercises: {e} sets")
        else:
            self.water_label.setText("💧 Water: No Data"); self.screen_label.setText("⏱️ Screen Time: No Data"); self.exercise_label.setText("🏃‍♂️ Exercises: No Data")