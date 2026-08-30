"""
watcher.py - monitors the watched folder and moves new files according to
rules.py, recording each move in db.py so it can be tagged later.
"""
import shutil
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import rules
import db

SETTLE_SECONDS = 1.5  # wait for file to finish writing before moving it


def _unique_destination(dest_folder: Path, filename: str) -> Path:
    dest_folder.mkdir(parents=True, exist_ok=True)
    candidate = dest_folder / filename
    if not candidate.exists():
        return candidate
    stem, suffix = Path(filename).stem, Path(filename).suffix
    i = 1
    while True:
        candidate = dest_folder / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def organize_file(file_path: Path, output_base: Path, log=print):
    if not file_path.exists() or not file_path.is_file():
        return
    try:
        size1 = file_path.stat().st_size
        time.sleep(SETTLE_SECONDS)
        size2 = file_path.stat().st_size
        if size1 != size2:
            return
    except FileNotFoundError:
        return

    all_rules = rules.load_rules()
    rule_name, destination = rules.classify(file_path, all_rules)
    dest_folder = output_base / destination
    dest_path = _unique_destination(dest_folder, file_path.name)

    try:
        shutil.move(str(file_path), str(dest_path))
    except Exception as e:
        log(f"Failed to move {file_path.name}: {e}")
        return

    db.record_file(str(dest_path), dest_path.name, rule_name)
    log(f"Organized: {file_path.name} -> {destination}/ ({rule_name or 'Unsorted'})")


class OrganizerHandler(FileSystemEventHandler):
    def __init__(self, output_base: Path, log=print):
        self.output_base = output_base
        self.log = log

    def on_created(self, event):
        if event.is_directory:
            return
        src = Path(event.src_path)
        try:
            src.relative_to(self.output_base)
            return
        except ValueError:
            pass
        organize_file(src, self.output_base, self.log)


def start_watcher(watch_folder: str, output_base: str, log=print):
    watch_path = Path(watch_folder)
    output_path = Path(output_base)
    output_path.mkdir(parents=True, exist_ok=True)

    for f in watch_path.iterdir():
        if f.is_file():
            organize_file(f, output_path, log)

    handler = OrganizerHandler(output_path, log)
    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=False)
    observer.start()
    log(f"Watching {watch_path} -> organizing into {output_path}")
    return observer
