GLOBAL_STYLE = """
QMainWindow { background-color: #e8e8e8; }
QWidget { font-family: 'Arial', sans-serif; font-size: 16px; color: black; }
QLabel { color: black; }
QFrame { background-color: transparent; }

/* Buttons */
QPushButton { 
    background-color: white; 
    border: 1px solid black; 
    border-radius: 10px; 
    padding: 10px 20px; 
    font-size: 24px; 
    color: black; 
}
QPushButton:hover { background-color: #f0f0f0; }
QPushButton:pressed { background-color: #e0e0e0; }
QPushButton:disabled { 
    background-color: #f0f0f0; 
    color: #b8b8b8;
}

/* Radio Toggle Buttons */
QPushButton#tracksRadio, QPushButton#usersRadio { 
    border-radius: 10px; 
    padding: 10px 20px; 
    font-size: 32px; 
}
QPushButton:checked { background-color: black; color: white; }

/* Inputs */
QLineEdit { 
    border: 1px solid black; 
    border-radius: 10px; 
    padding: 8px 12px; 
    font-size: 16px; 
    color: black; 
    background-color: white; 
}
QLineEdit:focus { border: 2px solid black; }

/* Left Selected Scroll Area */
QFrame#selectedTracksFrame { 
    background-color: white;
    border-radius: 10px;
}
QScrollArea { border: none; }
QWidget#scrollContent { background-color: transparent; }
QPushButton#removeBtn { 
    border: none; 
    color: #e53935; 
    font-weight: bold; 
    font-size: 16px; 
    background: transparent; 
    padding: 0 4px; 
}
QPushButton#removeBtn:hover { color: #b71c1c; }

/* Table Widget */
QTableWidget { 
    border: 1px solid black; 
    gridline-color: transparent; 
    background-color: white; 
    alternate-background-color: #f8f8f8; 
    border-top-left-radius: 10px; 
    border-top-right-radius: 10px; 
}
QHeaderView::section { 
    background-color: #2b2b2b; 
    color: white; 
    padding: 10px; 
    font-weight: bold; 
}
/* Round top-left corner of the header */
QHeaderView::section:first {
    border-top-left-radius: 9px;
}

/* Round top-right corner of the header */
QHeaderView::section:last {
    border-top-right-radius: 9px;
}

/* Table Checkbox Indicator Base */
QTableWidget::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #767676;
    background-color: #ffffff;
}

/* Unchecked State */
QTableWidget::indicator:unchecked {
    background-color: #ffffff;
    border: 1px solid #767676;
}

/* Checked State - Solid Black Fill */
QTableWidget::indicator:checked {
    background-color: #000000;
    border: 1px solid #000000;
}

/* Optional Hover Feedback */
QTableWidget::indicator:unchecked:hover {
    border-color: #000000;
}

/* Styling for selected cells/rows */
QTableWidget::item:selected {
    background-color: #2563eb;  /* Selected background color */
    color: #ffffff;              /* Selected text color */
}
QTableWidget::item:hover {
    background-color: #2563eb;
    color: #ffffff;              /* Selected text color */
}
QTableWidget {
    outline: none; /* Removes the dotted focus rectangle around selected cells */
}
"""