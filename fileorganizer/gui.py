import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
import threading
 
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
 
import config
import rules as rules_mod
import db
import watcher
APP_TITLE = "File Organizer"
THEME = "darkly"  # dark, flat, modern ttkbootstrap theme
 
HELP_TEXT = """Welcome to File Organizer!
 
QUICK START
1. Go to the Settings tab and pick a Watched folder (files dropped here
   get organized automatically) and an Output folder (where the sorted
   subfolders will be created).
2. Go to the Rules tab to define how files get sorted - by extension,
   filename text, size, or age. The first matching rule wins; anything
   that matches nothing goes into "Unsorted".
3. Once a file's been organized, find it in the Files & Tags tab and add
   your own tags so you can search for it later.
 
The app runs quietly in the background watching your folder the whole
time it's open - you don't need to do anything else.
 
A NOTE ON SECURITY WARNINGS
Since this app isn't code-signed (that costs money and isn't required
for it to work safely), you may see warnings when downloading or
running it:
 
- Chrome may say the download is "suspicious" - click the small arrow
  next to the blocked download and choose "Keep" or "Keep anyway."
- Windows SmartScreen may say it's from an "unknown publisher" - click
  "More info" then "Run anyway."
 
These are common false positives for small, independently-built apps
like this one - not a sign anything is actually wrong.
 
You can reopen this help anytime from the "Help" button up top.
"""
 
 
class HelpWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Welcome / Help")
        self.geometry("520x520")
        self.configure(bg="#1a1d21")
        self.transient(parent)
 
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
 
        text = tk.Text(
            frame, wrap="word", bg="#1a1d21", fg="#e6e6e6",
            relief="flat", borderwidth=0, font=("Segoe UI", 10),
            padx=4, pady=4
        )
        text.insert("1.0", HELP_TEXT)
        text.configure(state="disabled")
        text.pack(fill="both", expand=True, pady=(0, 12))
 
        ttk.Button(frame, text="Got it", command=self.destroy,
                   bootstyle="success", width=16).pack()
 
        self.grab_set()
        self.focus_set()
 
 
class App(ttk.Window):
    def __init__(self):
        super().__init__(themename=THEME)
        self.title(APP_TITLE)
        self.geometry("920x600")
        self.minsize(760, 480)
 
        is_first_run = not config.CONFIG_PATH.exists()
 
        db.init_db()
        self.cfg = config.load_config()
        self.observer = None
        self.watching = False

        header = ttk.Frame(self, padding=(16, 14, 16, 6))
        header.pack(fill="x")
        ttk.Label(header, text="File Organizer", font=("Segoe UI", 16, "bold")).pack(side="left")
        self.status_dot = ttk.Label(header, text="●", bootstyle="secondary", font=("Segoe UI", 12))
        self.status_dot.pack(side="right")
        self.status_label = ttk.Label(header, text="stopped", bootstyle="secondary")
        self.status_label.pack(side="right", padx=(0, 4))
        self.watch_toggle_btn = ttk.Button(header, text="Start Watching", command=self.toggle_watching,
                                            bootstyle="success", width=14)
        self.watch_toggle_btn.pack(side="right", padx=(0, 12))
        ttk.Button(header, text="Help", command=self.show_help,
                   bootstyle="secondary-outline", width=8).pack(side="right", padx=(0, 12))
 
        nb = ttk.Notebook(self, bootstyle="dark")
        nb.pack(fill="both", expand=True, padx=16, pady=(0, 8))
 
        self.settings_tab = SettingsTab(nb, self)
        self.rules_tab = RulesTab(nb, self)
        self.files_tab = FilesTab(nb, self)
 
        nb.add(self.settings_tab, text="  Settings  ")
        nb.add(self.rules_tab, text="  Rules  ")
        nb.add(self.files_tab, text="  Files & Tags  ")
 
        log_frame = ttk.Labelframe(self, text="Activity", padding=8, bootstyle="secondary")
        log_frame.pack(fill="x", side="bottom", padx=16, pady=(0, 16))
        self.log_box = tk.Text(
            log_frame, height=7, state="disabled",
            bg="#1a1d21", fg="#8fd19e", insertbackground="#8fd19e",
            relief="flat", borderwidth=0, font=("Consolas", 9)
        )
        self.log_box.pack(fill="x")
 
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if is_first_run:
            self.after(300, self.show_help)

    def show_help(self):
        HelpWindow(self)

    def log(self, msg):
        def _write():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
            self.files_tab.refresh()
        self.after(0, _write)

    def toggle_watching(self):
        if self.watching:
            self.stop_watching()
        else:
            self.start_watching()

    def start_watching(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        watch_folder = self.cfg["watch_folder"]
        output_base = self.cfg["output_base"]
        Path(watch_folder).mkdir(parents=True, exist_ok=True)
        Path(output_base).mkdir(parents=True, exist_ok=True)
        self.watching = True
        self.status_dot.configure(bootstyle="success")
        self.status_label.configure(text="watching")
        self.watch_toggle_btn.configure(text="Stop Watching", bootstyle="danger-outline")
        threading.Thread(
            target=self._start_watcher_thread,
            args=(watch_folder, output_base),
            daemon=True
        ).start()

    def stop_watching(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.watching = False
        self.status_dot.configure(bootstyle="secondary")
        self.status_label.configure(text="stopped")
        self.watch_toggle_btn.configure(text="Start Watching", bootstyle="success")

    def _start_watcher_thread(self, watch_folder, output_base):
        self.observer = watcher.start_watcher(watch_folder, output_base, log=self.log)

    def on_close(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.destroy()
 
 
class SettingsTab(ttk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, padding=20)
        self.app = app
 
        ttk.Label(self, text="Watched folder", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Label(self, text="New files dropped here get organized automatically",
                   bootstyle="secondary").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 6))
        self.watch_var = tk.StringVar(value=app.cfg["watch_folder"])
        ttk.Entry(self, textvariable=self.watch_var, width=60).grid(
            row=2, column=0, sticky="ew", pady=(0, 4), padx=(0, 8))
        ttk.Button(self, text="Browse...", command=self.browse_watch,
                   bootstyle="secondary-outline").grid(row=2, column=1, pady=(0, 4))
 
        ttk.Label(self, text="Output folder", font=("Segoe UI", 10, "bold")).grid(
            row=3, column=0, sticky="w", pady=(20, 4))
        ttk.Label(self, text="Organized subfolders (Documents, Images, etc.) are created here",
                   bootstyle="secondary").grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 6))
        self.output_var = tk.StringVar(value=app.cfg["output_base"])
        ttk.Entry(self, textvariable=self.output_var, width=60).grid(
            row=5, column=0, sticky="ew", pady=(0, 4), padx=(0, 8))
        ttk.Button(self, text="Browse...", command=self.browse_output,
                   bootstyle="secondary-outline").grid(row=5, column=1, pady=(0, 4))
 
        ttk.Button(self, text="Save & Restart Watching", command=self.save,
                   bootstyle="success", width=26).grid(row=6, column=0, sticky="w", pady=(24, 0))
 
        self.columnconfigure(0, weight=1)
 
    def browse_watch(self):
        d = filedialog.askdirectory()
        if d:
            self.watch_var.set(d)
 
    def browse_output(self):
        d = filedialog.askdirectory()
        if d:
            self.output_var.set(d)
 
    def save(self):
        self.app.cfg["watch_folder"] = self.watch_var.get()
        self.app.cfg["output_base"] = self.output_var.get()
        config.save_config(self.app.cfg)
        if self.app.watching:
            self.app.start_watching()
            messagebox.showinfo(APP_TITLE, "Saved. Watcher restarted.")
        else:
            messagebox.showinfo(APP_TITLE, "Saved. Click \"Start Watching\" to begin.")
 
 
