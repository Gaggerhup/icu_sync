from pathlib import Path

from PyQt6.QtCore import QDir, QLockFile


APP_LOCK_FILE_NAME = "PLKHealth-ICU-Sync.lock"


class SingleInstanceError(RuntimeError):
    pass


def acquire_single_instance_lock() -> QLockFile:
    lock_path = str(Path(QDir.tempPath()) / APP_LOCK_FILE_NAME)
    lock_file = QLockFile(lock_path)
    if not lock_file.tryLock(100):
        raise SingleInstanceError("ICU-Sync is already running.")
    return lock_file
