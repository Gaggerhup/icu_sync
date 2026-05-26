from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QAbstractItemView,
    QVBoxLayout,
    QWidget,
)

from app_locale_lib import apply_widget_number_locale


class MainWindowUI:
    patient_columns = [
        "",
        "admit_date",
        "cid",
        "an",
        "fullname",
        "current agey",
        "age mon",
        "porv_dx",
        "ward",
        "action",
    ]

    def setup_ui(self, window: QMainWindow) -> None:
        window.setWindowTitle("ICU-Sync")
        window.resize(1280, 960)

        central_widget = QWidget(window)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        header_panel = QFrame()
        header_panel.setObjectName("headerPanel")
        header_layout = QHBoxLayout(header_panel)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(10)

        title = QLabel("ICU-Sync")
        title.setObjectName("titleLabel")

        admit_label = QLabel("วัน admit ระหว่างวันที่")
        self.admit_from_date = QDateEdit()
        self.admit_from_date.setCalendarPopup(True)
        self.admit_from_date.setDisplayFormat("yyyy-MM-dd")
        self.admit_from_date.setDate(QDate.currentDate())
        apply_widget_number_locale(self.admit_from_date)

        range_label = QLabel("ถึง")
        self.admit_to_date = QDateEdit()
        self.admit_to_date.setCalendarPopup(True)
        self.admit_to_date.setDisplayFormat("yyyy-MM-dd")
        self.admit_to_date.setDate(QDate.currentDate())
        apply_widget_number_locale(self.admit_to_date)

        ward_label = QLabel("Ward")
        self.ward_filter_combo = QComboBox()
        self.ward_filter_combo.setMinimumWidth(180)
        self.ward_filter_combo.addItem("All wards", "")

        self.load_patient_button = QPushButton("Load Patient")
        self.settings_button = QPushButton("Settings")

        header_layout.addWidget(title)
        header_layout.addSpacing(18)
        header_layout.addWidget(admit_label)
        header_layout.addWidget(self.admit_from_date)
        header_layout.addWidget(range_label)
        header_layout.addWidget(self.admit_to_date)
        header_layout.addWidget(ward_label)
        header_layout.addWidget(self.ward_filter_combo)
        header_layout.addWidget(self.load_patient_button)
        header_layout.addStretch(1)
        header_layout.addWidget(self.settings_button)

        self.connection_label = QLabel()
        self.connection_label.setObjectName("connectionLabel")

        self.patient_table = QTableWidget(0, len(self.patient_columns))
        self.patient_table.setHorizontalHeaderLabels(self.patient_columns)
        self.patient_table.setSortingEnabled(True)
        self.patient_table.setAlternatingRowColors(True)
        self.patient_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.patient_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.patient_table.verticalHeader().setVisible(False)
        self.patient_table.horizontalHeader().setSectionsClickable(True)
        self.patient_table.horizontalHeader().setSortIndicatorShown(True)
        self.patient_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.patient_table.horizontalHeader().setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.Stretch,
        )
        self.patient_table.setColumnWidth(0, 42)
        self.patient_table.setColumnWidth(1, 110)
        self.patient_table.setColumnWidth(2, 140)
        self.patient_table.setColumnWidth(3, 110)
        self.patient_table.setColumnWidth(5, 105)
        self.patient_table.setColumnWidth(6, 90)
        self.patient_table.setColumnWidth(8, 140)
        self.patient_table.setColumnWidth(9, 96)

        bottom_layout = QHBoxLayout()
        self.selected_patient_label = QLabel("Selected: 0")
        self.sync_patient_button = QPushButton("Sync Patient to ICUCONS")
        self.sync_patient_button.setEnabled(False)
        bottom_layout.addWidget(self.selected_patient_label)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.sync_patient_button)

        root_layout.addWidget(header_panel)
        root_layout.addWidget(self.connection_label)
        root_layout.addWidget(self.patient_table, 1)
        root_layout.addLayout(bottom_layout)

        window.setCentralWidget(central_widget)
        window.setStatusBar(QStatusBar(window))

        window.setStyleSheet(
            """
            QFrame#headerPanel {
                background: #f5f7fa;
                border: 1px solid #d8dee9;
                border-radius: 6px;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: 700;
            }
            QLabel#connectionLabel {
                color: #4b5563;
            }
            QPushButton {
                min-height: 30px;
                padding: 4px 12px;
            }
            QTableWidget {
                gridline-color: #e5e7eb;
                selection-background-color: #dbeafe;
            }
            """
        )
