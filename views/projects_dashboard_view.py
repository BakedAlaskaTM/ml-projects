import sys
from pathlib import Path

# Allow this file to be launched directly (``python views/display.py``) while
# keeping the project's imports rooted at the repository directory.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QPushButton, QGridLayout, QLabel, QMessageBox
)
from supabase import create_client, Client
from dotenv import load_dotenv
from components.project_card_widget import ProjectCardWidget
from styles.styles import GLOBAL_STYLE
from libs.utils import (
    By,
    construct_project_map_rows,
    construct_selected_tracks,
    flatten_project_data,
    flatten_selected_tracks,
    write_json,
    generate_slug,
)
from libs import api, tmx
import requests
import os
import sys

GRID_COLS = 5
GRID_ROWS = 2

class ProjectsDashboardView(QWidget):
    project_selected = pyqtSignal(str) # Emits project slug
    def __init__(self, client: Client):
        super().__init__()
        self.client = client
        main_layout = QVBoxLayout(self)
        header_layout = QHBoxLayout()
        self.title = QLabel("Project Manager")
        self.title.setStyleSheet("font-size: 64px;")
        self.new_project_button = QPushButton("New Project")
        self.new_project_button.setFixedWidth(240)
        self.new_project_button.setFixedHeight(100)
        header_layout.addWidget(self.title)
        header_layout.addWidget(self.new_project_button)
        main_layout.addLayout(header_layout)
        self.card_layout = QGridLayout()
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        main_layout.addLayout(self.card_layout)

        self.new_project_button.clicked.connect(self.add_project)

    def load_projects(self):
        self.all_projects = api.get_all_projects(self.client)
        print(self.all_projects)
        if self.all_projects is None:
            print("Error fetching projects")
            sys.exit()
        self.title.setText(f"Project Manager \u2022 {len(self.all_projects)} project{'s' if len(self.all_projects) != 1 else ''}")
        self.populate_grid(self.all_projects)

    def add_project(self):
        project_info = [{
            "name": "New Project",
            "slug": generate_slug(),
            "is_active": True,
            "status": "ACTIVE"
        }]
        api.upsert_projects(self.client, project_info)
        self.load_projects()

    def delete_project(self, slug: str):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("WARNING: PROJECT DELETION")
        dlg.setText(f"Are you sure you want to delete project {slug}?")
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        button = dlg.exec()
        if button == QMessageBox.StandardButton.No:
            return

        api.upsert_projects(self.client, [{"slug": slug, "is_active": False}])
        self.load_projects()
        

    def populate_grid(self, projects):
        self.clear_layout(self.card_layout)
        # 2. Clear old stretch factors if reusing layout
        for r in range(self.card_layout.rowCount()):
            self.card_layout.setRowStretch(r, 0)
        for c in range(self.card_layout.columnCount()):
            self.card_layout.setColumnStretch(c, 0)
        
        for idx, project in enumerate(projects):
            project_card = ProjectCardWidget(project)
            project_card.edit_requested.connect(lambda slug: self.project_selected.emit(slug))
            project_card.delete_requested.connect(self.delete_project)
            self.card_layout.addWidget(project_card, idx // GRID_COLS, idx % GRID_COLS)

        self.card_layout.setColumnStretch(GRID_COLS, 1)  # Absorbs extra horizontal space
        self.card_layout.setRowStretch((len(projects) // GRID_COLS) + 1, 1)  # Absorbs extra vertical space

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                
                if widget is not None:
                    # Safely schedules the widget for deletion
                    widget.deleteLater()
                elif item.layout() is not None:
                    # Recursively clear nested layouts
                    self.clear_layout(item.layout())