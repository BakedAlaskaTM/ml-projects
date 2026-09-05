import sys
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFrame, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QButtonGroup, QAbstractItemView, 
    QFileDialog
)
from supabase import create_client, Client
from dotenv import load_dotenv
from styles import GLOBAL_STYLE
from utils import *
import tmx
import api
import requests
import os

RESULT_COUNT = 21
MAX_CACHE_PAGES = 1000 // RESULT_COUNT # RESULT_COUNT * CACHE_PAGES <= 1000

class HeaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.back_btn = QPushButton("Back to Projects")
        self.back_btn.setFixedWidth(440)
        self.back_btn.setFixedHeight(100)

        self.project_title_input = QLineEdit()
        self.project_title_input.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        self.project_title_input.setFixedWidth(1420)
        self.project_title_input.setFixedHeight(100)

        layout.addWidget(self.back_btn)
        layout.addWidget(self.project_title_input)

class CurrentlySelectedWidget(QFrame):
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

class SearchResultsWidget(QFrame):
    search_triggered = pyqtSignal(str)
    checkbox_toggled = pyqtSignal(str, bool)  # uid, track_name, is_checked
    page_changed = pyqtSignal(int) # +1 for next page, -1 for prev page
    cell_selected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFixedWidth(960)
        self.setFixedHeight(810)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # Top Bar: Search Input + Radio Buttons
        search_bar_layout = QHBoxLayout()
        search_bar_layout.setSpacing(15)

        self.search_input = QLineEdit()
        self.search_input.setFixedHeight(960)
        self.search_input.setFixedHeight(50)
        self.search_input.setPlaceholderText("Search tracks...")
        self.search_input.returnPressed.connect(
            lambda: self.search_triggered.emit(self.search_input.text())
        )

        search_bar_layout.addWidget(self.search_input, stretch=1)

        table_layout = QVBoxLayout()
        table_layout.setSpacing(0)
        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "Track Name", "Author", "AT", "Track Id", "Upload Date"])
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(30)

        # Table Column Widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 45)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        # Pagination Buttons
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(0)
        
        self.prev_btn = QPushButton("Previous page")
        self.next_btn = QPushButton("Next page")
        self.prev_btn.setStyleSheet("border-top-left-radius: 0; border-bottom-right-radius: 0; border-top-right-radius: 0; border: 1px solid black; font-size: 16px")
        self.next_btn.setStyleSheet("border-top-left-radius: 0; border-bottom-left-radius: 0; border-top-right-radius: 0; border: 1px solid black; font-size: 16px")
        self.prev_btn.setFixedHeight(63)
        self.next_btn.setFixedHeight(63)

        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.next_btn)

        main_layout.addLayout(search_bar_layout)
        table_layout.addWidget(self.table, stretch=1)
        table_layout.addLayout(pagination_layout)
        main_layout.addLayout(table_layout)

        # Signals for native item tracking
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.prev_btn.clicked.connect(lambda: self.page_changed.emit(-1))
        self.next_btn.clicked.connect(lambda: self.page_changed.emit(1))
    
    def populate_table(self, data: list, selected_ids: set):
        """Populates table using native checkable QTableWidgetItems."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        for row_idx, track in enumerate(data):
            self.table.insertRow(row_idx)
            self.table.setRowHeight(row_idx, 30)

            # Native Checkbox Item in Column 0
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            
            is_checked = track["TrackId"] in selected_ids
            chk_item.setCheckState(Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)
            
            # Store track data directly inside item metadata
            chk_item.setData(Qt.ItemDataRole.UserRole, track)
            self.table.setItem(row_idx, 0, chk_item)

            # Text columns
            self.table.setItem(row_idx, 1, QTableWidgetItem(track["TrackName"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(track["Authors"][0]["Name"]))
            
            at_item = QTableWidgetItem(format_time(track["AuthorTime"]))
            self.table.setItem(row_idx, 3, at_item)
            
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(track["TrackId"])))
            self.table.setItem(row_idx, 5, QTableWidgetItem(track["UpdatedAt"].split("T")[0]))

        self.table.blockSignals(False)

    def _on_cell_clicked(self, row: int, column: int):
        """Handles Shift+Click range checking when clicking the checkbox column."""
        if column != 0:
            self._highlight_row(row)
            return

        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.ShiftModifier and self.last_clicked_row is not None:
            start_row = min(self.last_clicked_row, row)
            end_row = max(self.last_clicked_row, row)
            
            target_state = self.table.item(row, 0).checkState()

            self.table.blockSignals(True)
            for r in range(start_row, end_row + 1):
                item = self.table.item(r, 0)
                if item:
                    item.setCheckState(target_state)
                    track = item.data(Qt.ItemDataRole.UserRole)
                    self.checkbox_toggled.emit(track["UId"], target_state == Qt.CheckState.Checked)
            self.table.blockSignals(False)

        self.last_clicked_row = row

    def _highlight_row(self, row: int):
        track_info = {
            "TrackName": self.table.item(row, 1).text(),
            "AuthorName": self.table.item(row, 2).text(),
            "AuthorTime": self.table.item(row, 3).text()
        }
        self.cell_selected.emit(track_info)

    def _on_item_changed(self, item: QTableWidgetItem):
        """Fires when a single checkbox is checked or unchecked."""
        if item.column() != 0:
            return

        track = item.data(Qt.ItemDataRole.UserRole)
        is_checked = (item.checkState() == Qt.CheckState.Checked)

        # Bulk update if multiple rows are highlighted/selected via Shift/Ctrl
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        if item.row() in selected_rows and len(selected_rows) > 1:
            self.table.blockSignals(True)
            for r in selected_rows:
                chk_item = self.table.item(r, 0)
                if chk_item:
                    chk_item.setCheckState(item.checkState())
                    t_data = chk_item.data(Qt.ItemDataRole.UserRole)
                    self.checkbox_toggled.emit(t_data["UId"], is_checked)
            self.table.blockSignals(False)
        else:
            self.checkbox_toggled.emit(track["UId"], is_checked)

    def set_row_checkbox(self, track_id: int, checked: bool):
        """Updates row checkbox state without emitting signals repeatedly."""
        self.table.blockSignals(True)
    
        target_state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 4)
            if id_item and id_item.text().isdigit() and int(id_item.text()) == track_id:
                chk_item = self.table.item(row, 0)
                if chk_item:
                    chk_item.setCheckState(target_state)
                break
                
        self.table.blockSignals(False)

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

class SelectedMapInfoWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(440)
        self.setFixedHeight(290)
        self.setContentsMargins(0, 0, 0, 0)

        info_frame = QFrame(self)
        info_frame.setStyleSheet("background-color: white; border: 1px solid black; border-radius: 10px")
        info_frame.setFixedWidth(440)
        info_frame.setFixedHeight(290)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(20)

        title = QLabel("Selected Map Information")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; border: none; margin-bottom: 10px")
        info_layout.addWidget(title)

        self.track_name = QLabel()
        self.author_name = QLabel()
        self.author_time = QLabel()

        fields = [
            ("Name", self.track_name),
            ("Author", self.author_name),
            ("AT", self.author_time),
        ]

        for label_text, widget in fields:
            widget.setText(f"{label_text} :")
            widget.setStyleSheet("border: none")
            info_layout.addWidget(widget)

        info_layout.addStretch()

    def update_label_text(self, track_info: dict):
        fields = [
            ("Name", track_info["TrackName"], self.track_name),
            ("Author", track_info["AuthorName"], self.author_name),
            ("AT", track_info["AuthorTime"], self.author_time),
        ]

        for label_text, info_text, widget in fields:
            widget.setText(f"{label_text} : {info_text}")

class BottomActionsWidget(QWidget):
    save_button_pressed = pyqtSignal()
    export_button_pressed = pyqtSignal()
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.export_btn = QPushButton("Export JSON")
        self.export_btn.setStyleSheet("font-size: 26px; font-weight: bold; padding: 15px;")
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("font-size: 26px; font-weight: bold; padding: 15px;")

        self.export_btn.clicked.connect(lambda: self.export_button_pressed.emit())
        self.save_btn.clicked.connect(lambda: self.save_button_pressed.emit())
        layout.addWidget(self.export_btn, stretch=1)
        layout.addWidget(self.save_btn, stretch=1)


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
        self.selected_panel = CurrentlySelectedWidget()
        self.results_panel = SearchResultsWidget()
        self.filters_panel = FiltersWidget()
        self.selected_map_info = SelectedMapInfoWidget()
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
    