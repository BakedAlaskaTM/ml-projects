from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QTextCharFormat
from PyQt6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFrame, QLabel, QDateEdit, QPlainTextEdit,
    QCalendarWidget
)
from datetime import datetime

class EditProjectInfoWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(960)
        self.setFixedHeight(810)
        self.setContentsMargins(40, 40, 40, 40)
        self.setObjectName("editProjectInfoFrame")
        self.setStyleSheet("""
            QFrame#editProjectInfoFrame {
                background-color: white;
                border: 1px solid black;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(40)

        date_layout = QVBoxLayout()
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(0)
        date_label = QLabel("Project Start Date")
        date_label.setStyleSheet("font-size: 36px; border: none")
        self.date_edit = QDateEdit()
        self.date_edit.setFixedWidth(880)
        self.date_edit.setFixedHeight(50)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setStyleSheet("""
            QDateEdit {
                background-color: #ffffff;
                border: 1px solid #18181b;
                border-radius: 10px;
                padding: 6px 44px 6px 12px;
                selection-background-color: #18181b;
                selection-color: #ffffff;
            }
            QDateEdit:focus {
                border: 2px solid #18181b;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 36px;
                border: none;
                border-left: 1px solid #e4e4e7;
            }
            QDateEdit::down-arrow {
                image: url("assets/down-arrow.svg");
                width: 16px;
                height: 16px;
            }
        """)

        calendar = self.date_edit.calendarWidget()
        calendar.setMinimumSize(420, 320)
        calendar.setGridVisible(True)
        calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #ffffff;
                border: 1px solid #d4d4d8;
                border-radius: 10px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #f4f4f5;
                border: none;
                border-bottom: 1px solid #e4e4e7;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                min-height: 44px;
            }
            QCalendarWidget QToolButton {
                background-color: transparent;
                color: #18181b;
                border: none;
                border-radius: 7px;
                padding: 7px 10px;
                font-size: 15px;
                font-weight: 600;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #e4e4e7;
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth,
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                min-width: 28px;
                min-height: 28px;
                padding: 4px;
            }
            QCalendarWidget QToolButton#qt_calendar_monthbutton {
                min-width: 90px;
                padding-right: 10px;
            }
            QCalendarWidget QToolButton#qt_calendar_monthbutton::menu-indicator {
                image: none;
                width: 0px;
            }
            QCalendarWidget QSpinBox {
                background-color: #ffffff;
                color: #18181b;
                border: 1px solid #d4d4d8;
                border-radius: 6px;
                padding: 4px 8px;
                selection-background-color: #18181b;
                selection-color: #ffffff;
            }
            QCalendarWidget QAbstractItemView {
                background-color: #ffffff;
                color: #18181b;
                border: none;
                outline: none;
                gridline-color: #eceff1;
                padding: 8px;
                font-size: 14px;
                selection-background-color: #2563eb;
                selection-color: #ffffff;
            }
            QCalendarWidget QAbstractItemView::item {
                border-radius: 6px;
                padding: 5px;
            }
            QCalendarWidget QAbstractItemView::item:hover {
                background-color: #f4f4f5;
            }
            QCalendarWidget QAbstractItemView::item:selected,
            QCalendarWidget QAbstractItemView::item:selected:hover {
                background-color: #2563eb;
                color: #ffffff;
            }
            QCalendarWidget QMenu {
                background-color: #ffffff;
                color: #18181b;
                border: 1px solid #d4d4d8;
                padding: 4px;
            }
            QCalendarWidget QMenu::item {
                border-radius: 5px;
                padding: 6px 18px;
            }
            QCalendarWidget QMenu::item:selected {
                background-color: #18181b;
                color: #ffffff;
            }
        """)

        weekday_format = QTextCharFormat()
        weekday_format.setForeground(QColor("#18181b"))
        weekend_format = QTextCharFormat()
        weekend_format.setForeground(QColor("#dc2626"))
        today_format = QTextCharFormat()
        today_format.setBackground(QColor("#dbeafe"))
        today_format.setForeground(QColor("#1d4ed8"))
        for day in (
            Qt.DayOfWeek.Monday,
            Qt.DayOfWeek.Tuesday,
            Qt.DayOfWeek.Wednesday,
            Qt.DayOfWeek.Thursday,
            Qt.DayOfWeek.Friday,
        ):
            calendar.setWeekdayTextFormat(day, weekday_format)
        calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
        calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)
        calendar.setDateTextFormat(QDate.currentDate(), today_format)

        self.date_edit.setSelectedSection(QDateEdit.Section.DaySection)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)

        desc_layout = QVBoxLayout()
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setSpacing(0)
        description_label = QLabel("Project Description")
        description_label.setStyleSheet("font-size: 36px; border: none")
        self.description = QPlainTextEdit()
        self.description.setPlaceholderText("Enter project details...")
        self.description.setFixedWidth(880)
        self.description.setFixedHeight(500)
        date_layout.addWidget(description_label)
        date_layout.addWidget(self.description)

        layout.addLayout(date_layout)
        layout.addLayout(desc_layout)

    def get_timestamptz(self) -> str:
        """Returns date formatted as timestamptz."""
        qdate = self.date_edit.date()
    
        # Create local midnight datetime and apply system local timezone
        dt = datetime(qdate.year(), qdate.month(), qdate.day()).astimezone()
        
        return dt.isoformat()

    def set_date(self, timestamptz_str: str):
        """Parses a Supabase timestamptz string (ISO 8601) and updates the QDateEdit."""
        if not timestamptz_str:
            return

        try:
            # Standardize ISO string format for Python 
            clean_str = timestamptz_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            self.date_edit.setDate(QDate(dt.year, dt.month, dt.day))
        except (ValueError, TypeError) as e:
            print(f"Error parsing date timestamp '{timestamptz_str}': {e}")

    def get_description(self) -> str:
        return self.description.toPlainText().strip()

    def set_description(self, text: str):
        self.description.setPlainText(text)
