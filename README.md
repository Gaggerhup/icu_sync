# ICU-Sync

ระบบ sync ข้อมูลผู้ป่วย ICU จากฐานข้อมูล HOSxP ส่งเข้าสู่ระบบ
https://icucons.plkhealth.go.th

## Development

Install dependencies and create the virtual environment:

```bash
uv sync
```

Run the desktop app:

```bash
uv run start.py
```

Always run the app through this repository's `.venv` managed by `uv`.
Do not run it with a global Python interpreter or another virtual environment.

## Project Layout

- `Main_ui.py` contains the main PyQt6 UI setup.
- `Main_logic.py` contains main window behavior and app startup.
- `start.py` is the application entry point.
- `DlgSetting.py` contains the settings dialog.
- `DlgPatientDetail.py` contains RX, vital sign, and LAB tabs for an admitted patient.
- `hosxp_lib.py` contains HOSxP database query helpers.
- `setting_lib.py` wraps `QSettings` access.

Runtime configuration is stored with `QSettings`.
