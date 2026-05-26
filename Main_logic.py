import sys
from typing import Any

from PyQt6.QtCore import QObject, QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
)

from app_locale_lib import configure_app_locale
from DlgPatientDetail import DlgPatientDetail
from DlgSetting import DlgSetting
from hosxp_lib import HosxpClient, HosxpConnectionError
from icuconsult_api_lib import IcuconsultApiClient
from Main_ui import MainWindowUI
from setting_lib import AppSettings, SettingsLogic


class PatientSchemaFetchWorker(QObject):
    finished = pyqtSignal(list)
    failed = pyqtSignal(str, str)

    def __init__(self, settings, patients: list[dict[str, Any]]) -> None:
        super().__init__()
        self.settings = settings
        self.patients = patients

    def run(self) -> None:
        try:
            client = HosxpClient(self.settings)
            api_client = IcuconsultApiClient(self.settings)
            payloads = []
            results = []
            for patient in self.patients:
                an = str(patient.get("an", ""))
                hn = str(patient.get("hn", ""))
                payload = client.fetch_web_case_payload(an, hn)
                payloads.append(payload)
                results.append(api_client.sync_case(payload))
        except HosxpConnectionError as exc:
            self.failed.emit("เชื่อมต่อ HOSxP ไม่สำเร็จ", str(exc))
            return
        except Exception as exc:
            self.failed.emit("ICUCONS sync failed", str(exc))
            return
        self.finished.emit([payloads, results])


