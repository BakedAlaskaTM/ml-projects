import sys
from pathlib import Path

# Allow this file to be launched directly (``python views/display.py``) while
# keeping the project's imports rooted at the repository directory.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
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

RESULT_COUNT = 21
MAX_CACHE_PAGES = 1000 // RESULT_COUNT # RESULT_COUNT * CACHE_PAGES <= 1000


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Manager")
        self.resize(1920, 1080)
        self.setStyleSheet(GLOBAL_STYLE)

        # Get relevant info from DB
        project_info = api.get_project_by_slug(supabase, "TRePcqMK")
        if project_info is not None:
            project_info = project_info[0]

        selected_tracks_rows = api.get_tracks_by_project_slug(supabase, "TRePcqMK")

        # Global Selection State: {track_id: track_name}
        self.selected_tracks = construct_selected_tracks(selected_tracks_rows) if selected_tracks_rows else {}
        self.current_page = 0 # Page pointer
        self.has_more_data = False # More data to be collected from TMX
        self.final_id = None # Last row ID for pagination
        self.query_dict = {}
        self.search_mode = tmx.Category.TRACKS
        self.results = [] # Cache search results for faster pagination
        self.stored_track_info = {}
        self.project_slug = project_info["slug"] if project_info else ""
        self.project_name = project_info["name"] if project_info else "Default project"
        self.initial_tracks = self.selected_tracks.copy()

        # Root Central Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        outer_layout = QHBoxLayout(central_widget)
        outer_layout.addStretch()

        main_content = QWidget()
        main_content.setFixedWidth(1920)
        main_content.setFixedHeight(1080)
        root_layout = QVBoxLayout(main_content)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(20)

        outer_layout.addWidget(main_content)
        outer_layout.addStretch()
        

        # Instantiate Component Widgets
        self.header = HeaderWidget()
        self.selected_panel = SelectedTracksWidget()
        self.results_panel = SearchResultsWidget()
        self.filters_panel = FiltersWidget()
        self.selected_map_info = FocusedMapInfoWidget()
        self.bottom_actions = BottomActionsWidget()

        # Assembly middle right content
        middle_right_col = QVBoxLayout()
        middle_right_col.setSpacing(10)
        middle_right_col.addWidget(self.filters_panel)
        middle_right_col.addWidget(self.selected_map_info)

        # Assembly Middle Content Row
        middle_row = QHBoxLayout()
        middle_row.setSpacing(20)
        middle_row.addWidget(self.selected_panel)
        middle_row.addWidget(self.results_panel, stretch=1)
        middle_row.addLayout(middle_right_col)

        self.results_panel.search_triggered.connect(self.handle_search)
        self.results_panel.checkbox_toggled.connect(self.handle_table_toggle)
        self.results_panel.page_changed.connect(self.handle_page_change)
        self.selected_panel.item_removed_signal.connect(self.handle_left_panel_remove)
        self.results_panel.cell_selected.connect(self.display_current_map_info)
        self.bottom_actions.export_button_pressed.connect(self.handle_export)
        self.bottom_actions.save_button_pressed.connect(self.handle_save)
        self.results_panel.prev_btn.setEnabled(self.current_page > 0)
        self.results_panel.next_btn.setEnabled(self.has_more_data)

        # Assembly Main View
        root_layout.addWidget(self.header)
        root_layout.addLayout(middle_row, stretch=1)
        root_layout.addWidget(self.bottom_actions)

        self.selected_panel.refresh_list(self.selected_tracks)
        self.header.project_title_input.setText(self.project_name)
        #self.load_mock_data()

    def handle_search(self, query_text: str):
        """Action triggers ONLY on Enter press in search input."""
        filter_states = self.filters_panel.get_filter_states()
        self.search_mode = tmx.Category.TRACKS if self.filters_panel.tracks_radio.isChecked() else tmx.Category.USERS
        self.query_dict = {"name": query_text, "count": RESULT_COUNT*MAX_CACHE_PAGES, "order1": 2}
        for param, value in filter_states.items():
            if value == "":
                continue
            self.query_dict[param] = value
        results = tmx.search(session, self.search_mode, self.query_dict)
        self.has_more_data = results["More"]
        self.results = tmx.flatten_results(results["Results"], self.search_mode)
        if len(self.results) > 0:
            self.final_id = self.results[-1]["TrackId"]
        self.current_page = 0
        self.results_panel.next_btn.setEnabled((self.current_page+1)*RESULT_COUNT < len(self.results) or self.has_more_data)
        self.results_panel.populate_table(self.results[self.current_page*RESULT_COUNT:(self.current_page+1)*RESULT_COUNT], set(self.selected_tracks.keys()))

    def handle_table_toggle(self, uid: str, is_checked: bool):
        if is_checked:
            self.selected_tracks[uid] = next(track_info for track_info in self.results if track_info["UId"] == uid)
        else:
            self.selected_tracks.pop(uid, None)
        self.selected_panel.refresh_list(self.selected_tracks)

    def handle_left_panel_remove(self, uid: str, track_id: int):
        self.selected_tracks.pop(uid, None)
        self.selected_panel.refresh_list(self.selected_tracks)
        self.results_panel.set_row_checkbox(track_id, False)

    def handle_page_change(self, dir: int):
        self.current_page = max(0, self.current_page + dir)

        # Only perform tmx query if on last cached page
        if (self.current_page+1)*RESULT_COUNT >= len(self.results) and self.has_more_data:
            self.query_dict["after"] = "" # Store final id
            results = tmx.search(session, self.search_mode, self.query_dict)
            self.has_more_data = results["More"]
            self.results += tmx.flatten_results(results["Results"], self.search_mode)

        # Update display
        self.results_panel.populate_table(self.results[self.current_page*RESULT_COUNT:(self.current_page+1)*RESULT_COUNT], set(self.selected_tracks.keys()))

        self.results_panel.prev_btn.setEnabled(self.current_page > 0)
        self.results_panel.next_btn.setEnabled((self.current_page+1)*RESULT_COUNT < len(self.results) or self.has_more_data)

    def display_current_map_info(self, track_info: dict):
        self.selected_map_info.update_label_text(track_info)

    def handle_export(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "JSON Files (*.json)")
        if save_path is None:
            return
        export_data = {}
        export_data["ProjectName"] = self.header.project_title_input.text()
        export_data["ProjectSlug"] = self.project_slug
        export_data["SelectedTracks"] = self.selected_tracks
        write_json(save_path, export_data)
        
    
    def handle_save(self):
        print("Starting save")
        removed_uids = set(self.initial_tracks.keys())-set(self.selected_tracks.keys())
        api.delete_project_map_rows(supabase, By.UID, list(removed_uids), self.project_slug)

        project_data = flatten_project_data(self.header.project_title_input.text(), self.project_slug)
        api.upsert_projects(supabase, project_data)
        print(self.selected_tracks)
        map_data = flatten_selected_tracks(self.selected_tracks)
        api.upsert_maps(supabase, map_data)

        project_map_data = construct_project_map_rows(self.selected_tracks.keys(), self.project_slug)
        api.upsert_project_map_rows(supabase, project_map_data)
        print("Save complete")
        self.initial_tracks = self.selected_tracks.copy()
        

    def load_mock_data(self):
        mock_results = [
            {"TrackName": "Track #1", "Authors": [{"UserId": 123808, "Name": "Author 1"}], "AuthorTime": 30520, "TrackId": 1582819, "UpdatedAt": "2022-02-05T"},
        ]
        self.results_panel.populate_table(mock_results, set(self.selected_tracks.keys()))

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
    
