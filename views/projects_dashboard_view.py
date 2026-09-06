import sys
from pathlib import Path

# Allow this file to be launched directly (``python views/display.py``) while
# keeping the project's imports rooted at the repository directory.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QPushButton
)
from supabase import create_client, Client
from dotenv import load_dotenv
from components.header_widget import HeaderWidget
from components.selected_tracks_widget import SelectedTracksWidget
from components.search_results_widget import SearchResultsWidget
from components.filters_widget import FiltersWidget
from components.focused_track_info_widget import FocusedMapInfoWidget
from components.bottom_actions_widget import BottomActionsWidget
from styles.styles import GLOBAL_STYLE
from libs.utils import (
    By,
    construct_project_map_rows,
    construct_selected_tracks,
    flatten_project_data,
    flatten_selected_tracks,
    write_json,
)
from libs import api, tmx
import requests
import os

class ProjectsDashboardView(QWidget):
    project_selected = pyqtSignal(str) # Emits project slug
    def __init__(self, client: Client):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.client = client
        print("Hi")
        self.editor_button = QPushButton("Go to project")
        self.main_layout.addWidget(self.editor_button)

        self.editor_button.clicked.connect(lambda: self.project_selected.emit("TRePcqMK"))