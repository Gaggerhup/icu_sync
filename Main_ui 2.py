from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


class MainWindowUI:
    def setup_ui(self, window: QMainWindow) -> None:
        window.setWindowTitle("ICU-Sync")
        window.resize(1280, 960)

        central_widget = QWidget(window)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        title = QLabel("ICU-Sync")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        subtitle = QLabel(
            "Sync ICU patient data from HOSxP to ICU consultation service."
        )
        subtitle.setWordWrap(True)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        self.settings_button = QPushButton("Settings")
        self.sync_button = QPushButton("Start Sync")
        self.sync_button.setDefault(True)

        button_row.addWidget(self.settings_button)
        button_row.addWidget(self.sync_button)
        button_row.addStretch(1)

        self.connection_label = QLabel()
        self.connection_label.setWordWrap(True)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(button_row)
        root_layout.addWidget(self.connection_label)
        root_layout.addStretch(1)

        window.setCentralWidget(central_widget)
        window.setStatusBar(QStatusBar(window))

        window.setStyleSheet(
            """
            QLabel#titleLabel {
                font-size: 28px;
                font-weight: 700;
            }
            QPushButton {
                min-height: 32px;
                padding: 4px 14px;
            }
            """
        )