class MainWindowLogic(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = MainWindowUI()
        self.ui.setup_ui(self)

        self.settings_logic = SettingsLogic()
        self.startup_warning = ""
        try:
            self.app_settings = self.settings_logic.load()
        except Exception as exc:
            self.app_settings = AppSettings()
            self.startup_warning = f"Load settings failed: {exc}"
        self.patient_rows: list[dict[str, Any]] = []
        self.schema_payloads: list[dict[str, Any]] = []
        self.schema_fetch_thread: QThread | None = None
        self.schema_fetch_worker: PatientSchemaFetchWorker | None = None

        self.ui.settings_button.clicked.connect(self.open_settings)
        self.ui.load_patient_button.clicked.connect(self.load_patients)
        self.ui.sync_patient_button.clicked.connect(self.sync_selected_patients)
        self.ui.ward_filter_combo.currentIndexChanged.connect(self.apply_ward_filter)
        self.ui.patient_table.itemChanged.connect(self.update_sync_button_state)
        self.refresh_connection_summary()
        self.statusBar().showMessage(
            "Ready. HOSxP database will connect when you load patients.",
            5000,
        )
        if self.startup_warning:
            QTimer.singleShot(0, self.show_startup_warning)

    def refresh_connection_summary(self) -> None:
        self.ui.connection_label.setText(
            "HOSxP: "
            f"{self.app_settings.hosxp_user or '(no user)'}"
            f"@{self.app_settings.hosxp_host}:{self.app_settings.hosxp_port}"
            f"/{self.app_settings.hosxp_database}"
            " | ICUCONS: "
            f"{self.app_settings.icucons_api_endpoint}"
        )

    def show_error_message(self, default_title: str, exc: Exception) -> None:
        title = (
            "เชื่อมต่อ HOSxP ไม่สำเร็จ"
            if isinstance(exc, HosxpConnectionError)
            else default_title
        )
        QMessageBox.critical(self, title, str(exc))

    def show_startup_warning(self) -> None:
        QMessageBox.warning(
            self,
            "Startup warning",
            f"{self.startup_warning}\n\nThe main screen is ready with default settings.",
        )

    def open_settings(self) -> None:
        dialog = DlgSetting(self.app_settings, self)
        if dialog.exec():
            self.app_settings = dialog.values()
            self.settings_logic.save(self.app_settings)
            self.refresh_connection_summary()
            self.statusBar().showMessage("Settings saved.", 3000)

    def load_patients(self) -> None:
        start_date = self.ui.admit_from_date.date().toString("yyyy-MM-dd")
        end_date = self.ui.admit_to_date.date().toString("yyyy-MM-dd")

        if self.ui.admit_from_date.date() > self.ui.admit_to_date.date():
            QMessageBox.warning(
                self,
                "Invalid date range",
                "Start admit date must be before or equal to end admit date.",
            )
            return

        self.statusBar().showMessage("Loading admitted patients...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            rows = HosxpClient(self.app_settings).fetch_admitted_patients(
                start_date,
                end_date,
            )
        except Exception as exc:
            QApplication.restoreOverrideCursor()
            self.show_error_message("Load patient failed", exc)
            self.statusBar().showMessage("Load patient failed.", 5000)
            return

        QApplication.restoreOverrideCursor()
        self.patient_rows = rows
        self.refresh_ward_filter_options(rows)
        filtered_rows = self.filtered_patient_rows()
        self.populate_patient_table(filtered_rows)
        self.statusBar().showMessage(
            f"Loaded {len(rows)} patient(s), showing {len(filtered_rows)}.",
            5000,
        )

    def refresh_ward_filter_options(self, rows: list[dict[str, Any]]) -> None:
        current_ward = self.ui.ward_filter_combo.currentData() or ""
        wards = sorted(
            {
                str(row.get("ward", "")).strip()
                for row in rows
                if str(row.get("ward", "")).strip()
            }
        )

        self.ui.ward_filter_combo.blockSignals(True)
        self.ui.ward_filter_combo.clear()
        self.ui.ward_filter_combo.addItem("All wards", "")
        for ward in wards:
            self.ui.ward_filter_combo.addItem(ward, ward)

        selected_index = self.ui.ward_filter_combo.findData(current_ward)
        self.ui.ward_filter_combo.setCurrentIndex(selected_index if selected_index >= 0 else 0)
        self.ui.ward_filter_combo.blockSignals(False)

    def filtered_patient_rows(self) -> list[dict[str, Any]]:
        selected_ward = self.ui.ward_filter_combo.currentData() or ""
        if not selected_ward:
            return self.patient_rows
        return [
            row
            for row in self.patient_rows
            if str(row.get("ward", "")).strip() == selected_ward
        ]

    def apply_ward_filter(self) -> None:
        filtered_rows = self.filtered_patient_rows()
        self.populate_patient_table(filtered_rows)
        selected_ward = self.ui.ward_filter_combo.currentData() or "All wards"
        self.statusBar().showMessage(
            f"{selected_ward}: showing {len(filtered_rows)} of {len(self.patient_rows)} patient(s).",
            5000,
        )

    def populate_patient_table(self, rows: list[dict[str, Any]]) -> None:
        table = self.ui.patient_table
        table.setSortingEnabled(False)
        table.blockSignals(True)
        table.setRowCount(0)

        for row_index, patient in enumerate(rows):
            table.insertRow(row_index)

            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            check_item.setCheckState(Qt.CheckState.Unchecked)
            check_item.setData(Qt.ItemDataRole.UserRole, patient)
            table.setItem(row_index, 0, check_item)

            values = [
                patient.get("admit_date", ""),
                patient.get("cid", ""),
                patient.get("an", ""),
                patient.get("fullname", ""),
                patient.get("current_agey", ""),
                patient.get("age_mon", ""),
                patient.get("porv_dx", ""),
                patient.get("ward", ""),
            ]
            for column_offset, value in enumerate(values, start=1):
                item = QTableWidgetItem("" if value is None else str(value))
                item.setData(Qt.ItemDataRole.UserRole, patient)
                table.setItem(row_index, column_offset, item)

            action_button = QPushButton("View")
            action_button.clicked.connect(
                lambda checked=False, selected_patient=patient: self.open_patient_detail(
                    selected_patient
                )
            )
            table.setItem(row_index, 9, QTableWidgetItem("View"))
            table.setCellWidget(row_index, 9, action_button)

        table.blockSignals(False)
        table.setSortingEnabled(True)
        self.update_sync_button_state()

    def update_sync_button_state(self) -> None:
        selected_count = len(self.selected_patients())
        self.ui.selected_patient_label.setText(f"Selected: {selected_count}")
        self.ui.sync_patient_button.setEnabled(selected_count > 0)

    def selected_patients(self) -> list[dict[str, Any]]:
        selected = []
        for row_index in range(self.ui.patient_table.rowCount()):
            item = self.ui.patient_table.item(row_index, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                patient = item.data(Qt.ItemDataRole.UserRole)
                if patient:
                    selected.append(patient)
        return selected

    def open_patient_detail(self, patient: dict[str, Any]) -> None:
        self.statusBar().showMessage(f"Loading detail for AN {patient.get('an', '')}...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            client = HosxpClient(self.app_settings)
            an = str(patient.get("an", ""))
            hn = str(patient.get("hn", ""))
            dialog = DlgPatientDetail(
                patient,
                client.fetch_rx(an),
                client.fetch_vital_sign(an, hn),
                client.fetch_lab(an, hn),
                self,
            )
        except Exception as exc:
            QApplication.restoreOverrideCursor()
            self.show_error_message("Load patient detail failed", exc)
            self.statusBar().showMessage("Load patient detail failed.", 5000)
            return

        QApplication.restoreOverrideCursor()
        self.statusBar().clearMessage()
        dialog.exec()

    def sync_selected_patients(self) -> None:
        selected = self.selected_patients()
        if not selected:
            return

        self.ui.sync_patient_button.setEnabled(False)
        self.ui.load_patient_button.setEnabled(False)
        self.statusBar().showMessage(
            f"Syncing {len(selected)} patient(s) from HOSxP to ICUCONS..."
        )

        self.schema_fetch_thread = QThread(self)
        self.schema_fetch_worker = PatientSchemaFetchWorker(self.app_settings, selected)
        self.schema_fetch_worker.moveToThread(self.schema_fetch_thread)
        self.schema_fetch_thread.started.connect(self.schema_fetch_worker.run)
        self.schema_fetch_worker.finished.connect(self.handle_schema_fetch_finished)
        self.schema_fetch_worker.failed.connect(self.handle_schema_fetch_failed)
        self.schema_fetch_worker.finished.connect(self.schema_fetch_thread.quit)
        self.schema_fetch_worker.failed.connect(self.schema_fetch_thread.quit)
        self.schema_fetch_thread.finished.connect(self.schema_fetch_worker.deleteLater)
        self.schema_fetch_thread.finished.connect(self.schema_fetch_thread.deleteLater)
        self.schema_fetch_thread.finished.connect(self.clear_schema_fetch_thread)
        self.schema_fetch_thread.start()

    def handle_schema_fetch_finished(self, result: list[Any]) -> None:
        payloads = result[0]
        sync_results = result[1]
        self.schema_payloads = payloads
        self.ui.load_patient_button.setEnabled(True)
        self.update_sync_button_state()
        total_vitals = sum(len(payload["case_vital"]) for payload in payloads)
        total_labs = sum(len(payload["case_lab"]) for payload in payloads)
        total_meds = sum(len(payload["case_medication"]) for payload in payloads)
        case_ids = ", ".join(
            item.case_id for item in sync_results if getattr(item, "case_id", None)
        )
        QMessageBox.information(
            self,
            "ICUCONS sync complete",
            "Synced HOSxP data into ICUCONS web database schema.\n"
            f"Case(s): {len(payloads)}\n"
            f"Vital rows: {total_vitals}\n"
            f"Lab rows: {total_labs}\n"
            f"Medication rows: {total_meds}\n"
            f"ICUCONS case id(s): {case_ids or '-'}",
        )
        self.statusBar().showMessage(
            f"Synced {len(payloads)} patient(s) to ICUCONS.",
            5000,
        )

    def handle_schema_fetch_failed(self, title: str, message: str) -> None:
        self.ui.load_patient_button.setEnabled(True)
        self.update_sync_button_state()
        QMessageBox.critical(self, title, message)
        self.statusBar().showMessage(f"{title}.", 5000)

    def clear_schema_fetch_thread(self) -> None:
        self.schema_fetch_thread = None
        self.schema_fetch_worker = None


def create_app() -> QApplication:
    configure_app_locale()
    app = QApplication(sys.argv)
    app.setOrganizationName("PLKHealth")
    app.setApplicationName("ICU-Sync")
    return app


def main() -> None:
    app = create_app()
    app.setQuitOnLastWindowClosed(True)
    window = MainWindowLogic()
    app._main_window = window
    window.showNormal()
    window.raise_()
    window.activateWindow()
    QTimer.singleShot(0, window.raise_)
    QTimer.singleShot(0, window.activateWindow)
    print("ICU-Sync window shown.", flush=True)
    sys.exit(app.exec())
