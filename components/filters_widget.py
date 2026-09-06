from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFrame, QButtonGroup
)

class FiltersWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(440)
        self.setFixedHeight(420)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: white; border: 1px solid black; border-radius: 10px")

        filter_layout = QVBoxLayout(self)
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

    def get_filter_states(self) -> dict:
        """Returns active text values across all filter inputs."""
        return {
            "author": self.author_name.text().strip(),
            "author_user_id": self.author_id.text().strip(),
            "id": self.track_ids.text().strip(),
            "replaysby": self.replays_by_id.text().strip()
        }