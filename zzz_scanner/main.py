"""
Genshin Artifact Scanner — main app.

Flow:
  1. Start screen: click "Start Scan", switch to Genshin during countdown.
  2. App minimizes, clicks through every 5-star thumbnail, OCRs each popup.
  3. Rating screen: for each artifact, shows the popup crop + parsed fields,
     you pick a score. Scores are the only manual input.
  4. Export: writes artifacts_export.json (matches the web app's create schema).

Run from an ADMINISTRATOR terminal.
"""
import json
import threading

import customtkinter as ctk
from PIL import Image

import config
from automation import scan_all

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FIELD_FONT = ("Segoe UI", 15)


class ScannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Genshin Artifact Scanner")
        self.geometry("960x720")

        self.results: list[dict] = []
        self.scores: dict[int, str] = {}
        self.idx = 0
        self._img_cache = None  # keep a ref so CTkImage isn't garbage-collected

        # Shared state — persisted across runs and shared by both screens
        self.path_var = ctk.StringVar(value=config.get_export_path())
        self.source = config.get_source()

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=16, pady=16)
        self._build_start_screen()

    # ---------- start screen ----------
    def _build_start_screen(self):
        self._clear()
        ctk.CTkLabel(
            self.container, text="Genshin Artifact Scanner",
            font=("Segoe UI", 26, "bold"),
        ).pack(pady=(40, 8))
        ctk.CTkLabel(
            self.container,
            text="Open Genshin to the \"Obtained\" screen.\n"
                 "Click Start, then switch to the game before the countdown ends.",
            font=FIELD_FONT, justify="center",
        ).pack(pady=8)

        # Source selector
        src_row = ctk.CTkFrame(self.container, fg_color="transparent")
        src_row.pack(pady=(16, 4))
        ctk.CTkLabel(src_row, text="Source:", font=("Segoe UI", 15, "bold")).pack(
            side="left", padx=(0, 10)
        )
        self.source_selector = ctk.CTkSegmentedButton(
            src_row, values=config.SOURCE_OPTIONS, command=self._set_source,
        )
        self.source_selector.set(self.source)
        self.source_selector.pack(side="left")

        # Save path
        path_row = ctk.CTkFrame(self.container, fg_color="transparent")
        path_row.pack(pady=(8, 4), fill="x", padx=60)
        ctk.CTkLabel(path_row, text="Save to:", font=("Segoe UI", 13)).pack(
            side="left", padx=(0, 8)
        )
        path_entry = ctk.CTkEntry(path_row, font=("Segoe UI", 13), textvariable=self.path_var)
        path_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(path_row, text="Browse", width=80, command=self._browse_path).pack(
            side="left", padx=(8, 0)
        )

        self.status_label = ctk.CTkLabel(self.container, text="", font=("Segoe UI", 18))
        self.status_label.pack(pady=16)

        self.scan_btn = ctk.CTkButton(
            self.container, text="Start Scan", width=200, height=44,
            font=("Segoe UI", 16, "bold"), command=self._start_scan,
        )
        self.scan_btn.pack(pady=10)

    def _set_source(self, value):
        self.source = value
        config.set_source(value)

    def _start_scan(self):
        self.scan_btn.configure(state="disabled")
        self._countdown(int(config.START_DELAY))

    def _countdown(self, remaining):
        if remaining > 0:
            self.status_label.configure(
                text=f"Switch to Genshin! Scanning in {remaining}..."
            )
            self.after(1000, lambda: self._countdown(remaining - 1))
        else:
            self.status_label.configure(text="Scanning... (mouse to a corner aborts)")
            self.iconify()  # minimize so the game keeps focus during automation
            threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        try:
            results = scan_all()
        except Exception as e:  # noqa: BLE001 — surface any failure to the UI
            self.after(0, lambda: self._scan_failed(str(e)))
            return
        self.after(0, lambda: self._scan_done(results))

    def _scan_failed(self, msg):
        self.deiconify()
        self.scan_btn.configure(state="normal")
        self.status_label.configure(text=f"Scan failed: {msg}")

    def _scan_done(self, results):
        self.deiconify()
        self.lift()
        self.results = results
        self.scores = {}
        self.idx = 0
        if not results:
            self.scan_btn.configure(state="normal")
            self.status_label.configure(text="No artifacts detected. Try again.")
            return
        self._build_rating_screen()
        self._show_current()

    # ---------- rating screen ----------
    def _build_rating_screen(self):
        self._clear()

        self.header = ctk.CTkLabel(self.container, text="", font=("Segoe UI", 20, "bold"))
        self.header.pack(pady=(4, 10))

        body = ctk.CTkFrame(self.container, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Left: popup crop image
        self.image_label = ctk.CTkLabel(body, text="")
        self.image_label.pack(side="left", padx=(0, 16))

        # Right: parsed fields
        self.fields_frame = ctk.CTkFrame(body)
        self.fields_frame.pack(side="left", fill="both", expand=True)
        self.fields_label = ctk.CTkLabel(
            self.fields_frame, text="", font=FIELD_FONT, justify="left", anchor="nw",
        )
        self.fields_label.pack(fill="both", expand=True, padx=14, pady=14)

        # Score buttons
        score_row = ctk.CTkFrame(self.container, fg_color="transparent")
        score_row.pack(pady=12)
        ctk.CTkLabel(score_row, text="Score:", font=("Segoe UI", 15, "bold")).pack(
            side="left", padx=(0, 10)
        )
        self.score_buttons: dict[str, ctk.CTkButton] = {}
        for s in config.SCORES:
            b = ctk.CTkButton(
                score_row, text=s, width=110,
                command=lambda val=s: self._set_score(val),
            )
            b.pack(side="left", padx=4)
            self.score_buttons[s] = b
        # Remember the theme default so we can restore unselected buttons
        self._default_btn_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]

        # Save path row
        path_row = ctk.CTkFrame(self.container, fg_color="transparent")
        path_row.pack(pady=(8, 0), fill="x", padx=20)
        ctk.CTkLabel(path_row, text="Save to:", font=("Segoe UI", 13)).pack(side="left", padx=(0, 8))
        self.path_entry = ctk.CTkEntry(path_row, font=("Segoe UI", 13), textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(path_row, text="Browse", width=80, command=self._browse_path).pack(
            side="left", padx=(8, 0)
        )

        # Navigation
        nav = ctk.CTkFrame(self.container, fg_color="transparent")
        nav.pack(pady=8)
        ctk.CTkButton(nav, text="< Prev", width=90, command=self._prev).pack(side="left", padx=6)
        self.progress_label = ctk.CTkLabel(nav, text="", font=FIELD_FONT)
        self.progress_label.pack(side="left", padx=12)
        ctk.CTkButton(nav, text="Next >", width=90, command=self._next).pack(side="left", padx=6)
        ctk.CTkButton(
            nav, text="Export JSON", width=130, fg_color="#2a8c4a",
            hover_color="#22713c", command=self._export,
        ).pack(side="left", padx=(24, 6))
        ctk.CTkButton(
            nav, text="New Scan", width=110, fg_color="#7a4ea0",
            hover_color="#633f85", command=self._restart,
        ).pack(side="left", padx=6)

        self.export_status = ctk.CTkLabel(self.container, text="", font=FIELD_FONT)
        self.export_status.pack(pady=(4, 0))

    def _show_current(self):
        data = self.results[self.idx]
        n = len(self.results)
        self.header.configure(text=f"Artifact {self.idx + 1} of {n}")

        # Image (scale popup crop to fit height ~440)
        img = data.get("_image")
        if isinstance(img, Image.Image):
            target_h = 440
            scale = target_h / img.height
            size = (int(img.width * scale), target_h)
            self._img_cache = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            self.image_label.configure(image=self._img_cache)
        else:
            self.image_label.configure(image=None, text="(no image)")

        # Fields, flagging low-confidence reads with a marker
        ok = data.get("_ok", {})
        def mark(field, value):
            flag = "" if ok.get(field, True) else "  ⚠"
            return f"{value if value not in (None, '') else '—'}{flag}"

        subs = ", ".join(data.get("substats") or []) or "—"
        un = data.get("unactivatedSubstat") or "—"
        text = (
            f"Set:            {mark('set', data.get('set'))}\n\n"
            f"Type:           {mark('type', data.get('type'))}\n\n"
            f"Main stat:      {mark('mainStat', data.get('mainStat'))}\n\n"
            f"# Substats:     {data.get('numberOfSubstats')}\n\n"
            f"Substats:       {mark('substats', subs)}\n\n"
            f"Unactivated:    {un}\n\n"
            f"Source:         {self.source}"
        )
        self.fields_label.configure(text=text)

        # Highlight selected score
        chosen = self.scores.get(self.idx)
        for s, btn in self.score_buttons.items():
            btn.configure(
                fg_color="#c8732b" if s == chosen else self._default_btn_color
            )

        scored = len(self.scores)
        self.progress_label.configure(text=f"{scored}/{n} scored")

    def _set_score(self, value):
        self.scores[self.idx] = value
        # advance to next unscored, else just next
        if self.idx < len(self.results) - 1:
            self.idx += 1
        self._show_current()

    def _prev(self):
        if self.idx > 0:
            self.idx -= 1
            self._show_current()

    def _next(self):
        if self.idx < len(self.results) - 1:
            self.idx += 1
            self._show_current()

    def _export(self):
        path = self.path_var.get().strip() or config.EXPORT_FILE

        out = []
        for i, r in enumerate(self.results):
            out.append({
                "set": r.get("set"),
                "type": r.get("type"),
                "mainStat": r.get("mainStat"),
                "numberOfSubstats": r.get("numberOfSubstats"),
                "substats": r.get("substats") or [],
                "unactivatedSubstat": r.get("unactivatedSubstat"),
                "score": self.scores.get(i, "Unknown"),
                "source": self.source,  # chosen on the start page
            })
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
        except OSError as e:
            self.export_status.configure(text=f"Could not save: {e}")
            return

        config.set_export_path(path)  # remember for next time
        unscored = len(self.results) - len(self.scores)
        note = f" ({unscored} left as 'Unknown')" if unscored else ""
        self.export_status.configure(
            text=f"Saved {len(out)} artifact(s) → {path}{note}"
        )

    def _browse_path(self):
        from tkinter import filedialog
        chosen = filedialog.asksaveasfilename(
            title="Save artifacts JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="artifacts_export.json",
        )
        if chosen:
            self.path_var.set(chosen)
            config.set_export_path(chosen)  # remember immediately

    def _restart(self):
        """Discard the current scan and return to the start screen for a new run."""
        self.results = []
        self.scores = {}
        self.idx = 0
        self._img_cache = None
        self._build_start_screen()

    # ---------- helpers ----------
    def _clear(self):
        for w in self.container.winfo_children():
            w.destroy()


if __name__ == "__main__":
    app = ScannerApp()
    app.mainloop()
