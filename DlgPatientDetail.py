from typing import Any

from PyQt6.QtWidgets import (
    QDialog,
    QHeaderView,
    QLabel,
    QAbstractItemView,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class DlgPatientDetail(QDialog):
    def __init__(
        self,
        patient: dict[str, Any],
        rx_rows: list[dict[str, Any]],
        vital_rows: list[dict[str, Any]],
        lab_rows: list[dict[str, Any]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Patient Detail - AN {patient.get('an', '')}")
        self.resize(980, 720)

        title = QLabel(
            f"{patient.get('fullname', '')} | AN {patient.get('an', '')} | "
            f"CID {patient.get('cid', '')}"
        )

        self.tabs = QTabWidget()
        self.rx_table = self._create_table()
        self.vital_table = self._create_table()
        self.lab_table = self._create_table()

        self.tabs.addTab(self._wrap_table(self.rx_table), "RX")
        self.tabs.addTab(self._wrap_table(self.vital_table), "Viatal Sign")
        self.tabs.addTab(self._wrap_table(self.lab_table), "LAB")

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.tabs, 1)

        self.populate_table(self.rx_table, rx_rows)
        self.populate_table(self.vital_table, vital_rows)
        self.populate_table(self.lab_table, lab_rows)

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        return table

    def _wrap_table(self, table: QTableWidget) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(table)
        return widget

    def populate_table(self, table: QTableWidget, rows: list[dict[str, Any]]) -> None:
        table.setSortingEnabled(False)
        table.clear()

        if not rows:
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["No data"])
            table.setRowCount(0)
            table.setSortingEnabled(True)
            return

        columns = list(rows[0].keys())
        table.setColumnCount(len(columns))
        table.setRowCount(len(rows))
        table.setHorizontalHeaderLabels(columns)

        for row_index, row in enumerate(rows):
            for column_index, column in enumerate(columns):
                table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem("" if row[column] is None else str(row[column])),
                )

        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        table.setSortingEnabled(True)
