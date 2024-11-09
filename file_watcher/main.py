import logging
import re
import time
import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer


@dataclass
class FileState:
    """Stores metadata about a file"""

    modified_time: float
    size: int
    hash: str = ""


class CustomEventHandler(FileSystemEventHandler):
    def __init__(self, callbacks: dict[str, Callable]) -> None:
        self._callbacks = callbacks
        super().__init__()

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if not event.is_directory:
            self._callbacks["created"](event.src_path)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if not event.is_directory:
            self._callbacks["modified"](event.src_path)

    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        if not event.is_directory:
            self._callbacks["deleted"](event.src_path)


class FileSystemWatcher:
    def __init__(self, directory: str, patterns: list[str] | None = None) -> None:
        self.directory = Path(directory)
        self.patterns = patterns or {"*"}  # Defaults to watching all files
        self.file_state: dict[str, FileState] = {}
        self._logger = self._setup_logger()

        self._callbacks = {
            "created": self._handle_created,
            "modified": self._handle_modified,
            "deleted": self._handled_deleted,
        }

        self.event_handler = CustomEventHandler(self._callbacks)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, str(self.directory), recursive=True)

    def _setup_logger(self) -> logging.Logger:
        """Configure logger for the file watcher"""
        logger = logging.getLogger("FileWatcher")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _get_file_checksum(self, file_path) -> str:
        block_size = 4096
        hash = hashlib.blake2b()

        with open(file_path, "rb") as file:
            for block in iter(lambda: file.read(block_size), b""):
                hash.update(block)
        return hash.hexdigest()

    def _is_file_path_allowed_by_pattern(self, file_path) -> bool:
        allowed = []
        for pattern in self.patterns:
            match = re.compile(rf"{pattern}").search(file_path)
            allowed.append(match)
        return any(allowed)

    def _get_file_state(self, file_path: str) -> FileState | None:
        """Get current state of a file"""
        if "git" in file_path:
            return None
        path = Path(file_path)
        if path.exists() and self._is_file_path_allowed_by_pattern(file_path):
            return FileState(
                modified_time=path.stat().st_mtime,
                size=path.stat().st_size,
                hash=self._get_file_checksum(file_path),
            )
        return None

    def _handle_created(self, file_path: str) -> None:
        """Handle file creation events"""
        self._logger.info(f"File created: {file_path}")
        if file_state := self._get_file_state(file_path):
            self.file_state[file_path] = file_state

    def _handle_modified(self, file_path: str) -> None:
        """Handle file modifications events"""
        new_state = None
        if file_state := self._get_file_state(file_path):
            new_state = file_state
        else:
            return

        if file_path in self.file_state:
            old_state = self.file_state[file_path]
            if new_state.modified_time != old_state.modified_time:
                self._logger.info(f"File modified: {file_path}")
                self._logger.info(
                    f"Size changed from {old_state.size} to {new_state.size} bytes"
                )
        self.file_state[file_path] = new_state

    def _handled_deleted(self, file_path: str) -> None:
        """Handle file deletion events"""
        self._logger.info(f"File deleted: {file_path}")
        self.file_state.pop(file_path, None)

    def start(self):
        """Start watching the directory"""
        self._logger.info(f"Starting to watch the directory: {self.directory}")
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop watching the directory"""
        self.observer.stop()
        self.observer.join()
        self._logger.info("Stopped watching directory")


if __name__ == "__main__":
    import sys

    args = sys.argv
    dir = args[1]
    pattern = args[2:]
    watcher = FileSystemWatcher(dir, pattern)
    try:
        watcher.start()
    except KeyboardInterrupt:
        watcher.stop()
