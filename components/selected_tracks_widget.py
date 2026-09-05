from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea
)

class SelectedTracksWidget(QFrame):
    item_removed_signal = pyqtSignal(str, int)  # Emits uid, track_id when red 'X' clicked

    def __init__(self):
        super().__init__()
        self.setFixedWidth(440)
        self.setFixedHeight(810)
        self.setObjectName("selectedTracksFrame")
        self.setStyleSheet("border: 1px solid black")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.title = QLabel("Currently Selected")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 20px; font-weight: bold; border: none;")
        main_layout.addWidget(self.title)

        # Scrollable container
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none")
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scrollContent")
        self.items_layout = QVBoxLayout(self.scroll_content)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(10)
        self.items_layout.addStretch()  # Push items to top

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

    def refresh_list(self, selected_tracks: dict):
        """Rebuilds list from state dictionary {track_id: track_info (dict)}."""
        # Clear existing items
        while self.items_layout.count() > 1:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for uid, track_info in selected_tracks.items():
            track_name = track_info["TrackName"]
            track_id = track_info["TrackId"]
            row_frame = QFrame()
            row_frame.setStyleSheet("border: none;")
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(0, 0, 0, 0)

            name_lbl = QLabel(track_name)
            name_lbl.setFixedWidth(240)
            name_lbl.setStyleSheet("font-size: 16px;")
            # Elide middle/end for overly long strings
            metrics = name_lbl.fontMetrics()
            elided_text = metrics.elidedText(track_name, Qt.TextElideMode.ElideRight, 180)
            name_lbl.setText(elided_text)

            id_lbl = QLabel(str(track_id))
            id_lbl.setFixedWidth(120)
            id_lbl.setStyleSheet("font-size: 16px; color: #555;")
            id_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            remove_btn = QPushButton("X")
            remove_btn.setObjectName("removeBtn")
            remove_btn.clicked.connect(lambda _, uid=uid, tid=track_id: self.item_removed_signal.emit(uid, tid))

            row_layout.addWidget(name_lbl)
            row_layout.addWidget(id_lbl)
            row_layout.addWidget(remove_btn)

            self.items_layout.insertWidget(self.items_layout.count() - 1, row_frame)
        self.title.setText(f"Currently Selected: {len(selected_tracks.keys())}")