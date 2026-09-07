import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
)
from supabase import create_client, Client
from dotenv import load_dotenv
from components.header_widget import HeaderWidget
from components.selected_tracks_widget import SelectedTracksWidget
from components.search_results_widget import SearchResultsWidget
from components.filters_widget import FiltersWidget
from components.focused_track_info_widget import FocusedMapInfoWidget
from components.bottom_actions_widget import BottomActionsWidget
from views.project_editor_view import ProjectEditorView
from views.projects_dashboard_view import ProjectsDashboardView
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Manager")
        self.resize(1920, 1080)
        self.setStyleSheet(GLOBAL_STYLE)

        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        
        outer_layout = QHBoxLayout(central_widget)
        outer_layout.addStretch()
        
        # 1. Create the stack manager
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setFixedWidth(1920)
        self.stacked_widget.setFixedHeight(1080)
        outer_layout.addWidget(self.stacked_widget, stretch=1)
        outer_layout.addStretch()

        # 2. Instantiate views
        self.dashboard_page = ProjectsDashboardView(supabase)
        self.editor_page = ProjectEditorView(supabase, session)

        # 3. Add pages to the stack
        self.stacked_widget.addWidget(self.dashboard_page)  # Index 0
        self.stacked_widget.addWidget(self.editor_page)     # Index 1

        # 4. Connect routing signals
        self.dashboard_page.project_selected.connect(self.open_editor)
        self.editor_page.back_to_dashboard.connect(self.open_dashboard)

        self.open_dashboard()
    
    def open_editor(self, project_slug: str):
        """Navigates to editor view and passes data."""
        self.editor_page.load_project_data(project_slug)
        self.stacked_widget.setCurrentWidget(self.editor_page)

    def open_dashboard(self):
        """Swaps back to dashboard view."""
        self.dashboard_page.load_projects()
        self.stacked_widget.setCurrentWidget(self.dashboard_page)

if __name__ == "__main__":
    # Load variables from .env into system environment
    load_dotenv()

    # Replace with your actual project keys from Supabase dashboard
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY") # Use service role if bypasses RLS is needed for backend

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    session = requests.Session()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    session.close()