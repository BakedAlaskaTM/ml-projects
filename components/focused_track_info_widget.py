from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QVBoxLayout, QLabel, QFrame)

class FocusedMapInfoWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(440)
        self.setFixedHeight(350)
        self.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet("background-color: white; border: 1px solid black; border-radius: 10px")
        info_layout = QVBoxLayout(self)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(20)

        title = QLabel("Selected Map Information")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; border: none; margin-bottom: 10px")
        info_layout.addWidget(title)

        self.track_name = QLabel()
        self.author_name = QLabel()
        self.author_time = QLabel()
        self.author_id = QLabel()
        self.track_id = QLabel()
        self.uid = QLabel()
        self.upload_date = QLabel()

        fields = [
            ("Name", self.track_name),
            ("Author", self.author_name),
            ("AT", self.author_time),
            ("Author ID", self.author_id),
            ("Track ID", self.track_id),
            ("Track UID", self.uid),
            ("Upload Date", self.upload_date)
        ]

        for label_text, widget in fields:
            widget.setText(f"{label_text} :")
            widget.setStyleSheet("border: none")
            info_layout.addWidget(widget)

        info_layout.addStretch()

    def update_label_text(self, track_info: dict):
        fields = [
            ("Name", track_info["TrackName"], self.track_name),
            ("Author", track_info["Authors"][0]["Name"], self.author_name),
            ("AT", track_info["AuthorTime"], self.author_time),
            ("Author ID", track_info["Authors"][0]["UserId"], self.author_id),
            ("Track ID", track_info["TrackId"], self.track_id),
            ("Track UID", track_info["UId"], self.uid),
            ("Upload Date", track_info["UpdatedAt"], self.upload_date)
        ]

        for label_text, info_text, widget in fields:
            widget.setText(f"{label_text} : {info_text}")
