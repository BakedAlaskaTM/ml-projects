from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, 
)
from libs.utils import format_time

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