class RulesTab(ttk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, padding=16)
        self.app = app
        self.rules = rules_mod.load_rules()
 
        left = ttk.Frame(self)
        left.pack(side="left", fill="y", padx=(0, 16))
 
        ttk.Label(left, text="Rules (top wins)", font=("Segoe UI", 10, "bold")).pack(
            anchor="w", pady=(0, 6))
        self.listbox = tk.Listbox(
            left, width=32, height=14,
            bg="#22262b", fg="#e6e6e6", selectbackground="#2f8f4e",
            relief="flat", borderwidth=0, highlightthickness=1,
            highlightbackground="#3a3f45"
        )
        self.listbox.pack(fill="y", pady=(0, 8))
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.refresh_list()
 
        btns = ttk.Frame(left)
        btns.pack(fill="x")
        ttk.Button(btns, text="New", command=self.new_rule,
                   bootstyle="secondary-outline", width=8).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(btns, text="Delete", command=self.delete_rule,
                   bootstyle="danger-outline", width=8).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(btns, text="▲ Up", command=lambda: self.move(-1),
                   bootstyle="secondary-outline", width=8).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(btns, text="▼ Down", command=lambda: self.move(1),
                   bootstyle="secondary-outline", width=8).grid(row=1, column=1, padx=2, pady=2)
 
        form = ttk.Labelframe(self, text="Rule details", padding=16, bootstyle="secondary")
        form.pack(side="left", fill="both", expand=True)
 
        self.fields = {}
        labels = [
            ("name", "Rule name"),
            ("extensions", "Extensions (comma-separated, e.g. pdf,docx)"),
            ("name_contains", "Filename contains (optional)"),
            ("min_size_kb", "Min size KB (optional)"),
            ("max_size_kb", "Max size KB (optional)"),
            ("older_than_days", "Older than N days (optional)"),
            ("destination", "Destination subfolder (e.g. Documents/Invoices)"),
        ]
        for i, (key, label) in enumerate(labels):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", pady=6)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=42).grid(row=i, column=1, pady=6, padx=(10, 0))
            self.fields[key] = var
 
        ttk.Button(form, text="Save Rule", command=self.save_rule,
                   bootstyle="success", width=20).grid(
            row=len(labels), column=0, columnspan=2, pady=(16, 0))
 
        self.selected_index = None
 
    def refresh_list(self):
        self.listbox.delete(0, "end")
        for r in self.rules:
            self.listbox.insert("end", f"  {r['name']}")
 
    def on_select(self, evt):
        sel = self.listbox.curselection()
        if not sel:
            return
        self.selected_index = sel[0]
        r = self.rules[self.selected_index]
        self.fields["name"].set(r.get("name", ""))
        self.fields["extensions"].set(",".join(r.get("extensions") or []))
        self.fields["name_contains"].set(r.get("name_contains") or "")
        self.fields["min_size_kb"].set(r.get("min_size_kb") or "")
        self.fields["max_size_kb"].set(r.get("max_size_kb") or "")
        self.fields["older_than_days"].set(r.get("older_than_days") or "")
        self.fields["destination"].set(r.get("destination", ""))
 
    def new_rule(self):
        self.selected_index = None
        for var in self.fields.values():
            var.set("")
 
    def save_rule(self):
        name = self.fields["name"].get().strip()
        destination = self.fields["destination"].get().strip()
        if not name or not destination:
            messagebox.showerror(APP_TITLE, "Rule name and destination are required.")
            return
 
        def _int_or_none(s):
            s = s.strip()
            return int(s) if s else None
 
        ext_raw = self.fields["extensions"].get().strip()
        rule = {
            "name": name,
            "extensions": [e.strip() for e in ext_raw.split(",") if e.strip()] or None,
            "name_contains": self.fields["name_contains"].get().strip() or None,
            "min_size_kb": _int_or_none(self.fields["min_size_kb"].get()),
            "max_size_kb": _int_or_none(self.fields["max_size_kb"].get()),
            "older_than_days": _int_or_none(self.fields["older_than_days"].get()),
            "destination": destination,
        }
 
        if self.selected_index is not None:
            self.rules[self.selected_index] = rule
        else:
            self.rules.append(rule)
        rules_mod.save_rules(self.rules)
        self.refresh_list()
        messagebox.showinfo(APP_TITLE, "Rule saved.")
 
    def delete_rule(self):
        if self.selected_index is None:
            return
        del self.rules[self.selected_index]
        rules_mod.save_rules(self.rules)
        self.refresh_list()
        self.new_rule()
 
    def move(self, direction):
        if self.selected_index is None:
            return
        i = self.selected_index
        j = i + direction
        if 0 <= j < len(self.rules):
            self.rules[i], self.rules[j] = self.rules[j], self.rules[i]
            rules_mod.save_rules(self.rules)
            self.refresh_list()
            self.listbox.selection_set(j)
            self.selected_index = j
 
 
