from pathlib import Path

from PySide6.QtCore import QDate, QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ProjectCardWidget(QFrame):
    """Compact summary card for a project on the dashboard."""

    edit_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, project: dict | None = None):
        super().__init__()
        self.project_slug = ""

        self.setObjectName("projectCard")
        self.setFixedSize(360, 360)
        self.setStyleSheet("""
            QFrame#projectCard {
                background-color: #ffffff;
                border: 1px solid #18181b;
                border-radius: 10px;
            }
            QFrame#projectCard QLabel {
                background-color: transparent;
                border: none;
                color: #18181b;
            }
            QLabel#projectCardStatus {
                font-size: 20px;
                font-weight: 500;
            }
            QLabel#projectCardName {
                font-size: 28px;
                font-weight: 400;
            }
            QLabel#projectCardSlug {
                color: #3f3f46;
                font-size: 16px;
            }
            QLabel#projectCardMeta {
                font-size: 15px;
            }
            QLabel#projectCardDescription {
                color: #27272a;
                font-size: 14px;
            }
            QFrame#projectCardDivider {
                background-color: #3f3f46;
                border: none;
            }
            QPushButton#projectCardDeleteButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 0;
            }
            QPushButton#projectCardDeleteButton:hover {
                background-color: #fef2f2;
            }
            QPushButton#projectCardDeleteButton:pressed {
                background-color: #fee2e2;
            }
            QPushButton#projectCardEditButton {
                background-color: #ffffff;
                border: 1px solid #18181b;
                border-radius: 10px;
                color: #18181b;
                font-size: 18px;
                font-weight: 400;
                padding: 0;
            }
            QPushButton#projectCardEditButton:hover {
                background-color: #f4f4f5;
            }
            QPushButton#projectCardEditButton:pressed {
                background-color: #e4e4e7;
            }
        """)

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(0)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.status_label = QLabel()
        self.status_label.setObjectName("projectCardStatus")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        self.delete_button = QPushButton()
        self.delete_button.setObjectName("projectCardDeleteButton")
        trash_icon_path = Path(__file__).resolve().parents[1] / "assets" / "trash-can.svg"
        self.delete_button.setIcon(QIcon(str(trash_icon_path)))
        self.delete_button.setIconSize(QSize(18, 20))
        self.delete_button.setFixedSize(32, 32)
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_button.setToolTip("Delete project")

        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.delete_button)
        card_layout.addLayout(header_layout)

        card_layout.addSpacing(8)

        self.project_name_label = QLabel()
        self.project_name_label.setObjectName("projectCardName")
        self.project_name_label.setFixedHeight(36)
        card_layout.addWidget(self.project_name_label)

        self.project_slug_label = QLabel()
        self.project_slug_label.setObjectName("projectCardSlug")
        self.project_slug_label.setFixedHeight(24)
        card_layout.addWidget(self.project_slug_label)

        card_layout.addSpacing(20)

        metadata_layout = QHBoxLayout()
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(8)

        self.start_date_label = QLabel()
        self.start_date_label.setObjectName("projectCardMeta")
        self.map_count_label = QLabel()
        self.map_count_label.setObjectName("projectCardMeta")
        self.map_count_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        metadata_layout.addWidget(self.start_date_label)
        metadata_layout.addStretch()
        metadata_layout.addWidget(self.map_count_label)
        card_layout.addLayout(metadata_layout)

        card_layout.addSpacing(16)

        divider = QFrame()
        divider.setObjectName("projectCardDivider")
        divider.setFixedHeight(1)
        card_layout.addWidget(divider)

        card_layout.addSpacing(16)

        self.description_label = QLabel()
        self.description_label.setObjectName("projectCardDescription")
        self.description_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self.description_label.setWordWrap(True)
        self.description_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        card_layout.addWidget(self.description_label, stretch=1)

        card_layout.addSpacing(12)

        edit_button_row = QHBoxLayout()
        edit_button_row.setContentsMargins(0, 0, 0, 0)
        self.edit_button = QPushButton("Edit Project  \u2192")
        self.edit_button.setObjectName("projectCardEditButton")
        self.edit_button.setFixedSize(185, 30)
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_button_row.addStretch()
        edit_button_row.addWidget(self.edit_button)
        edit_button_row.addStretch()
        card_layout.addLayout(edit_button_row)

        self.edit_button.clicked.connect(
            lambda: self.edit_requested.emit(self.project_slug)
        )
        self.delete_button.clicked.connect(
            lambda: self.delete_requested.emit(self.project_slug)
        )

        self.set_project(project or {})

    def set_project(self, project: dict):
        """Populate the card from a Supabase project row or exported project data."""
        self.project_slug = str(project.get("slug", project.get("Slug", "")) or "")
        name = str(project.get("name", project.get("Name", "Untitled Project")))
        status = project.get("status", project.get("Status", ""))
        description = str(
            project.get("description", project.get("Description", "")) or ""
        )
        started_at = project.get("started_at", project.get("StartDate", ""))

        if hasattr(status, "value"):
            status = status.value

        map_count = project.get("map_count", project.get("MapCount", 0))

        self.status_label.setText(str(status).upper())
        self.project_name_label.setText(name)
        self.project_slug_label.setText(self.project_slug)
        self.start_date_label.setText(f"Started {self._format_date(started_at)}")
        self.map_count_label.setText(f"{int(map_count or 0)} Maps")
        self.description_label.setText(description)

    @staticmethod
    def _format_date(value) -> str:
        if isinstance(value, QDate):
            date = value
        else:
            date = QDate.fromString(str(value or "")[:10], Qt.DateFormat.ISODate)

        return date.toString("dd/MM/yyyy") if date.isValid() else "--/--/----"
