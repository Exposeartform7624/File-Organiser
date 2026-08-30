
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
import threading

import config
import rules as rules_mod
import db
import watcher

APP_TITLE = "File Organizer"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("880x560")

        db.init_db()
        self.cfg = config.load_config()
        self.observer = None

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.settings_tab = SettingsTab(nb, self)
        self.rules_tab = RulesTab(nb, self)
        self.files_tab = FilesTab(nb, self)

        nb.add(self.settings_tab, text="Settings")
        nb.add(self.rules_tab, text="Rules")
        nb.add(self.files_tab, text="Files & Tags")

        self.log_box = tk.Text(self, height=8, state="disabled", bg="#111", fg="#0f0")
        self.log_box.pack(fill="x", side="bottom")

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.start_watching()

    def log(self, msg):
        def _write():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
            self.files_tab.refresh()
        self.after(0, _write)

    def start_watching(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        watch_folder = self.cfg["watch_folder"]
        output_base = self.cfg["output_base"]
        Path(watch_folder).mkdir(parents=True, exist_ok=True)
        Path(output_base).mkdir(parents=True, exist_ok=True)
        threading.Thread(
            target=self._start_watcher_thread,
            args=(watch_folder, output_base),
            daemon=True
        ).start()

    def _start_watcher_thread(self, watch_folder, output_base):
        self.observer = watcher.start_watcher(watch_folder, output_base, log=self.log)

    def on_close(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.destroy()


class SettingsTab(ttk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app
        pad = {"padx": 10, "pady": 8}

        ttk.Label(self, text="Watched folder (new files here get organized):").grid(
            row=0, column=0, sticky="w", **pad)
        self.watch_var = tk.StringVar(value=app.cfg["watch_folder"])
        ttk.Entry(self, textvariable=self.watch_var, width=60).grid(row=1, column=0, **pad)
        ttk.Button(self, text="Browse...", command=self.browse_watch).grid(row=1, column=1, **pad)

        ttk.Label(self, text="Output folder (organized files land here):").grid(
            row=2, column=0, sticky="w", **pad)
        self.output_var = tk.StringVar(value=app.cfg["output_base"])
        ttk.Entry(self, textvariable=self.output_var, width=60).grid(row=3, column=0, **pad)
        ttk.Button(self, text="Browse...", command=self.browse_output).grid(row=3, column=1, **pad)

        ttk.Button(self, text="Save & Restart Watching", command=self.save).grid(
            row=4, column=0, sticky="w", **pad)

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
        self.app.start_watching()
        messagebox.showinfo(APP_TITLE, "Saved. Watcher restarted.")


class RulesTab(ttk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app
        self.rules = rules_mod.load_rules()

        self.listbox = tk.Listbox(self, width=40)
        self.listbox.pack(side="left", fill="y", padx=10, pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.refresh_list()

        btns = ttk.Frame(self)
        btns.pack(side="left", fill="y", pady=10)
        ttk.Button(btns, text="New Rule", command=self.new_rule).pack(fill="x", pady=2)
        ttk.Button(btns, text="Delete Rule", command=self.delete_rule).pack(fill="x", pady=2)
        ttk.Button(btns, text="Move Up", command=lambda: self.move(-1)).pack(fill="x", pady=2)
        ttk.Button(btns, text="Move Down", command=lambda: self.move(1)).pack(fill="x", pady=2)

        form = ttk.Frame(self)
        form.pack(side="left", fill="both", expand=True, padx=10, pady=10)

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
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", pady=4)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=45).grid(row=i, column=1, pady=4)
            self.fields[key] = var

        ttk.Button(form, text="Save Rule", command=self.save_rule).grid(
            row=len(labels), column=0, columnspan=2, pady=10)

        self.selected_index = None

    def refresh_list(self):
        self.listbox.delete(0, "end")
        for r in self.rules:
            self.listbox.insert("end", r["name"])

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
        super().__init__(parent)
        self.app = app

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="Filter by tag:").pack(side="left")
        self.tag_filter = tk.StringVar()
        ttk.Entry(top, textvariable=self.tag_filter, width=25).pack(side="left", padx=6)
        ttk.Button(top, text="Filter", command=self.refresh).pack(side="left")
        ttk.Button(top, text="Clear", command=self.clear_filter).pack(side="left", padx=6)

        cols = ("filename", "rule", "tags", "organized_at")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c, w in zip(cols, (280, 120, 250, 160)):
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, padx=10, pady=6)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=8)
        ttk.Button(bottom, text="Add Tag", command=self.add_tag).pack(side="left")
        ttk.Button(bottom, text="Remove Tag", command=self.remove_tag).pack(side="left", padx=6)

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
