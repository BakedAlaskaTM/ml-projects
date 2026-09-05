from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLineEdit)

class HeaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.back_btn = QPushButton("Back to Projects")
        self.back_btn.setFixedWidth(440)
        self.back_btn.setFixedHeight(100)

        self.project_title_input = QLineEdit()
        self.project_title_input.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        self.project_title_input.setFixedWidth(1420)
        self.project_title_input.setFixedHeight(100)

        layout.addWidget(self.back_btn)
        layout.addWidget(self.project_title_input)