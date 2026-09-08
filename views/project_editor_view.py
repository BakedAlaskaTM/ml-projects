from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QStackedWidget
)
from supabase import Client
from components.header_widget import HeaderWidget
from components.selected_tracks_widget import SelectedTracksWidget
from components.search_results_widget import SearchResultsWidget
from components.filters_widget import FiltersWidget
from components.focused_track_info_widget import FocusedMapInfoWidget
from components.bottom_actions_widget import BottomActionsWidget
from components.edit_project_info_widget import EditProjectInfoWidget
from libs.utils import (
    By,
    ProjectStatus,
    construct_project_map_rows,
    construct_selected_tracks,
    flatten_project_data,
    flatten_selected_tracks,
    write_json,
)
from libs import api, tmx
import requests

RESULT_COUNT = 21
MAX_CACHE_PAGES = 1000 // RESULT_COUNT # RESULT_COUNT * CACHE_PAGES <= 1000


class ProjectEditorView(QWidget):
    back_to_dashboard = Signal()
    def __init__(self, client: Client, session: requests.Session):
        super().__init__()

        self.client = client
        self.session = session

        # Setup stored data
        self.project_info = {"Name": None, "Slug": None, "Status": None, "StartDate": None, "Description": None}
        self.selected_tracks = {}
        self.current_page = 0 # Page pointer
        self.has_more_data = False # More data to be collected from TMX
        self.final_id = None # Last row ID for pagination
        self.query_dict = {}
        self.search_mode = tmx.Category.TRACKS
        self.results = [] # Cache search results for faster pagination
        self.stored_track_info = {}
        self.initial_tracks = None

        self.setFixedWidth(1920)
        self.setFixedHeight(1080)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(20)

        # Instantiate Component Widgets
        self.header = HeaderWidget()
        self.selected_panel = SelectedTracksWidget()
        self.results_panel = SearchResultsWidget()
        self.filters_panel = FiltersWidget()
        self.selected_map_info = FocusedMapInfoWidget()
        self.bottom_actions = BottomActionsWidget()
        self.edit_project_info = EditProjectInfoWidget()

        # Create stacked middle section
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setContentsMargins(0, 0, 0, 0)

        # Assembly middle right content (tracks)
        middle_right_col = QVBoxLayout()
        middle_right_col.setSpacing(20)
        middle_right_col.setContentsMargins(0, 0, 0, 0)
        middle_right_col.addWidget(self.filters_panel)
        middle_right_col.addWidget(self.selected_map_info)

        # Assembly Middle Content Row (tracks)
        middle_row_widget = QWidget()
        middle_row = QHBoxLayout(middle_row_widget)
        middle_row.setContentsMargins(0, 0, 0, 0)
        middle_row.setSpacing(20)
        middle_row.addWidget(self.selected_panel)
        middle_row.addWidget(self.results_panel, stretch=1)
        middle_row.addLayout(middle_right_col)

        self.stacked_widget.addWidget(middle_row_widget)

        # Assembly middle row (project)
        project_edit_widget = QWidget()
        project_edit_layout = QHBoxLayout(project_edit_widget)
        project_edit_layout.addStretch()
        project_edit_layout.addWidget(self.edit_project_info)
        project_edit_layout.addStretch()

        self.stacked_widget.addWidget(project_edit_widget)

        self.header.back_btn.clicked.connect(lambda: self.back_to_dashboard.emit())
        self.header.edit_focus_changed.connect(self.handle_edit_focus_change)
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
        root_layout.addWidget(self.stacked_widget, stretch=1)
        root_layout.addWidget(self.bottom_actions)

    def load_project_data(self, project_slug: str):
        # Get relevant info from DB
        project_info = api.get_project_by_slug(self.client, project_slug)
        if project_info is None:
            print("Project load failure")
            self.back_to_dashboard.emit()
            return
        project_info = project_info[0]

        selected_tracks_rows = api.get_tracks_by_project_slug(self.client, project_slug)

        self.project_info["Slug"] = project_info["slug"]
        self.project_info["Name"] = project_info["name"]
        self.project_info["Status"] = ProjectStatus(project_info["status"])
        self.project_info["StartDate"] = project_info["started_at"]
        self.project_info["Description"] = project_info["description"]

        # Global Selection State: {track_uid: {track_info}}
        self.selected_tracks = construct_selected_tracks(selected_tracks_rows) if selected_tracks_rows else {}
        self.current_page = 0 # Page pointer
        self.has_more_data = False # More data to be collected from TMX
        self.final_id = None # Last row ID for pagination
        self.query_dict = {}
        self.search_mode = tmx.Category.TRACKS
        self.results = [] # Cache search results for faster pagination
        self.stored_track_info = {}
        self.initial_tracks = self.selected_tracks.copy()

        # Update UI
        self.selected_panel.refresh_list(self.selected_tracks)
        self.header.project_title_input.setText(self.project_info["Name"])
        self.header.status_dropdown.setCurrentText(self.project_info["Status"].name)
        self.edit_project_info.set_date(self.project_info["StartDate"])
        self.edit_project_info.set_description(self.project_info["Description"])

    def handle_search(self, query_text: str):
        """Action triggers ONLY on Enter press in search input."""
        filter_states = self.filters_panel.get_filter_states()
        self.query_dict = {"name": query_text, "count": RESULT_COUNT*MAX_CACHE_PAGES, "order1": 2}
        for param, value in filter_states.items():
            if value == "":
                continue
            self.query_dict[param] = value
        results = tmx.search(self.session, self.search_mode, self.query_dict)
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
            results = tmx.search(self.session, self.search_mode, self.query_dict)
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
        export_data["ProjectSlug"] = self.project_info["Slug"]
        export_data["ProjectStatus"] = ProjectStatus(self.header.status_dropdown.currentText())
        export_data["ProjectStartDate"] = self.project_info["StartDate"]
        export_data["ProjectDescription"] = self.project_info["Description"]
        export_data["SelectedTracks"] = self.selected_tracks
        write_json(save_path, export_data)
        
    
    def handle_save(self):
        self.project_info["Status"] = ProjectStatus(self.header.status_dropdown.currentText())
        self.project_info["Name"] = self.header.project_title_input.text()
        self.project_info["StartDate"] = self.edit_project_info.get_timestamptz()
        self.project_info["Description"] = self.edit_project_info.get_description()
        print("Starting save")
        removed_uids = set(self.initial_tracks.keys())-set(self.selected_tracks.keys())
        api.delete_project_map_rows(self.client, By.UID, list(removed_uids), self.project_info["Slug"])

        project_data = flatten_project_data(self.project_info)
        api.upsert_projects(self.client, project_data)
        print(self.selected_tracks)
        map_data = flatten_selected_tracks(self.selected_tracks)
        api.upsert_maps(self.client, map_data)

        project_map_data = construct_project_map_rows(self.selected_tracks.keys(), self.project_info["Slug"])
        api.upsert_project_map_rows(self.client, project_map_data)
        print("Save complete")
        self.initial_tracks = self.selected_tracks.copy()

    def handle_edit_focus_change(self, focus: str):
        match focus:
            case "TRACKS":
                self.stacked_widget.setCurrentIndex(0)
            case "PROJECT":
                self.stacked_widget.setCurrentIndex(1)

    def load_mock_data(self):
        mock_results = [
            {"TrackName": "Track #1", "Authors": [{"UserId": 123808, "Name": "Author 1"}], "AuthorTime": 30520, "TrackId": 1582819, "UpdatedAt": "2022-02-05T"},
        ]
        self.results_panel.populate_table(mock_results, set(self.selected_tracks.keys()))
