import ctypes
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QCalendarWidget, QFrame, QTabWidget, QPushButton, 
                               QToolButton, QMenu, QGridLayout, QWidgetAction,
                               QListWidget, QListWidgetItem, QLineEdit)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextCharFormat, QColor, QCursor
from config import Config
from .styles import BASECAMP_QSS

class StatsWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        
        self.setWindowTitle("Basecamp Tracking History")
        self.setFixedSize(620, 520) 
        self.setObjectName("stats_main_window") 
        self.setStyleSheet(BASECAMP_QSS)

        # Load all exercises into memory once
        self.all_exercises = Config.get_exercises()

        self.setup_ui()
        self.update_stats(QDate.currentDate())
        
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
        
        self.setup_stats_tab()
        self.setup_exercise_tab()

    # ==========================================
    # TAB 1: STATS & CALENDAR
    # ==========================================
    def setup_stats_tab(self):
        self.stats_tab = QWidget()
        self.stats_tab_layout = QHBoxLayout(self.stats_tab)
        self.stats_tab_layout.setContentsMargins(15, 15, 15, 15)
        self.stats_tab_layout.setSpacing(20)
        self.tabs.addTab(self.stats_tab, "Stats")

        # --- Left Side (Calendar) ---
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
        self.header_layout.addWidget(self.btn_year); self.header_layout.addStretch(); self.header_layout.addWidget(self.btn_next)
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
        
        self.btn_today = QPushButton("Jump to Today")
        self.btn_today.setObjectName("btn_today")
        self.btn_today.clicked.connect(self.jump_to_today)
        self.left_panel.addWidget(self.btn_today)
        
        self.stats_tab_layout.addLayout(self.left_panel)

        # --- Right Side (Stats Frame) ---
        self.stats_frame = QFrame()
        self.stats_frame.setObjectName("bg_frame")
        self.stats_f_layout = QVBoxLayout(self.stats_frame)
        self.stats_f_layout.setSpacing(15)
        
        self.date_label = QLabel("Loading..."); self.date_label.setObjectName("header_text")
        self.water_label = QLabel("💧 Water: 0ml"); self.water_label.setObjectName("task_text")
        self.screen_label = QLabel("⏱️ Screen Time: 0h 0m"); self.screen_label.setObjectName("task_text")
        self.exercise_label = QLabel("🏃‍♂️ Exercises: 0"); self.exercise_label.setObjectName("task_text")
        
        self.stats_f_layout.addWidget(self.date_label); self.stats_f_layout.addWidget(self.water_label)
        self.stats_f_layout.addWidget(self.screen_label); self.stats_f_layout.addWidget(self.exercise_label)
        self.stats_f_layout.addStretch()
        
        self.stats_tab_layout.addWidget(self.stats_frame)
        self.update_header_labels(self.calendar.yearShown(), self.calendar.monthShown())

    # ==========================================
    # TAB 2: EXERCISE MANAGER
    # ==========================================
    def setup_exercise_tab(self):
        self.exercise_tab = QWidget()
        self.ex_main_layout = QVBoxLayout(self.exercise_tab)
        self.ex_main_layout.setContentsMargins(20, 20, 20, 20)
        
        self.lists_layout = QHBoxLayout()
        
        # --- Left List ---
        self.pool_layout = QVBoxLayout()
        self.pool_layout.addWidget(QLabel("AVAILABLE POOL"))
        self.available_list = QListWidget()
        self.available_list.itemSelectionChanged.connect(self.on_exercise_selected) 
        self.pool_layout.addWidget(self.available_list)
        self.lists_layout.addLayout(self.pool_layout)

        # --- Middle Buttons ---
        self.mid_layout = QVBoxLayout()
        self.mid_layout.addStretch()
        
        self.btn_add = QPushButton(" >> ")
        self.btn_add.clicked.connect(self.move_to_selected)
        self.btn_remove = QPushButton(" << ")
        self.btn_remove.clicked.connect(self.move_to_available)
        
        self.btn_save_rotation = QPushButton("Save Rotation")
        self.btn_save_rotation.setObjectName("btn_done") 
        self.btn_save_rotation.clicked.connect(self.save_rotation)

        self.mid_layout.addWidget(self.btn_add)
        self.mid_layout.addWidget(self.btn_remove)
        self.mid_layout.addSpacing(20)
        self.mid_layout.addWidget(self.btn_save_rotation)
        self.mid_layout.addStretch()
        self.lists_layout.addLayout(self.mid_layout)

        # --- Right List ---
        self.selected_layout = QVBoxLayout()
        self.selected_layout.addWidget(QLabel("ACTIVE ROTATION"))
        self.selected_list = QListWidget()
        self.selected_list.itemSelectionChanged.connect(self.on_exercise_selected) 
        self.selected_layout.addWidget(self.selected_list)
        self.lists_layout.addLayout(self.selected_layout)

        # Populate lists based on JSON 'is_active' flag
        for ex in self.all_exercises:
            display_label = self.format_exercise_label(ex)
            item = QListWidgetItem(display_label)
            item.setData(Qt.UserRole, ex) 
            
            if ex.get("is_active", False):
                self.selected_list.addItem(item)
            else:
                self.available_list.addItem(item)

        self.ex_main_layout.addLayout(self.lists_layout)

        # --- Bottom Editor Panel ---
        self.editor_frame = QFrame()
        self.editor_frame.setObjectName("bg_frame")
        self.editor_layout = QHBoxLayout(self.editor_frame)
        
        self.edit_name = QLineEdit(); self.edit_name.setPlaceholderText("Name")
        self.edit_sets = QLineEdit(); self.edit_sets.setPlaceholderText("Sets"); self.edit_sets.setFixedWidth(50)
        self.edit_reps = QLineEdit(); self.edit_reps.setPlaceholderText("Reps"); self.edit_reps.setFixedWidth(50)
        self.edit_time = QLineEdit(); self.edit_time.setPlaceholderText("Time (s)"); self.edit_time.setFixedWidth(60)
        
        self.btn_update_ex = QPushButton("Update Details")
        self.btn_update_ex.clicked.connect(self.update_exercise_details)
        
        self.editor_layout.addWidget(QLabel("Edit:")); self.editor_layout.addWidget(self.edit_name)
        self.editor_layout.addWidget(QLabel("Sets:")); self.editor_layout.addWidget(self.edit_sets)
        self.editor_layout.addWidget(QLabel("Reps:")); self.editor_layout.addWidget(self.edit_reps)
        self.editor_layout.addWidget(QLabel("Sec:")); self.editor_layout.addWidget(self.edit_time)
        self.editor_layout.addStretch(); self.editor_layout.addWidget(self.btn_update_ex)
        
        self.ex_main_layout.addWidget(self.editor_frame)
        self.tabs.addTab(self.exercise_tab, "Exercise")

    # ==========================================
    # LOGIC: EXERCISE MANAGEMENT
    # ==========================================
    def format_exercise_label(self, ex_dict):
        name = ex_dict.get("name", "Unknown")
        sets, reps, time_sec = ex_dict.get("sets"), ex_dict.get("reps"), ex_dict.get("time_sec")
        if time_sec: return f"{name} ({time_sec} sec)"
        elif sets and reps: return f"{name} ({sets}x{reps})"
        return name

    def get_all_exercises_from_ui(self):
        """Rebuilds the master list directly from the UI to prevent PySide memory severing."""
        current_exercises = []
        
        # Read the Available Pool
        for i in range(self.available_list.count()):
            ex = self.available_list.item(i).data(Qt.UserRole)
            ex["is_active"] = False
            current_exercises.append(ex)
            
        # Read the Active Rotation
        for i in range(self.selected_list.count()):
            ex = self.selected_list.item(i).data(Qt.UserRole)
            ex["is_active"] = True
            current_exercises.append(ex)
            
        return current_exercises

    def on_exercise_selected(self):
        sender_list = self.sender()
        if not sender_list: return

        # Exclusive selection logic
        if sender_list == self.available_list:
            self.selected_list.clearSelection()
            self.selected_list.setCurrentItem(None)
        else:
            self.available_list.clearSelection()
            self.available_list.setCurrentItem(None)

        item = sender_list.currentItem()
        if not item: return

        ex_dict = item.data(Qt.UserRole)
        self.edit_name.setText(str(ex_dict.get("name", "")))
        self.edit_sets.setText(str(ex_dict.get("sets") or ""))
        self.edit_reps.setText(str(ex_dict.get("reps") or ""))
        self.edit_time.setText(str(ex_dict.get("time_sec") or ""))

    def update_exercise_details(self):
        item = self.available_list.currentItem() or self.selected_list.currentItem()
        if not item: return

        ex_dict = item.data(Qt.UserRole)
        ex_dict["name"] = self.edit_name.text()
        
        def parse_int(text): 
            return int(text) if text.strip().isdigit() else None
            
        ex_dict["sets"] = parse_int(self.edit_sets.text())
        ex_dict["reps"] = parse_int(self.edit_reps.text())
        ex_dict["time_sec"] = parse_int(self.edit_time.text())

        item.setText(self.format_exercise_label(ex_dict))
        item.setData(Qt.UserRole, ex_dict)
        
        # Pull directly from UI state and save
        self.all_exercises = self.get_all_exercises_from_ui()
        Config.save_exercises(self.all_exercises)

    def move_to_selected(self):
        for item in self.available_list.selectedItems():
            ex_dict = item.data(Qt.UserRole)
            ex_dict["is_active"] = True
            self.selected_list.addItem(item.text())
            self.selected_list.item(self.selected_list.count()-1).setData(Qt.UserRole, ex_dict)
            self.available_list.takeItem(self.available_list.row(item))
        self.btn_save_rotation.setText("Save Rotation")

    def move_to_available(self):
        for item in self.selected_list.selectedItems():
            ex_dict = item.data(Qt.UserRole)
            ex_dict["is_active"] = False
            self.available_list.addItem(item.text())
            self.available_list.item(self.available_list.count()-1).setData(Qt.UserRole, ex_dict)
            self.selected_list.takeItem(self.selected_list.row(item))
        self.btn_save_rotation.setText("Save Rotation")

    def save_rotation(self):
        # Rebuild fresh from UI right before saving
        self.all_exercises = self.get_all_exercises_from_ui()
        Config.save_exercises(self.all_exercises)
        self.btn_save_rotation.setText("Saved!")

    # ==========================================
    # LOGIC: STATS & CALENDAR
    # ==========================================
    def update_header_labels(self, y, m): 
        self.btn_month.setText(QDate(y, m, 1).toString("MMMM"))
        self.btn_year.setText(str(y))
        
    def prev_month(self): self.calendar.showPreviousMonth()
    def next_month(self): self.calendar.showNextMonth()
    def jump_to_today(self): 
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.showSelectedDate()
        
    def on_date_selected(self): 
        self.update_stats(self.calendar.selectedDate())

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
        years = [self.calendar.yearShown() + i for i in range(-4, 5)]
        for i, y in enumerate(years):
            b = QPushButton(str(y)); b.setObjectName("grid_btn")
            b.clicked.connect(lambda checked=False, x=y: self.set_calendar_year(x, m))
            l.addWidget(b, i // 3, i % 3)
        a = QWidgetAction(m); a.setDefaultWidget(w); m.addAction(a); m.exec(QCursor.pos())

    def set_calendar_month(self, m, menu): 
        self.calendar.setCurrentPage(self.calendar.yearShown(), m); menu.close()
        
    def set_calendar_year(self, y, menu): 
        self.calendar.setCurrentPage(y, self.calendar.monthShown()); menu.close()

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
            self.water_label.setText("💧 Water: No Data")
            self.screen_label.setText("⏱️ Screen Time: No Data")
            self.exercise_label.setText("🏃‍♂️ Exercises: No Data")