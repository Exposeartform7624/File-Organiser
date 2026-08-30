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

- **Settings tab** — pick the folder to watch (e.g. your Downloads folder)
  and the output base folder where organized subfolders will be created.
  Click "Save & Restart Watching" to apply.
- **Rules tab** — define rules, top to bottom. The first matching rule wins.
  Each rule can match on: extensions, filename-contains text, min/max size
  in KB, and file age in days. Set a destination subfolder like
  `Documents/Invoices`. Files that match nothing land in `Unsorted`.
- **Files & Tags tab** every organized file appears here. Select one and
  use "Add Tag" / "Remove Tag" to tag it manually. Use the tag filter box
  to find everything tagged, say, `important`.

Files already sitting in the watched folder when you start the app get
organized immediately; anything dropped in afterward is picked up live.

## Building a standalone .exe (no Python required to run it)

**Option A — build locally on Windows:**
```
pip install -r requirements.txt
pip install pyinstaller
pyinstaller file_organizer.spec --noconfirm
```
The exe appears at `dist\FileOrganizer.exe`. Or just double-click `build.bat`.

**Option B — auto-build via GitHub Actions (recommended for distributing from your repo):**

1. Push this whole folder — including the `.github/workflows/build.yml`
   file — to your GitHub repo. That workflow file is what makes GitHub
   build the exe for you.
2. Tag a release and push the tag:
   ```
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. GitHub Actions spins up a Windows runner, builds `FileOrganizer.exe`, and
   automatically attaches it to a new Release on your repo — visible under
   the "Releases" section on the right side of your repo page.
4. Anyone can then go to your repo's Releases page and download
   `FileOrganizer.exe` directly no Python install needed on their end.

You can also trigger a build manually anytime from the repo's **Actions**
tab ("Run workflow") without needing to push a new tag.

### Notes on the exe
- First launch may take a couple seconds longer than the Python version
  (PyInstaller unpacks itself into a temp folder each run).
- Windows SmartScreen may warn that it's from an "unknown publisher" the
  first time someone runs it, since it isn't code-signed that's normal
  for unsigned indie tools; they click "More info" → "Run anyway".
  Code-signing costs money (a certificate) and isn't required for this to work.
- `rules.json`, `config.json`, and `fileorganizer.db` are created next to
  the exe on first run, same as with the Python version.

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
