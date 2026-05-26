from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from hosxp_lib import HosxpClient
from setting_lib import (
    AppSettings,
    DEFAULT_ICUCONS_API_ENDPOINT,
    normalize_icucons_api_endpoint,
    split_icucons_api_endpoint,
)


class ConnectionTestWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings

    def run(self) -> None:
        try:
            HosxpClient(self.settings).test_connection()
        except Exception as exc:
            self.finished.emit(str(exc))
        else:
            self.finished.emit("")


class DlgSetting(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(560, 420)

        self.hosxp_host_input = QLineEdit(settings.hosxp_host)
        self.hosxp_port_input = QSpinBox()
        self.hosxp_port_input.setRange(1, 65535)
        self.hosxp_port_input.setValue(settings.hosxp_port)
        self.hosxp_database_input = QLineEdit(settings.hosxp_database)
        self.hosxp_user_input = QLineEdit(settings.hosxp_user)
        self.hosxp_password_input = QLineEdit(settings.hosxp_password)
        self.hosxp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        endpoint = settings.icucons_api_endpoint or DEFAULT_ICUCONS_API_ENDPOINT
        self.icucons_api_endpoint_input = QLineEdit(endpoint)
        self.icucons_api_endpoint_input.setPlaceholderText(DEFAULT_ICUCONS_API_ENDPOINT)
        self.icucons_api_token_input = QLineEdit(settings.icucons_api_token)
        self.icucons_api_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.icucons_timeout_input = QSpinBox()
        self.icucons_timeout_input.setRange(1, 300)
        self.icucons_timeout_input.setValue(settings.icucons_timeout)
        self._test_thread: QThread | None = None
        self._test_worker: ConnectionTestWorker | None = None

        form_layout = QFormLayout()
        form_layout.addRow("HOSxP host", self.hosxp_host_input)
        form_layout.addRow("HOSxP port", self.hosxp_port_input)
        form_layout.addRow("HOSxP database", self.hosxp_database_input)
        form_layout.addRow("HOSxP user", self.hosxp_user_input)
        form_layout.addRow("HOSxP password", self.hosxp_password_input)
        form_layout.addRow("ICUCONS API endpoint", self.icucons_api_endpoint_input)
        form_layout.addRow("ICUCONS API token", self.icucons_api_token_input)
        form_layout.addRow("ICUCONS timeout (sec)", self.icucons_timeout_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.test_connection_button = QPushButton("ทดสอบเชื่อมต่อ")
        self.test_connection_button.clicked.connect(self.test_connection)
        test_layout = QHBoxLayout()
        test_layout.addWidget(self.test_connection_button)
        test_layout.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addLayout(test_layout)
        layout.addWidget(buttons)

    def test_connection(self) -> None:
        if self._test_thread and self._test_thread.isRunning():
            return

        self.test_connection_button.setEnabled(False)
        self.test_connection_button.setText("กำลังทดสอบ...")
        self._test_thread = QThread(self)
        self._test_worker = ConnectionTestWorker(self.values())
        self._test_worker.moveToThread(self._test_thread)
        self._test_thread.started.connect(self._test_worker.run)
        self._test_worker.finished.connect(self.connection_test_finished)
        self._test_worker.finished.connect(self._test_thread.quit)
        self._test_worker.finished.connect(self._test_worker.deleteLater)
        self._test_thread.finished.connect(self.connection_test_thread_finished)
        self._test_thread.finished.connect(self._test_thread.deleteLater)
        self._test_thread.start()

    def connection_test_finished(self, error_message: str) -> None:
        self.test_connection_button.setText("ทดสอบเชื่อมต่อ")
        self.test_connection_button.setEnabled(True)
        self._test_worker = None

        if error_message:
            QMessageBox.critical(self, "เชื่อมต่อ HOSxP ไม่สำเร็จ", error_message)
            return

        QMessageBox.information(
            self,
            "เชื่อมต่อ HOSxP สำเร็จ",
            "เชื่อมต่อ HOSxP สำเร็จ",
        )

    def connection_test_thread_finished(self) -> None:
        self._test_thread = None

    def values(self) -> AppSettings:
        api_endpoint = normalize_icucons_api_endpoint(
            self.icucons_api_endpoint_input.text().strip()
            or DEFAULT_ICUCONS_API_ENDPOINT
        )
        base_url, api_path = split_icucons_api_endpoint(api_endpoint)

        return AppSettings(
            hosxp_host=self.hosxp_host_input.text().strip(),
            hosxp_port=self.hosxp_port_input.value(),
            hosxp_database=self.hosxp_database_input.text().strip(),
            hosxp_user=self.hosxp_user_input.text().strip(),
            hosxp_password=self.hosxp_password_input.text(),
            icucons_api_endpoint=api_endpoint,
            icucons_base_url=base_url,
            icucons_api_path=api_path,
            icucons_api_token=self.icucons_api_token_input.text(),
            icucons_timeout=self.icucons_timeout_input.value(),
        )