class FilesTab(ttk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, padding=16)
        self.app = app
 
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="Filter by tag:").pack(side="left", padx=(0, 8))
        self.tag_filter = tk.StringVar()
        ttk.Entry(top, textvariable=self.tag_filter, width=25).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="Filter", command=self.refresh,
                   bootstyle="success-outline").pack(side="left", padx=2)
        ttk.Button(top, text="Clear", command=self.clear_filter,
                   bootstyle="secondary-outline").pack(side="left", padx=2)
 
        cols = ("filename", "rule", "tags", "organized_at")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", bootstyle="dark", height=16)
        headers = {"filename": "Filename", "rule": "Rule", "tags": "Tags", "organized_at": "Organized At"}
        for c, w in zip(cols, (300, 130, 260, 170)):
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, pady=(0, 10))
 
        bottom = ttk.Frame(self)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="+ Add Tag", command=self.add_tag,
                   bootstyle="success").pack(side="left", padx=(0, 6))
        ttk.Button(bottom, text="− Remove Tag", command=self.remove_tag,
                   bootstyle="danger-outline").pack(side="left")
 
        self.refresh()
 
    def clear_filter(self):
        self.tag_filter.set("")
        self.refresh()
 
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        rows = db.get_all_files(self.tag_filter.get().strip() or None)
        for _id, path, filename, rule_matched, organized_at in rows:
            tags = ", ".join(db.get_tags_for_file(path))
            self.tree.insert("", "end", iid=path,
                              values=(filename, rule_matched or "Unsorted", tags, organized_at))
 
    def _selected_path(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_TITLE, "Select a file first.")
            return None
        return sel[0]
 
    def add_tag(self):
        path = self._selected_path()
        if not path:
            return
        tag = simpledialog.askstring(APP_TITLE, "Tag name:")
        if tag:
            db.add_tag(path, tag)
            self.refresh()
 
    def remove_tag(self):
        path = self._selected_path()
        if not path:
            return
        tag = simpledialog.askstring(APP_TITLE, "Tag to remove:")
        if tag:
            db.remove_tag(path, tag)
            self.refresh()
 
 
if __name__ == "__main__":
    App().mainloop()