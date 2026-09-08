from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QFrame, QLabel)
from libs.utils import ProjectStatus

class HeaderWidget(QWidget):
    edit_focus_changed = Signal(str) # TRACKS or PROJECT
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        editing_frame = QFrame()
        editing_frame.setStyleSheet("border: 1px solid black; border-radius: 10px; background-color: white;")
        editing_frame.setFixedWidth(440)
        editing_frame.setFixedHeight(100)
        editing_frame.setContentsMargins(0, 0, 0, 0)
        editing_layout = QHBoxLayout(editing_frame)
        editing_layout.setSpacing(20)
        editing_layout.setContentsMargins(20, 0, 0, 0)
        edit_focus_label = QLabel("Editing:")
        edit_focus_label.setStyleSheet("font-size: 36px; font-weight: bold; border: none; background: transparent;")
        edit_focus_label.setFixedWidth(150)
        edit_focus_label.setFixedHeight(100)
        self.edit_focus_dropdown = QComboBox()
        self.edit_focus_dropdown.setStyleSheet("font-size: 36px; font-weight: bold; padding: 20px; border: none;")
        self.edit_focus_dropdown.setFixedWidth(240)
        self.edit_focus_dropdown.setFixedHeight(98)
        self.edit_focus_dropdown.addItems(["TRACKS", "PROJECT"])
        editing_layout.addWidget(edit_focus_label)
        editing_layout.addWidget(self.edit_focus_dropdown)

        self.project_title_input = QLineEdit()
        self.project_title_input.setStyleSheet("font-size: 36px; font-weight: bold; padding: 10px;")
        self.project_title_input.setFixedWidth(740)
        self.project_title_input.setFixedHeight(100)

        self.status_dropdown = QComboBox()
        self.status_dropdown.setStyleSheet("font-size: 36px; font-weight: bold; padding: 20px;")
        self.status_dropdown.setFixedWidth(200)
        self.status_dropdown.setFixedHeight(100)
        self.status_dropdown.addItems(ProjectStatus.list_all())

        self.back_btn = QPushButton("Back")
        self.back_btn.setStyleSheet("font-size: 36px; font-weight: bold;")
        self.back_btn.setFixedWidth(440)
        self.back_btn.setFixedHeight(100)

        layout.addWidget(editing_frame)
        layout.addWidget(self.project_title_input)
        layout.addWidget(self.status_dropdown)
        layout.addWidget(self.back_btn)

        self.edit_focus_dropdown.currentTextChanged.connect(lambda: self.edit_focus_changed.emit(self.edit_focus_dropdown.currentText()))
