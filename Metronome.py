

import json
import os
import queue
import sys
import threading
import time
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
import keyboard
import pygame


APP_NAME = "Metronome"
APP_AUTHOR = "LostXRP"
HOTKEY = "ctrl+shift+c"

BG = "#09090D"
CARD = "#121219"
CARD_ALT = "#171720"
BORDER = "#252532"
TEXT = "#F7F7FA"
MUTED = "#9292A6"
ACCENT = "#8B5CF6"
ACCENT_HOVER = "#7C3AED"
SUCCESS = "#34D399"
DANGER = "#FB7185"

DEFAULT_SETTINGS = {
    "bpm": 100.0,
    "volume": 0.70,
    "audio_enabled": True,
    "visual_enabled": True,
    "always_on_top": False,
    "compact_mode": False,
    "sound_path": "",
}


def bundled_path(relative_path: str) -> Path:
    """Return a path that works from source and from a PyInstaller bundle."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative_path


def settings_path() -> Path:
    base = Path(os.getenv("APPDATA", Path.home() / ".config"))
    folder = base / "LostXRP" / "Metronome"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "settings.json"


class MetronomeEngine:
    """High-resolution beat scheduler that never touches Tkinter directly."""

    def __init__(self, beat_queue: queue.SimpleQueue):
        self.beat_queue = beat_queue
        self.running = threading.Event()
        self.shutdown = threading.Event()
        self.lock = threading.Lock()

        self.bpm = 100.0
        self.audio_enabled = True
        self.sound: pygame.mixer.Sound | None = None

        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def set_bpm(self, bpm: float) -> None:
        with self.lock:
            self.bpm = max(20.0, min(240.0, float(bpm)))

    def set_audio_enabled(self, enabled: bool) -> None:
        with self.lock:
            self.audio_enabled = bool(enabled)

    def set_sound(self, sound: pygame.mixer.Sound | None) -> None:
        with self.lock:
            self.sound = sound

    def start(self) -> None:
        self.running.set()

    def stop(self) -> None:
        self.running.clear()

    def close(self) -> None:
        self.running.clear()
        self.shutdown.set()

    def _snapshot(self):
        with self.lock:
            return self.bpm, self.audio_enabled, self.sound

    def _loop(self) -> None:
        next_beat = time.perf_counter()

        while not self.shutdown.is_set():
            if not self.running.is_set():
                self.shutdown.wait(0.02)
                next_beat = time.perf_counter()
                continue

            bpm, audio_enabled, sound = self._snapshot()
            interval = 60.0 / bpm

            now = time.perf_counter()
            wait_for = next_beat - now
            if wait_for > 0:
                self.shutdown.wait(min(wait_for, 0.01))
                continue

            # Beat event is passed to the UI thread through a queue.
            self.beat_queue.put(now)

            if audio_enabled and sound is not None:
                try:
                    sound.play()
                except pygame.error:
                    pass

            next_beat += interval

            # If the machine stalls, resume from "now" instead of firing
            # a burst of delayed beats to catch up.
            if next_beat < time.perf_counter() - interval:
                next_beat = time.perf_counter() + interval


class MetronomeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")

        self.title("Metronome | LostXRP")
        self.geometry("540x720")
        self.minsize(500, 680)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.settings = self.load_settings()
        self.beat_queue: queue.SimpleQueue = queue.SimpleQueue()
        self.hotkey_toggle = threading.Event()
        self.engine = MetronomeEngine(self.beat_queue)

        self.is_running = False
        self.pulse_after_id = None
        self.hotkey_handle = None
        self.audio_ready = False

        self._init_audio()
        self._build_ui()
        self._apply_settings()
        self._register_hotkey()

        self.after(15, self._process_events)

    # ---------- persistence ----------

    def load_settings(self) -> dict:
        data = DEFAULT_SETTINGS.copy()
        path = settings_path()

        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data.update({k: loaded[k] for k in data.keys() if k in loaded})
            except (OSError, json.JSONDecodeError):
                pass

        return data

    def save_settings(self) -> None:
        self.settings.update(
            {
                "bpm": round(float(self.bpm_var.get()), 2),
                "volume": round(float(self.volume_var.get()), 2),
                "audio_enabled": bool(self.audio_var.get()),
                "visual_enabled": bool(self.visual_var.get()),
                "always_on_top": bool(self.top_var.get()),
                "compact_mode": bool(self.compact_var.get()),
            }
        )

        try:
            settings_path().write_text(
                json.dumps(self.settings, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    # ---------- audio ----------

    def _init_audio(self) -> None:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)
            self.audio_ready = True
        except pygame.error:
            self.audio_ready = False
            return

        custom_path = str(self.settings.get("sound_path", "")).strip()
        candidate = Path(custom_path) if custom_path else bundled_path("assets/tick.wav")

        self._load_sound(candidate, persist=False)

    def _load_sound(self, path: Path, persist: bool = True) -> bool:
        if not self.audio_ready or not path.exists():
            self.engine.set_sound(None)
            return False

        try:
            sound = pygame.mixer.Sound(str(path))
            sound.set_volume(float(self.settings.get("volume", 0.70)))
            self.engine.set_sound(sound)

            if persist:
                self.settings["sound_path"] = str(path)
                self.save_settings()

            return True
        except pygame.error:
            self.engine.set_sound(None)
            return False

    def choose_sound(self) -> None:
        selected = filedialog.askopenfilename(
            title="Choose metronome sound",
            filetypes=[
                ("Audio files", "*.wav *.ogg *.mp3"),
                ("WAV files", "*.wav"),
                ("All files", "*.*"),
            ],
        )
        if not selected:
            return

        if self._load_sound(Path(selected), persist=True):
            self.sound_name.configure(text=Path(selected).name)
        else:
            self.sound_name.configure(text="Unable to load sound")

    def reset_sound(self) -> None:
        default = bundled_path("assets/tick.wav")
        if self._load_sound(default, persist=False):
            self.settings["sound_path"] = ""
            self.sound_name.configure(text="Default tick")
            self.save_settings()

    # ---------- UI ----------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 14))
        header.grid_columnconfigure(0, weight=1)

        title_wrap = ctk.CTkFrame(header, fg_color="transparent")
        title_wrap.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_wrap,
            text="METRONOME",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_wrap,
            text="OSRS timing utility  •  LostXRP",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=MUTED,
        ).pack(anchor="w", pady=(1, 0))

        self.status_badge = ctk.CTkLabel(
            header,
            text="  READY  ",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=CARD_ALT,
            corner_radius=10,
            text_color=MUTED,
        )
        self.status_badge.grid(row=0, column=1, sticky="e")

        # Pulse card
        self.pulse_card = ctk.CTkFrame(
            self,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            corner_radius=18,
        )
        self.pulse_card.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 14))
        self.pulse_card.grid_columnconfigure(0, weight=1)

        self.pulse_canvas = ctk.CTkCanvas(
            self.pulse_card,
            width=160,
            height=160,
            bg=CARD,
            highlightthickness=0,
        )
        self.pulse_canvas.grid(row=0, column=0, pady=(22, 6))
        self.pulse_ring = self.pulse_canvas.create_oval(
            20, 20, 140, 140,
            outline=BORDER,
            width=2,
            fill=BG,
        )
        self.pulse_core = self.pulse_canvas.create_oval(
            48, 48, 112, 112,
            outline="",
            fill=CARD_ALT,
        )

        self.live_bpm_label = ctk.CTkLabel(
            self.pulse_card,
            text="100",
            font=ctk.CTkFont(family="Segoe UI", size=42, weight="bold"),
            text_color=TEXT,
        )
        self.live_bpm_label.grid(row=1, column=0)

        ctk.CTkLabel(
            self.pulse_card,
            text="BEATS PER MINUTE",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=MUTED,
        ).grid(row=2, column=0, pady=(0, 20))

        # Tempo card
        self.tempo_card = ctk.CTkFrame(
            self,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            corner_radius=18,
        )
        self.tempo_card.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 14))
        self.tempo_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.tempo_card,
            text="Tempo",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=18, pady=(16, 10))

        minus = self._square_button(self.tempo_card, "−", lambda: self.adjust_bpm(-1))
        minus.grid(row=1, column=0, padx=(18, 10), pady=(0, 10))

        self.bpm_var = ctk.DoubleVar(value=100.0)
        self.bpm_entry = ctk.CTkEntry(
            self.tempo_card,
            width=120,
            justify="center",
            fg_color=BG,
            border_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
        )
        self.bpm_entry.grid(row=1, column=1, pady=(0, 10))
        self.bpm_entry.insert(0, "100")
        self.bpm_entry.bind("<Return>", self._entry_commit)
        self.bpm_entry.bind("<FocusOut>", self._entry_commit)

        plus = self._square_button(self.tempo_card, "+", lambda: self.adjust_bpm(1))
        plus.grid(row=1, column=2, padx=(10, 18), pady=(0, 10))

        self.bpm_slider = ctk.CTkSlider(
            self.tempo_card,
            from_=20,
            to=240,
            number_of_steps=2200,
            command=self._slider_changed,
            fg_color=BG,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
        )
        self.bpm_slider.grid(
            row=2, column=0, columnspan=3, sticky="ew", padx=18, pady=(0, 14)
        )

        self.preset_control = ctk.CTkSegmentedButton(
            self.tempo_card,
            values=["1 tick", "2 ticks", "3 ticks", "4 ticks"],
            command=self.set_preset,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=CARD_ALT,
            unselected_hover_color=BORDER,
            text_color=TEXT,
        )
        self.preset_control.grid(
            row=3, column=0, columnspan=3, sticky="ew", padx=18, pady=(0, 18)
        )

        # Main action button
        self.start_button = ctk.CTkButton(
            self,
            text="START  •  CTRL + SHIFT + C",
            height=48,
            corner_radius=14,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.toggle_metronome,
        )
        self.start_button.grid(row=3, column=0, sticky="ew", padx=28, pady=(0, 14))

        # Settings card
        self.settings_card = ctk.CTkFrame(
            self,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            corner_radius=18,
        )
        self.settings_card.grid(row=4, column=0, sticky="ew", padx=28, pady=(0, 20))
        self.settings_card.grid_columnconfigure((0, 1), weight=1)

        self.audio_var = ctk.BooleanVar(value=True)
        self.visual_var = ctk.BooleanVar(value=True)
        self.top_var = ctk.BooleanVar(value=False)
        self.compact_var = ctk.BooleanVar(value=False)
        self.volume_var = ctk.DoubleVar(value=0.70)

        self._add_switch(
            self.settings_card, "Audio", self.audio_var, self._audio_toggled, 0, 0
        )
        self._add_switch(
            self.settings_card, "Visual pulse", self.visual_var, self.save_settings, 0, 1
        )
        self._add_switch(
            self.settings_card, "Always on top", self.top_var, self._top_toggled, 1, 0
        )
        self._add_switch(
            self.settings_card, "Compact mode", self.compact_var, self._compact_toggled, 1, 1
        )

        volume_wrap = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        volume_wrap.grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(8, 12))
        volume_wrap.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            volume_wrap,
            text="Volume",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, padx=(0, 12))

        self.volume_slider = ctk.CTkSlider(
            volume_wrap,
            from_=0,
            to=1,
            number_of_steps=100,
            variable=self.volume_var,
            command=self._volume_changed,
            fg_color=BG,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
        )
        self.volume_slider.grid(row=0, column=1, sticky="ew")

        sound_wrap = ctk.CTkFrame(self.settings_card, fg_color=CARD_ALT, corner_radius=12)
        sound_wrap.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18)
        )
        sound_wrap.grid_columnconfigure(0, weight=1)

        sound_text = ctk.CTkFrame(sound_wrap, fg_color="transparent")
        sound_text.grid(row=0, column=0, sticky="w", padx=12, pady=10)

        ctk.CTkLabel(
            sound_text,
            text="Sound",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w")

        self.sound_name = ctk.CTkLabel(
            sound_text,
            text="Default tick",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=MUTED,
        )
        self.sound_name.pack(anchor="w")

        ctk.CTkButton(
            sound_wrap,
            text="Choose",
            width=72,
            height=30,
            corner_radius=9,
            fg_color=BORDER,
            hover_color="#343445",
            text_color=TEXT,
            command=self.choose_sound,
        ).grid(row=0, column=1, padx=(6, 6), pady=9)

        ctk.CTkButton(
            sound_wrap,
            text="Reset",
            width=62,
            height=30,
            corner_radius=9,
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            hover_color=BORDER,
            text_color=MUTED,
            command=self.reset_sound,
        ).grid(row=0, column=2, padx=(0, 10), pady=9)

    def _square_button(self, parent, text: str, command):
        return ctk.CTkButton(
            parent,
            text=text,
            width=42,
            height=38,
            corner_radius=10,
            fg_color=CARD_ALT,
            hover_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            command=command,
        )

    def _add_switch(self, parent, label, variable, command, row, column):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=column, sticky="ew", padx=18, pady=(14 if row == 0 else 5, 3))
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box,
            text=label,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkSwitch(
            box,
            text="",
            width=38,
            variable=variable,
            command=command,
            progress_color=ACCENT,
            button_color=TEXT,
            button_hover_color="#FFFFFF",
        ).grid(row=0, column=1, sticky="e")

    # ---------- settings/UI state ----------

    def _apply_settings(self) -> None:
        bpm = self._sanitize_bpm(self.settings.get("bpm", 100.0))
        self.set_bpm(bpm)

        volume = max(0.0, min(1.0, float(self.settings.get("volume", 0.70))))
        self.volume_var.set(volume)
        self.volume_slider.set(volume)

        self.audio_var.set(bool(self.settings.get("audio_enabled", True)))
        self.visual_var.set(bool(self.settings.get("visual_enabled", True)))
        self.top_var.set(bool(self.settings.get("always_on_top", False)))
        self.compact_var.set(bool(self.settings.get("compact_mode", False)))

        self.engine.set_audio_enabled(self.audio_var.get())
        self.attributes("-topmost", self.top_var.get())
        self._volume_changed(volume)

        custom_path = str(self.settings.get("sound_path", "")).strip()
        if custom_path:
            self.sound_name.configure(text=Path(custom_path).name)

        self._sync_preset_display(bpm)

        if self.compact_var.get():
            self.after(50, self._apply_compact_layout)

    def _sanitize_bpm(self, value) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 100.0
        return max(20.0, min(240.0, number))

    def set_bpm(self, bpm: float) -> None:
        bpm = self._sanitize_bpm(bpm)
        self.bpm_var.set(bpm)
        self.bpm_slider.set(bpm)
        self.engine.set_bpm(bpm)

        display = f"{bpm:.2f}".rstrip("0").rstrip(".")
        self.bpm_entry.delete(0, "end")
        self.bpm_entry.insert(0, display)
        self.live_bpm_label.configure(text=display)

        self._sync_preset_display(bpm)
        self.save_settings()

    def adjust_bpm(self, delta: float) -> None:
        self.set_bpm(float(self.bpm_var.get()) + delta)

    def _entry_commit(self, _event=None) -> None:
        self.set_bpm(self._sanitize_bpm(self.bpm_entry.get()))

    def _slider_changed(self, value: float) -> None:
        self.set_bpm(round(float(value), 1))

    def set_preset(self, value: str) -> None:
        presets = {
            "1 tick": 100.0,
            "2 ticks": 50.0,
            "3 ticks": 100.0 / 3.0,
            "4 ticks": 25.0,
        }
        if value in presets:
            self.set_bpm(presets[value])

    def _sync_preset_display(self, bpm: float) -> None:
        candidates = {
            "1 tick": 100.0,
            "2 ticks": 50.0,
            "3 ticks": 100.0 / 3.0,
            "4 ticks": 25.0,
        }
        for name, value in candidates.items():
            if abs(bpm - value) < 0.06:
                self.preset_control.set(name)
                return
        self.preset_control.set("")

    def _audio_toggled(self) -> None:
        self.engine.set_audio_enabled(self.audio_var.get())
        self.save_settings()

    def _top_toggled(self) -> None:
        self.attributes("-topmost", self.top_var.get())
        self.save_settings()

    def _volume_changed(self, value: float) -> None:
        volume = max(0.0, min(1.0, float(value)))
        self.volume_var.set(volume)
        _, _, sound = self.engine._snapshot()
        if sound is not None:
            sound.set_volume(volume)
        self.save_settings()

    def _compact_toggled(self) -> None:
        self._apply_compact_layout()
        self.save_settings()

    def _apply_compact_layout(self) -> None:
        compact = self.compact_var.get()

        if compact:
            self.tempo_card.grid_remove()
            self.settings_card.grid_remove()
            self.geometry("390x430")
            self.minsize(370, 410)
        else:
            self.tempo_card.grid()
            self.settings_card.grid()
            self.geometry("540x720")
            self.minsize(500, 680)

    # ---------- metronome ----------

    def _register_hotkey(self) -> None:
        try:
            self.hotkey_handle = keyboard.add_hotkey(
                HOTKEY,
                lambda: self.hotkey_toggle.set(),
                suppress=False,
                trigger_on_release=False,
            )
        except Exception:
            self.hotkey_handle = None
            self.start_button.configure(text="START")

    def toggle_metronome(self) -> None:
        if self.is_running:
            self.stop_metronome()
        else:
            self.start_metronome()

    def start_metronome(self) -> None:
        self.is_running = True
        self.engine.start()
        self.start_button.configure(
            text="STOP  •  CTRL + SHIFT + C",
            fg_color=DANGER,
            hover_color="#E85D75",
        )
        self.status_badge.configure(
            text="  RUNNING  ",
            fg_color="#123127",
            text_color=SUCCESS,
        )

    def stop_metronome(self) -> None:
        self.is_running = False
        self.engine.stop()
        self.start_button.configure(
            text="START  •  CTRL + SHIFT + C",
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
        )
        self.status_badge.configure(
            text="  READY  ",
            fg_color=CARD_ALT,
            text_color=MUTED,
        )
        self._reset_pulse()

    def _process_events(self) -> None:
        if self.hotkey_toggle.is_set():
            self.hotkey_toggle.clear()
            self.toggle_metronome()

        got_beat = False
        while True:
            try:
                self.beat_queue.get_nowait()
                got_beat = True
            except queue.Empty:
                break

        if got_beat and self.visual_var.get() and self.is_running:
            self._pulse()

        if self.winfo_exists():
            self.after(15, self._process_events)

    def _pulse(self) -> None:
        if self.pulse_after_id is not None:
            try:
                self.after_cancel(self.pulse_after_id)
            except Exception:
                pass

        self.pulse_canvas.itemconfigure(
            self.pulse_ring,
            outline=ACCENT,
            width=4,
        )
        self.pulse_canvas.itemconfigure(
            self.pulse_core,
            fill=ACCENT,
        )

        self.pulse_after_id = self.after(110, self._reset_pulse)

    def _reset_pulse(self) -> None:
        try:
            self.pulse_canvas.itemconfigure(
                self.pulse_ring,
                outline=BORDER,
                width=2,
            )
            self.pulse_canvas.itemconfigure(
                self.pulse_core,
                fill=CARD_ALT,
            )
        except Exception:
            pass

    # ---------- shutdown ----------

    def on_close(self) -> None:
        self.save_settings()
        self.engine.close()

        if self.hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self.hotkey_handle)
            except Exception:
                pass

        try:
            pygame.mixer.quit()
        except pygame.error:
            pass

        self.destroy()


if __name__ == "__main__":
    app = MetronomeApp()
    app.mainloop()
