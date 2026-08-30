"""
watcher.py - monitors the watched folder and moves new files according to
rules.py, recording each move in db.py so it can be tagged later.

IMPORTANT: browsers download files by first writing to a temporary file
(e.g. Chrome's "something.crdownload", Firefox's "something.part") and
only rename it to the real filename once the download finishes. If we
organize that temp file the moment it's created, we yank it out from
under the browser mid-write and corrupt or kill the download. So:
  - temp/partial download extensions are ignored outright on creation
  - the *rename* from temp -> final name (on_moved) is what actually
    triggers organizing, since that's the real "file has arrived" signal
  - as a second safety net, organize_file still re-checks that a file's
    size has stabilized before touching it, in case something else hands
    us a file mid-write through a plain on_created event
"""
import shutil
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import rules
import db

SETTLE_SECONDS = 1.5     # pause between size checks to confirm a file is done writing
SETTLE_RETRIES = 3       # how many consecutive stable checks we require

# Extensions used by browsers/download managers for in-progress downloads.
# Never organize a file still wearing one of these - it isn't finished yet.
IGNORED_TEMP_EXTENSIONS = {
    "crdownload",  # Chrome, Edge, Brave
    "part",        # Firefox
    "partial",     # some download managers
    "download",    # Safari
    "opdownload",  # Opera
    "tmp",
}


def _is_temp_download(file_path: Path) -> bool:
    return file_path.suffix.lower().lstrip(".") in IGNORED_TEMP_EXTENSIONS


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


def _wait_until_settled(file_path: Path) -> bool:
    """Returns True once the file's size has stopped changing across
    SETTLE_RETRIES consecutive checks, or False if the file disappeared
    or never stabilized (still actively being written)."""
    stable_count = 0
    last_size = None
    for _ in range(SETTLE_RETRIES + 2):  # a couple extra attempts as slack
        try:
            size = file_path.stat().st_size
        except FileNotFoundError:
            return False
        if size == last_size:
            stable_count += 1
            if stable_count >= SETTLE_RETRIES:
                return True
        else:
            stable_count = 0
        last_size = size
        time.sleep(SETTLE_SECONDS)
    return False


def organize_file(file_path: Path, output_base: Path, log=print):
    if not file_path.exists() or not file_path.is_file():
        return
    if _is_temp_download(file_path):
        return  # still downloading - wait for the rename to the final name

    if not _wait_until_settled(file_path):
        return  # file vanished or is still being written; skip for now

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

    def _is_inside_output(self, path: Path) -> bool:
        try:
            path.relative_to(self.output_base)
            return True
        except ValueError:
            return False

    def on_created(self, event):
        if event.is_directory:
            return
        src = Path(event.src_path)
        if self._is_inside_output(src):
            return
        organize_file(src, self.output_base, self.log)

    def on_moved(self, event):
        # This fires when a browser renames its temp download file (e.g.
        # "movie.mp4.crdownload" -> "movie.mp4") to its final name - that
        # rename is the real signal the download is complete.
        if event.is_directory:
            return
        dest = Path(event.dest_path)
        if self._is_inside_output(dest):
            return
        organize_file(dest, self.output_base, self.log)


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