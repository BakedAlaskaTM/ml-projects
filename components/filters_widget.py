from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFrame, QButtonGroup
)

class FiltersWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(440)
        self.setFixedHeight(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tracks_radio = QPushButton("Tracks")
        self.tracks_radio.setFixedHeight(50)
        self.tracks_radio.setObjectName("tracksRadio")
        self.tracks_radio.setCheckable(True)
        self.tracks_radio.setChecked(True)

        self.users_radio = QPushButton("Users")
        self.users_radio.setFixedHeight(50)
        self.users_radio.setObjectName("usersRadio")
        self.users_radio.setCheckable(True)

        self.radio_group = QButtonGroup(self)
        self.radio_group.addButton(self.tracks_radio)
        self.radio_group.addButton(self.users_radio)

        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(20)
        radio_layout.addWidget(self.tracks_radio)
        radio_layout.addWidget(self.users_radio)

        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: white; border: 1px solid black; border-radius: 10px")
        filter_frame.setFixedHeight(410)
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(20, 20, 20, 20)
        filter_layout.setSpacing(20)

        title = QLabel("Filters")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; border: none; margin-bottom: 10px")
        filter_layout.addWidget(title)

        # Filter Inputs
        self.author_name = QLineEdit()
        self.author_id = QLineEdit()
        self.track_ids = QLineEdit()
        self.replays_by_id = QLineEdit()

        fields = [
            ("Author Name", self.author_name),
            ("Author ID", self.author_id),
            ("Track Id(s)", self.track_ids),
            ("Replays By (ID)", self.replays_by_id)
        ]

        for label_text, widget in fields:
            input_layout = QVBoxLayout()
            input_layout.setSpacing(8)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("border: none; font-size: 16px;")
            input_layout.addWidget(lbl)
            input_layout.addWidget(widget)
            filter_layout.addLayout(input_layout)

        filter_layout.addStretch()

        layout.addLayout(radio_layout)
        layout.addWidget(filter_frame)

    def get_filter_states(self) -> dict:
        """Returns active text values across all filter inputs."""
        return {
            "author": self.author_name.text().strip(),
            "author_user_id": self.author_id.text().strip(),
            "id": self.track_ids.text().strip(),
            "replaysby": self.replays_by_id.text().strip()
        }