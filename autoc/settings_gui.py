"""Settings window (tkinter, ships with Python on Windows)."""
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from . import languages, paths
from .config import Config
from .dictionary import available_languages

FIXES = [
    ("fix_spelling", "Fix spelling mistakes"),
    ("fix_sentence_start", "Capitalise the first word of a sentence"),
    ("fix_two_initial_caps", "Fix TWo INitial CApitals (THe -> The)"),
    ("fix_caps_lock", "Fix accidental caps lock (hELLO -> Hello)"),
    ("fix_standalone_i", "English: i -> I, im -> I'm, dont -> don't"),
    ("use_replacements", "Use replacement tables (built-in + your own)"),
    ("undo_with_backspace", "Backspace right after a fix restores what I typed (and teaches AutoC)"),
]


def main():
    cfg = Config.load()
    root = tk.Tk()
    root.title("AutoC settings")
    root.geometry("560x560")
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=8, pady=8)

    # ---- General
    g = ttk.Frame(nb, padding=10)
    nb.add(g, text="General")
    vars_ = {}
    for key, label in FIXES:
        vars_[key] = tk.BooleanVar(value=getattr(cfg, key))
        ttk.Checkbutton(g, text=label, variable=vars_[key]).pack(anchor="w", pady=2)
    ttk.Label(g, text="On/off hotkey (e.g. f12, ctrl+alt+a):").pack(anchor="w", pady=(14, 0))
    hotkey = tk.StringVar(value=cfg.toggle_hotkey)
    ttk.Entry(g, textvariable=hotkey, width=20).pack(anchor="w")
    ttk.Label(g, text="Text typed while AutoC is off is never corrected afterwards.",
              foreground="gray").pack(anchor="w", pady=(2, 0))
    autostart = tk.BooleanVar(value=cfg.start_with_windows)
    ttk.Checkbutton(g, text="Start AutoC with Windows", variable=autostart).pack(anchor="w", pady=(14, 0))

    # ---- Languages
    lf = ttk.Frame(nb, padding=10)
    nb.add(lf, text="Languages")
    auto_kb = tk.BooleanVar(value=cfg.auto_add_keyboard_languages)
    ttk.Checkbutton(lf, text="Automatically use the languages of my installed keyboards",
                    variable=auto_kb).pack(anchor="w")
    ttk.Label(lf, text="Enabled languages (AutoC detects which one you are typing):").pack(anchor="w", pady=(8, 2))
    box = ttk.Frame(lf)
    box.pack(fill="both", expand=True)
    canvas = tk.Canvas(box, highlightthickness=0)
    sb = ttk.Scrollbar(box, command=canvas.yview)
    inner = ttk.Frame(canvas)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    lang_vars = {}
    for code in sorted(available_languages(), key=lambda c: languages.name(c)):
        lang_vars[code] = tk.BooleanVar(value=code in cfg.languages)
        ttk.Checkbutton(inner, text=f"{languages.name(code)} ({code})", variable=lang_vars[code]).pack(anchor="w")
    prim = ttk.Frame(lf)
    prim.pack(fill="x", pady=6)
    ttk.Label(prim, text="Main language:").pack(side="left")
    primary = tk.StringVar(value=cfg.primary_language)
    ttk.Combobox(prim, textvariable=primary, values=sorted(lang_vars), width=6).pack(side="left", padx=6)

    def add_dict():
        f = filedialog.askopenfilename(title="Word list or Hunspell .dic",
                                       filetypes=[("Dictionaries", "*.txt *.dic *.gz"), ("All", "*.*")])
        if not f:
            return
        code = simpledialog.askstring("Language code", "Language code for this dictionary (e.g. de, sw, xx):")
        if code:
            import shutil
            ext = ".dic" if f.endswith(".dic") else ".txt"
            shutil.copyfile(f, paths.user_dict_dir() / (code.strip().lower() + ext))
            messagebox.showinfo("AutoC", "Dictionary added. Reopen settings to enable it.")
    ttk.Button(lf, text="Add my own dictionary...", command=add_dict).pack(anchor="w")

    # ---- Words
    wf = ttk.Frame(nb, padding=10)
    nb.add(wf, text="My words")
    ttk.Label(wf, text="Words AutoC must never change (names, brands like Koleku):").pack(anchor="w")
    words = tk.Listbox(wf, height=7)
    words.pack(fill="x")
    for w in cfg.user_words:
        words.insert("end", w)
    row = ttk.Frame(wf)
    row.pack(anchor="w", pady=3)

    def add_word():
        w = simpledialog.askstring("Add word", "Word:")
        if w and w.strip():
            words.insert("end", w.strip())
    ttk.Button(row, text="Add", command=add_word).pack(side="left")
    ttk.Button(row, text="Remove", command=lambda: [words.delete(i) for i in reversed(words.curselection())]).pack(side="left", padx=4)
    ttk.Label(wf, text="Your own replacements (typed  ->  becomes):").pack(anchor="w", pady=(12, 0))
    reps = ttk.Treeview(wf, columns=("a", "b"), show="headings", height=6)
    reps.heading("a", text="Typed")
    reps.heading("b", text="Replace with")
    reps.pack(fill="x")
    for k, v in cfg.custom_replacements.items():
        reps.insert("", "end", values=(k, v))
    row2 = ttk.Frame(wf)
    row2.pack(anchor="w", pady=3)

    def add_rep():
        a = simpledialog.askstring("Replacement", "When I type:")
        b = a and simpledialog.askstring("Replacement", f"Replace '{a}' with:")
        if a and b:
            reps.insert("", "end", values=(a.strip(), b))
    ttk.Button(row2, text="Add", command=add_rep).pack(side="left")
    ttk.Button(row2, text="Remove", command=lambda: [reps.delete(i) for i in reps.selection()]).pack(side="left", padx=4)

    # ---- Apps
    af = ttk.Frame(nb, padding=10)
    nb.add(af, text="Excluded apps")
    ttk.Label(af, text="AutoC does nothing in these programs (one .exe per line):").pack(anchor="w")
    apps = tk.Text(af, height=16)
    apps.pack(fill="both", expand=True)
    apps.insert("1.0", "\n".join(cfg.excluded_apps))

    def save():
        for key, v in vars_.items():
            setattr(cfg, key, v.get())
        cfg.toggle_hotkey = hotkey.get().strip() or "f12"
        cfg.auto_add_keyboard_languages = auto_kb.get()
        cfg.languages = [c for c, v in lang_vars.items() if v.get()] or ["en"]
        cfg.primary_language = primary.get() if primary.get() in cfg.languages else cfg.languages[0]
        cfg.user_words = list(words.get(0, "end"))
        cfg.custom_replacements = {reps.set(i, "a").lower(): reps.set(i, "b") for i in reps.get_children()}
        cfg.excluded_apps = [l.strip().lower() for l in apps.get("1.0", "end").splitlines() if l.strip()]
        cfg.start_with_windows = autostart.get()
        cfg.save()
        try:
            from .app import set_autostart
            set_autostart(cfg.start_with_windows)
        except Exception:
            pass
        messagebox.showinfo("AutoC", "Saved. Changes apply within a couple of seconds.")
        root.destroy()

    bar = ttk.Frame(root)
    bar.pack(fill="x", padx=8, pady=(0, 8))
    ttk.Button(bar, text="Save", command=save).pack(side="right")
    ttk.Button(bar, text="Cancel", command=root.destroy).pack(side="right", padx=6)
    root.mainloop()
    return 0
