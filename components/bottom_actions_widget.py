from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton)

class BottomActionsWidget(QWidget):
    save_button_pressed = pyqtSignal()
    export_button_pressed = pyqtSignal()
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.export_btn = QPushButton("Export JSON")
        self.export_btn.setStyleSheet("font-size: 26px; font-weight: bold; padding: 15px;")
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("font-size: 26px; font-weight: bold; padding: 15px;")

        self.export_btn.clicked.connect(lambda: self.export_button_pressed.emit())
        self.save_btn.clicked.connect(lambda: self.save_button_pressed.emit())
        layout.addWidget(self.export_btn, stretch=1)
        layout.addWidget(self.save_btn, stretch=1)