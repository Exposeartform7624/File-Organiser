# File Organizer

A Windows desktop app that watches a folder and automatically sorts new
files into subfolders based on rules you define (extension, filename
text, size, or age). Tags are manual after a file is organized, tag it
yourself and search by tag later, even after it's been moved.

## Running from source

1. Install Python 3.10+ from python.org (check "Add to PATH" during install).
2. Open Command Prompt in this folder and run:
   ```
   pip install -r requirements.txt
   ```
3. Launch the app:
   ```
   python main.py
   ```

## How it works

- **Start Watching** — nothing gets touched until you click this. The app
  opens with watching **stopped** (the status dot next to the button is
  grey and reads "stopped"). Click "Start Watching" in the top-right of
  the window whenever you're ready to begin — the dot turns green and
  reads "watching." Click "Stop Watching" any time to pause it again.
  Closing the app also stops it.
- **Settings tab** — pick the folder to watch (e.g. your Downloads folder)
  and the output base folder where organized subfolders will be created.
  If watching is already running, "Save & Restart Watching" applies your
  changes immediately; if it's stopped, it just saves your settings and
  waits for you to click "Start Watching."
- **Rules tab** — define rules, top to bottom. The first matching rule wins.
  Each rule can match on: extensions, filename-contains text, min/max size
  in KB, and file age in days. Set a destination subfolder like
  `Documents/Invoices`. Files that match nothing land in `Unsorted`.
- **Files & Tags tab** every organized file appears here. Select one and
  use "Add Tag" / "Remove Tag" to tag it manually. Use the tag filter box
  to find everything tagged, say, `important`.

Once you click "Start Watching," any files already sitting in the watched
folder get organized immediately, and anything dropped in afterward is
picked up live — for as long as watching stays on.

## Starting the app, step by step

1. Launch the app (`python main.py`, or double-click `FileOrganizer.exe`
   if you built the standalone version).
2. On first launch, a Help window walks you through the basics — you can
   reopen it anytime with the "Help" button.
3. Go to the **Settings tab** and confirm (or change) the watched folder
   and output folder, then click "Save & Restart Watching" if you changed
   anything.
4. Go to the **Rules tab** and set up rules if you want something other
   than the default Images/Videos/Documents sorting.
5. Click **Start Watching** in the top-right corner. The status dot turns
   green and existing files in the watched folder get organized right
   away; new files get picked up as they arrive.
6. Click **Stop Watching** whenever you want to pause it — your rules and
   settings stay saved for next time.

## Getting a standalone .exe (no Python required to run it)

**Option A — download the latest release (easiest, no build needed):**

Grab the prebuilt `FileOrganizer.exe` straight from the Releases page:

[**Download latest release**](https://github.com/souvikdey2396-byte/File-Organiser/releases/latest)

No Python install required just download and run.

**Option B — build it yourself locally on Windows:**
```
pip install -r requirements.txt
pip install pyinstaller
pyinstaller file_organizer.spec --noconfirm
```
The exe appears at `dist\FileOrganizer.exe`. Or just double-click `build.bat`.

### Notes on the exe
- First launch may take a couple seconds longer than the Python version
  (PyInstaller unpacks itself into a temp folder each run).
- `rules.json`, `config.json`, and `fileorganizer.db` are created next to
  the exe on first run, same as with the Python version.
- See "Is this safe to use?" below for why Windows may flag the exe on
  first run.

## Is this safe to use?

Yes. If Windows Defender / SmartScreen or your browser flags the exe as
"unrecognized" or from an "unknown publisher," that's expected and not a
sign anything is wrong — it's a false positive that happens to nearly
every small, independently-built Windows app that isn't code-signed.

**Why it happens:** Windows and antivirus tools build trust for an exe
based on how many other people have already run it and whether it's
signed with a paid code-signing certificate. A freshly built, unsigned
exe like this one has neither yet, so it gets flagged automatically —
regardless of what the code actually does.

**What you'll see and how to proceed:**
- **Windows SmartScreen** — "Windows protected your PC" / unknown
  publisher. Click "More info," then "Run anyway."
- **Browser download warning** (Chrome/Edge) — may call the download
  "suspicious." Click the small arrow next to the blocked download and
  choose "Keep" or "Keep anyway."
- **Windows Defender** — if it quarantines or flags the file, you can
  allow it (or restore it from quarantine) via Windows Security →
  Virus & threat protection → Protection history.

You only need to do this once per machine, the first time you run a
newly built exe. Code-signing (which would remove these warnings
entirely) costs money for a certificate and isn't required for the app
to work correctly — it's purely about publisher reputation, not safety
of the code itself.

If you'd rather avoid the warnings altogether, run the app from source
with `python main.py` instead of the exe — see "Running from source"
above.

## Notes

- Rules are stored in `rules.json`, settings in `config.json`, and the
  file/tag database in `fileorganizer.db` all created automatically in
  this folder (or next to the exe) on first run. Back these up if you want
  to preserve your setup.
- If two organized files would have the same name, the app appends
  `(1)`, `(2)`, etc. rather than overwriting.
- To run the organizer automatically at login (Python version), create a
  shortcut to `pythonw.exe main.py` (use `pythonw.exe` instead of
  `python.exe` to avoid a console window) and place it in your Startup
  folder (`shell:startup` in the Run dialog). For the exe version, just
  place a shortcut to `FileOrganizer.exe` there instead.
