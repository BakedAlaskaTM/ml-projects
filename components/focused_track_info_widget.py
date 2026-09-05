from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QFrame)

class FocusedMapInfoWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(440)
        self.setFixedHeight(290)
        self.setContentsMargins(0, 0, 0, 0)

        info_frame = QFrame(self)
        info_frame.setStyleSheet("background-color: white; border: 1px solid black; border-radius: 10px")
        info_frame.setFixedWidth(440)
        info_frame.setFixedHeight(290)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(20)

        title = QLabel("Selected Map Information")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; border: none; margin-bottom: 10px")
        info_layout.addWidget(title)

        self.track_name = QLabel()
        self.author_name = QLabel()
        self.author_time = QLabel()

        fields = [
            ("Name", self.track_name),
            ("Author", self.author_name),
            ("AT", self.author_time),
        ]

        for label_text, widget in fields:
            widget.setText(f"{label_text} :")
            widget.setStyleSheet("border: none")
            info_layout.addWidget(widget)

        info_layout.addStretch()

    def update_label_text(self, track_info: dict):
        fields = [
            ("Name", track_info["TrackName"], self.track_name),
            ("Author", track_info["AuthorName"], self.author_name),
            ("AT", track_info["AuthorTime"], self.author_time),
        ]

        for label_text, info_text, widget in fields:
            widget.setText(f"{label_text} : {info_text}")