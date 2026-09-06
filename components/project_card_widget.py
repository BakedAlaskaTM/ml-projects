from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, 
    QWidget, QLabel
)

class ProjectCardWidget(QWidget):
    def __init__(self):
        super().__init__()

        card_layout = QVBoxLayout()

        self.project_name_label = QLabel()
        self.project_slug_label = QLabel()
        self.status_label = QLabel()