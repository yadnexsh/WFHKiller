import ctypes
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QCalendarWidget, QFrame, QTabWidget, QPushButton, 
                               QToolButton, QMenu, QGridLayout, QWidgetAction)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextCharFormat, QColor, QCursor
from config import Config
from .styles import BASECAMP_QSS

class StatsWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        
        self.setWindowTitle("Basecamp Tracking History")
        self.setFixedSize(580, 400) # Slightly taller to fit the Today button and tabs
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
        # 1. Main Layout & Tab Widget
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # 2. The Stats Tab
        self.stats_tab = QWidget()
        self.stats_layout = QHBoxLayout(self.stats_tab)
        self.stats_layout.setContentsMargins(15, 15, 15, 15)
        self.stats_layout.setSpacing(20)
        
        self.tabs.addTab(self.stats_tab, "Stats")

        # --- Left Side: Custom Header + Calendar + Today Button ---
        self.left_panel = QVBoxLayout()
        self.left_panel.setSpacing(10)

        # Custom Header
        self.header_layout = QHBoxLayout()
        self.btn_prev = QToolButton()
        self.btn_prev.setText("<")
        self.btn_prev.clicked.connect(self.prev_month)
        
        self.btn_month = QPushButton("Month")
        self.btn_month.setObjectName("header_dropdown")
        self.btn_month.clicked.connect(self.show_month_menu)
        
        self.lbl_sep = QLabel("|")
        self.lbl_sep.setAlignment(Qt.AlignCenter)
        
        self.btn_year = QPushButton("Year")
        self.btn_year.setObjectName("header_dropdown")
        self.btn_year.clicked.connect(self.show_year_menu)
        
        self.btn_next = QToolButton()
        self.btn_next.setText(">")
        self.btn_next.clicked.connect(self.next_month)

        self.header_layout.addWidget(self.btn_prev)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_month)
        self.header_layout.addWidget(self.lbl_sep)
        self.header_layout.addWidget(self.btn_year)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_next)
        
        self.left_panel.addLayout(self.header_layout)

        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setNavigationBarVisible(False) # Hides the native Qt header
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        
        standard_format = QTextCharFormat()
        standard_format.setForeground(QColor("#e0e0e0"))
        for day in [Qt.Monday, Qt.Tuesday, Qt.Wednesday, Qt.Thursday, Qt.Friday, Qt.Saturday]:
            self.calendar.setWeekdayTextFormat(day, standard_format)

        sunday_format = QTextCharFormat()
        sunday_format.setForeground(QColor("#ff4a4a")) 
        self.calendar.setWeekdayTextFormat(Qt.Sunday, sunday_format)

        self.calendar.selectionChanged.connect(self.on_date_selected) 
        self.calendar.currentPageChanged.connect(self.update_header_labels)
        self.left_panel.addWidget(self.calendar)

        # Today Button
        self.btn_today = QPushButton("Jump to Today")
        self.btn_today.setObjectName("btn_today")
        self.btn_today.clicked.connect(self.jump_to_today)
        self.left_panel.addWidget(self.btn_today)

        self.stats_layout.addLayout(self.left_panel)

        # --- Right Side: Stats Panel ---
        self.stats_frame = QFrame()
        self.stats_frame.setObjectName("bg_frame") 
        self.stats_frame_layout = QVBoxLayout(self.stats_frame)
        self.stats_frame_layout.setSpacing(15)

        self.date_label = QLabel("Loading...")
        self.date_label.setObjectName("header_text")

        self.water_label = QLabel("💧 Water: 0ml")
        self.water_label.setObjectName("task_text")

        self.screen_label = QLabel("⏱️ Screen Time: 0h 0m")
        self.screen_label.setObjectName("task_text")

        self.exercise_label = QLabel("🏃‍♂️ Exercises: 0")
        self.exercise_label.setObjectName("task_text")

        self.stats_frame_layout.addWidget(self.date_label)
        self.stats_frame_layout.addWidget(self.water_label)
        self.stats_frame_layout.addWidget(self.screen_label)
        self.stats_frame_layout.addWidget(self.exercise_label)
        self.stats_frame_layout.addStretch() 

        self.stats_layout.addWidget(self.stats_frame)

        # Initialize labels
        self.update_header_labels(self.calendar.yearShown(), self.calendar.monthShown())

    # --- Interaction Logic ---
    def update_header_labels(self, year, month):
        month_name = QDate(year, month, 1).toString("MMMM")
        self.btn_month.setText(month_name)
        self.btn_year.setText(str(year))

    def prev_month(self):
        self.calendar.showPreviousMonth()

    def next_month(self):
        self.calendar.showNextMonth()

    def jump_to_today(self):
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.calendar.showSelectedDate()

    def on_date_selected(self):
        self.update_stats(self.calendar.selectedDate())

    # --- Custom Grid Menus ---
    def show_month_menu(self):
        menu = QMenu(self)
        menu.setObjectName("grid_menu")
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for i, m_str in enumerate(months):
            btn = QPushButton(m_str)
            btn.setObjectName("grid_btn")
            # i+1 converts index 0-11 to month 1-12
            btn.clicked.connect(lambda checked=False, m=i+1: self.set_calendar_month(m, menu))
            layout.addWidget(btn, i // 3, i % 3) # Creates a 4x3 grid

        action = QWidgetAction(menu)
        action.setDefaultWidget(widget)
        menu.addAction(action)
        menu.exec(QCursor.pos())

    def show_year_menu(self):
        menu = QMenu(self)
        menu.setObjectName("grid_menu")
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        current_year = self.calendar.yearShown()
        # Create a 3x3 grid around the currently viewed year
        years = [current_year + i for i in range(-4, 5)] 
        
        for i, y in enumerate(years):
            btn = QPushButton(str(y))
            btn.setObjectName("grid_btn")
            btn.clicked.connect(lambda checked=False, year=y: self.set_calendar_year(year, menu))
            layout.addWidget(btn, i // 3, i % 3) # Creates a 3x3 grid

        action = QWidgetAction(menu)
        action.setDefaultWidget(widget)
        menu.addAction(action)
        menu.exec(QCursor.pos())

    def set_calendar_month(self, month, menu):
        self.calendar.setCurrentPage(self.calendar.yearShown(), month)
        menu.close()

    def set_calendar_year(self, year, menu):
        self.calendar.setCurrentPage(year, self.calendar.monthShown())
        menu.close()

    # --- Stats Fetching ---
    def update_stats(self, qdate):
        date_str = qdate.toString("yyyy-MM-dd") 
        self.date_label.setText(f"STATS FOR: {date_str}")

        stats = self.db.get_stats_for_date(date_str)

        if stats:
            water = stats['water_ml']
            screen_sec = stats['screen_time_sec']
            exercises = stats['exercises_completed']
            hours = screen_sec // 3600
            minutes = (screen_sec % 3600) // 60
            self.water_label.setText(f"💧 Water: {water}ml / {Config.DAILY_WATER_TARGET_ML}ml")
            self.screen_label.setText(f"⏱️ Screen Time: {hours}h {minutes}m")
            self.exercise_label.setText(f"🏃‍♂️ Exercises: {exercises} sets")
        else:
            self.water_label.setText("💧 Water: No Data")
            self.screen_label.setText("⏱️ Screen Time: No Data")
            self.exercise_label.setText("🏃‍♂️ Exercises: No Data")