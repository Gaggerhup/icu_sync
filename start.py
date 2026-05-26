import os
import sys
import traceback
from pathlib import Path

import PyQt6


def _configure_qt_plugin_paths() -> None:
    qt_plugins_path = Path(PyQt6.__file__).resolve().parent / "Qt6" / "plugins"
    qt_platforms_path = qt_plugins_path / "platforms"
    if not qt_platforms_path.exists():
        return

    qt_plugins = str(qt_plugins_path)
    qt_platforms = str(qt_platforms_path)
    if not os.environ.get("QT_PLUGIN_PATH"):
        os.environ["QT_PLUGIN_PATH"] = qt_plugins
    if not os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH"):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_platforms
    from PyQt6.QtCore import QCoreApplication

    if qt_plugins not in QCoreApplication.libraryPaths():
        QCoreApplication.addLibraryPath(qt_plugins)
    print(f"Qt plugin path: {qt_plugins}", flush=True)


def _print_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: object,
) -> None:
    print("Unhandled application error:", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)


def _pause_frozen_windows_console() -> None:
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return
    try:
        input("\nPress Enter to close ICU-Sync...")
    except (EOFError, KeyboardInterrupt):
        pass


def main() -> None:
    sys.excepthook = _print_exception
    try:
        print("ICU-Sync starting...", flush=True)
        _configure_qt_plugin_paths()
        from Main_logic import main as app_main

        app_main()
    except SystemExit:
        _pause_frozen_windows_console()
        raise
    except Exception as exc:
        _print_exception(type(exc), exc, exc.__traceback__)
        _pause_frozen_windows_console()
        sys.exit(1)


if __name__ == "__main__":
    main()
