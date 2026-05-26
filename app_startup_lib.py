import sys
from pathlib import Path


WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_RUN_VALUE_NAME = "ICU-Sync"


def is_windows_startup_supported() -> bool:
    return sys.platform == "win32"


def windows_startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable).resolve()}"'
    start_script = Path(__file__).resolve().parent / "start.py"
    return f'"{Path(sys.executable).resolve()}" "{start_script}"'


def is_windows_startup_enabled() -> bool:
    if not is_windows_startup_supported():
        return False

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY) as key:
            winreg.QueryValueEx(key, WINDOWS_RUN_VALUE_NAME)
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return True


def set_windows_startup_enabled(enabled: bool) -> None:
    if not is_windows_startup_supported():
        return

    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(
                key,
                WINDOWS_RUN_VALUE_NAME,
                0,
                winreg.REG_SZ,
                windows_startup_command(),
            )
            return

        try:
            winreg.DeleteValue(key, WINDOWS_RUN_VALUE_NAME)
        except FileNotFoundError:
            pass
