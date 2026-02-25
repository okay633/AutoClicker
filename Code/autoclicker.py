from pynput.keyboard import Key, KeyCode, Listener
import customtkinter
import json
import os
import pydirectinput
import spinbox as spinbox
import sys
import threading
import time
import webbrowser


class App(customtkinter.CTk):
    WIDTH = 470
    HEIGHT = 700

    @staticmethod
    def resource(relative_path):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def __init__(self):
        super().__init__()

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")
        pydirectinput.PAUSE = 0

        self.title("AutoClicker")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.running_mode = None
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.listener = None
        self.started_at = None
        self.total_actions = 0

        self.preset_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets.json")

        self.button_var = customtkinter.StringVar(value="Left")
        self.clicktype_var = customtkinter.StringVar(value="Single")
        self.interval_var = customtkinter.StringVar(value="0.01")
        self.delay_var = customtkinter.StringVar(value="0")
        self.repeat_mode_var = customtkinter.StringVar(value="Until Stopped")
        self.theme_var = customtkinter.StringVar(value="Dark")
        self.keyboard_key_var = customtkinter.StringVar(value="w")
        self.hotkey_click_var = customtkinter.StringVar(value="f5")
        self.hotkey_hold_var = customtkinter.StringVar(value="f6")
        self.preset_name_var = customtkinter.StringVar(value="")
        self.preset_selected_var = customtkinter.StringVar(value="Select preset")

        self.topmost_var = customtkinter.BooleanVar(value=True)
        self.status_var = customtkinter.StringVar(value="Idle")
        self.total_actions_var = customtkinter.StringVar(value="0")
        self.runtime_var = customtkinter.StringVar(value="0.0s")
        self.hotkey_click = Key.f5
        self.hotkey_hold = Key.f6
        self.credits_window = None

        self.build_ui()
        self.apply_hotkeys(show_status=False)
        self.refresh_presets()
        self.start_global_hotkeys()
        self.update_runtime()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.container = customtkinter.CTkFrame(self)
        self.container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.container.grid_columnconfigure(0, weight=1)

        header = customtkinter.CTkFrame(self.container)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)

        self.menu_button = customtkinter.CTkButton(
            header,
            text="☰",
            width=38,
            command=self.open_credits,
            font=("Roboto Medium", 18),
        )
        self.menu_button.grid(row=0, column=0, sticky="nw", padx=(12, 2), pady=(10, 0))

        title = customtkinter.CTkLabel(header, text="AutoClicker", font=("Roboto Medium", 24))
        title.grid(row=0, column=1, sticky="w", padx=12, pady=(10, 2))

        self.subtitle_label = customtkinter.CTkLabel(
            header,
            text="Click: F5  •  Hold: F6",
            font=("Roboto Medium", 13),
        )
        self.subtitle_label.grid(row=1, column=1, sticky="w", padx=12, pady=(0, 4))

        watermark = customtkinter.CTkLabel(
            header,
            text="it is me zed",
            font=("Roboto Medium", 12),
            text_color=("gray40", "gray70"),
        )
        watermark.grid(row=2, column=1, sticky="e", padx=12, pady=(0, 10))

        controls = customtkinter.CTkFrame(self.container)
        controls.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        controls.grid_columnconfigure((0, 1), weight=1)

        self.start_auto_button = customtkinter.CTkButton(
            controls,
            text="Start",
            command=self.start_button,
            font=("Roboto Medium", 15),
        )
        self.start_auto_button.grid(row=0, column=0, padx=(12, 6), pady=12, sticky="ew")

        self.stop_auto_button = customtkinter.CTkButton(
            controls,
            text="Stop",
            state="disabled",
            command=self.stop_button,
            font=("Roboto Medium", 15),
        )
        self.stop_auto_button.grid(row=0, column=1, padx=(6, 12), pady=12, sticky="ew")

        config_frame = customtkinter.CTkFrame(self.container)
        config_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=8)
        config_frame.grid_columnconfigure((0, 1), weight=1)

        customtkinter.CTkLabel(config_frame, text="Button", font=("Roboto Medium", 13)).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 0)
        )
        customtkinter.CTkLabel(config_frame, text="Click Type", font=("Roboto Medium", 13)).grid(
            row=0, column=1, sticky="w", padx=12, pady=(10, 0)
        )

        self.buttonmenu = customtkinter.CTkComboBox(
            config_frame,
            variable=self.button_var,
            values=["Left", "Middle", "Right", "Keyboard"],
            command=self.on_button_change,
        )
        self.buttonmenu.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 10))

        self.clicktypemenu = customtkinter.CTkOptionMenu(
            config_frame,
            variable=self.clicktype_var,
            values=["Single", "Double", "Triple", "Hold"],
        )
        self.clicktypemenu.grid(row=1, column=1, sticky="ew", padx=12, pady=(4, 10))

        customtkinter.CTkLabel(config_frame, text="Keyboard Key", font=("Roboto Medium", 13)).grid(
            row=2, column=0, sticky="w", padx=12, pady=(2, 0)
        )
        self.key_entry = customtkinter.CTkEntry(config_frame, textvariable=self.keyboard_key_var)
        self.key_entry.grid(row=3, column=0, sticky="ew", padx=12, pady=(4, 12))

        timing_frame = customtkinter.CTkFrame(self.container)
        timing_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=8)
        timing_frame.grid_columnconfigure((0, 1), weight=1)

        customtkinter.CTkLabel(timing_frame, text="Interval (s)", font=("Roboto Medium", 13)).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 0)
        )
        customtkinter.CTkLabel(timing_frame, text="Start Delay (s)", font=("Roboto Medium", 13)).grid(
            row=0, column=1, sticky="w", padx=12, pady=(10, 0)
        )

        self.clickinterval = customtkinter.CTkEntry(timing_frame, textvariable=self.interval_var)
        self.clickinterval.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 12))

        self.delay_entry = customtkinter.CTkEntry(timing_frame, textvariable=self.delay_var)
        self.delay_entry.grid(row=1, column=1, sticky="ew", padx=12, pady=(4, 12))

        repeat_frame = customtkinter.CTkFrame(self.container)
        repeat_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=8)
        repeat_frame.grid_columnconfigure((0, 1), weight=1)

        self.repeat_until = customtkinter.CTkRadioButton(
            repeat_frame,
            text="Until Stopped",
            variable=self.repeat_mode_var,
            value="Until Stopped",
        )
        self.repeat_until.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        self.repeat_times = customtkinter.CTkRadioButton(
            repeat_frame,
            text="Repeat Count",
            variable=self.repeat_mode_var,
            value="Repeat Count",
        )
        self.repeat_times.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

        self.repeattimes = spinbox.FloatSpinbox(repeat_frame, width=130, height=30, step_size=1)
        self.repeattimes.grid(row=0, column=1, rowspan=2, sticky="e", padx=12, pady=12)
        self.repeattimes.set(1)

        hotkey_frame = customtkinter.CTkFrame(self.container)
        hotkey_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=8)
        hotkey_frame.grid_columnconfigure((0, 1, 2), weight=1)

        customtkinter.CTkLabel(hotkey_frame, text="Toggle Click Hotkey", font=("Roboto Medium", 13)).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 0)
        )
        customtkinter.CTkLabel(hotkey_frame, text="Toggle Hold Hotkey", font=("Roboto Medium", 13)).grid(
            row=0, column=1, sticky="w", padx=12, pady=(10, 0)
        )

        self.hotkey_click_entry = customtkinter.CTkEntry(hotkey_frame, textvariable=self.hotkey_click_var)
        self.hotkey_click_entry.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 10))

        self.hotkey_hold_entry = customtkinter.CTkEntry(hotkey_frame, textvariable=self.hotkey_hold_var)
        self.hotkey_hold_entry.grid(row=1, column=1, sticky="ew", padx=12, pady=(4, 10))

        self.apply_hotkey_btn = customtkinter.CTkButton(hotkey_frame, text="Apply", command=self.apply_hotkeys)
        self.apply_hotkey_btn.grid(row=1, column=2, sticky="ew", padx=12, pady=(4, 10))

        extras_frame = customtkinter.CTkFrame(self.container)
        extras_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=8)
        extras_frame.grid_columnconfigure((0, 1), weight=1)

        customtkinter.CTkLabel(extras_frame, text="Theme", font=("Roboto Medium", 13)).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 0)
        )
        self.theme_menu = customtkinter.CTkOptionMenu(
            extras_frame,
            variable=self.theme_var,
            values=["Dark", "Light", "System"],
            command=self.change_theme,
        )
        self.theme_menu.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 10))

        self.topmost_switch = customtkinter.CTkSwitch(
            extras_frame,
            text="Always on top",
            variable=self.topmost_var,
            command=self.toggle_topmost,
        )
        self.topmost_switch.select()
        self.topmost_switch.grid(row=1, column=1, sticky="w", padx=12, pady=(4, 10))

        presets_frame = customtkinter.CTkFrame(self.container)
        presets_frame.grid(row=7, column=0, sticky="ew", padx=10, pady=8)
        presets_frame.grid_columnconfigure((0, 1, 2), weight=1)

        customtkinter.CTkLabel(presets_frame, text="Presets", font=("Roboto Medium", 13)).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 0)
        )

        self.preset_entry = customtkinter.CTkEntry(presets_frame, textvariable=self.preset_name_var, placeholder_text="Preset name")
        self.preset_entry.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 10))

        self.preset_select = customtkinter.CTkComboBox(
            presets_frame,
            variable=self.preset_selected_var,
            values=["Select preset"],
            command=self.load_preset,
            state="readonly",
        )
        self.preset_select.grid(row=1, column=1, sticky="ew", padx=12, pady=(4, 10))

        self.save_preset_btn = customtkinter.CTkButton(presets_frame, text="Save", command=self.save_preset)
        self.save_preset_btn.grid(row=1, column=2, sticky="ew", padx=12, pady=(4, 10))

        stats_frame = customtkinter.CTkFrame(self.container)
        stats_frame.grid(row=8, column=0, sticky="ew", padx=10, pady=(8, 10))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        customtkinter.CTkLabel(stats_frame, text="Status", font=("Roboto Medium", 13)).grid(
            row=0, column=0, padx=12, pady=(10, 0), sticky="w"
        )
        customtkinter.CTkLabel(stats_frame, text="Total Actions", font=("Roboto Medium", 13)).grid(
            row=0, column=1, padx=12, pady=(10, 0), sticky="w"
        )
        customtkinter.CTkLabel(stats_frame, text="Runtime", font=("Roboto Medium", 13)).grid(
            row=0, column=2, padx=12, pady=(10, 0), sticky="w"
        )

        customtkinter.CTkLabel(stats_frame, textvariable=self.status_var).grid(
            row=1, column=0, padx=12, pady=(4, 12), sticky="w"
        )
        customtkinter.CTkLabel(stats_frame, textvariable=self.total_actions_var).grid(
            row=1, column=1, padx=12, pady=(4, 12), sticky="w"
        )
        customtkinter.CTkLabel(stats_frame, textvariable=self.runtime_var).grid(
            row=1, column=2, padx=12, pady=(4, 12), sticky="w"
        )

        self.on_button_change(self.button_var.get())

    def parse_float(self, value, fallback, minimum=None, maximum=None):
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = fallback

        if minimum is not None:
            parsed = max(minimum, parsed)
        if maximum is not None:
            parsed = min(maximum, parsed)
        return parsed

    def parse_repeat_count(self):
        raw_value = self.repeattimes.get()
        if raw_value is None:
            return 1
        return max(1, int(raw_value))

    def change_theme(self, selected):
        customtkinter.set_appearance_mode(selected.lower())

    def toggle_topmost(self):
        self.attributes("-topmost", bool(self.topmost_var.get()))

    def parse_hotkey(self, value):
        if value is None:
            return None

        token = str(value).strip().lower()
        if not token:
            return None

        if token.startswith("key."):
            token = token[4:]

        aliases = {
            "esc": "escape",
            "return": "enter",
            "control": "ctrl",
            "pgup": "page_up",
            "pgdn": "page_down",
        }
        token = aliases.get(token, token)

        named_keys = {
            "space": Key.space,
            "enter": Key.enter,
            "tab": Key.tab,
            "backspace": Key.backspace,
            "delete": Key.delete,
            "insert": Key.insert,
            "home": Key.home,
            "end": Key.end,
            "page_up": Key.page_up,
            "page_down": Key.page_down,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
            "shift": Key.shift,
            "ctrl": Key.ctrl,
            "alt": Key.alt,
            "caps_lock": Key.caps_lock,
            "num_lock": Key.num_lock,
            "scroll_lock": Key.scroll_lock,
            "pause": Key.pause,
            "print_screen": Key.print_screen,
            "menu": Key.menu,
            "cmd": Key.cmd,
        }

        if token in named_keys:
            return named_keys[token]

        if token.startswith("f") and token[1:].isdigit():
            number = int(token[1:])
            if 1 <= number <= 20:
                return getattr(Key, f"f{number}")

        if len(token) == 1:
            return KeyCode.from_char(token)

        return None

    def hotkey_matches(self, pressed, configured):
        if isinstance(configured, Key):
            return pressed == configured

        if isinstance(configured, KeyCode):
            if not isinstance(pressed, KeyCode):
                return False
            if pressed.char is None or configured.char is None:
                return pressed == configured
            return pressed.char.lower() == configured.char.lower()

        return False

    def format_hotkey(self, value):
        return value.strip().upper() if value.strip() else "?"

    def update_hotkey_subtitle(self):
        self.subtitle_label.configure(
            text=f"Click: {self.format_hotkey(self.hotkey_click_var.get())}  •  Hold: {self.format_hotkey(self.hotkey_hold_var.get())}"
        )

    def apply_hotkeys(self, show_status=True):
        click_text = self.hotkey_click_var.get().strip().lower() or "f5"
        hold_text = self.hotkey_hold_var.get().strip().lower() or "f6"

        click_key = self.parse_hotkey(click_text)
        hold_key = self.parse_hotkey(hold_text)

        if click_key is None or hold_key is None:
            if show_status:
                self.status_var.set("Invalid hotkey. Example: f5, g, space")
            return

        if click_text == hold_text:
            if show_status:
                self.status_var.set("Hotkeys must be different")
            return

        self.hotkey_click_var.set(click_text)
        self.hotkey_hold_var.set(hold_text)
        self.hotkey_click = click_key
        self.hotkey_hold = hold_key
        self.update_hotkey_subtitle()

        if show_status:
            self.status_var.set("Hotkeys updated")

    def on_button_change(self, selected):
        if selected == "Keyboard":
            self.key_entry.configure(state="normal")
        else:
            self.key_entry.configure(state="disabled")

    def start_global_hotkeys(self):
        self.listener = Listener(on_press=self.on_global_press)
        self.listener.start()

    def on_global_press(self, key):
        if self.hotkey_matches(key, self.hotkey_click):
            if self.running_mode == "click":
                self.stop_button()
            elif self.running_mode is None:
                self.start_click_mode()
            return

        if self.hotkey_matches(key, self.hotkey_hold):
            if self.running_mode == "hold":
                self.stop_button()
            elif self.running_mode is None:
                self.start_hold_mode()

    def update_runtime(self):
        if self.started_at is None:
            self.runtime_var.set("0.0s")
        else:
            elapsed = time.monotonic() - self.started_at
            self.runtime_var.set(f"{elapsed:.1f}s")
        self.after(200, self.update_runtime)

    def get_target(self):
        target = self.button_var.get()
        if target == "Keyboard":
            key = self.keyboard_key_var.get().strip().lower()
            if not key:
                return "w"
            return key
        return target.lower()

    def set_running_ui_state(self, is_running):
        if is_running:
            self.buttonmenu.configure(state="disabled")
            self.clicktypemenu.configure(state="disabled")
            self.clickinterval.configure(state="disabled")
            self.delay_entry.configure(state="disabled")
            self.repeattimes.configure(state="disabled")
            self.start_auto_button.configure(state="disabled")
            self.stop_auto_button.configure(state="normal")
            self.key_entry.configure(state="disabled")
            self.hotkey_click_entry.configure(state="disabled")
            self.hotkey_hold_entry.configure(state="disabled")
            self.apply_hotkey_btn.configure(state="disabled")
            self.status_var.set("Running")
            self.started_at = time.monotonic()
        else:
            self.buttonmenu.configure(state="normal")
            self.clicktypemenu.configure(state="normal")
            self.clickinterval.configure(state="normal")
            self.delay_entry.configure(state="normal")
            self.repeattimes.configure(state="normal")
            self.start_auto_button.configure(state="normal")
            self.stop_auto_button.configure(state="disabled")
            self.on_button_change(self.button_var.get())
            self.hotkey_click_entry.configure(state="normal")
            self.hotkey_hold_entry.configure(state="normal")
            self.apply_hotkey_btn.configure(state="normal")
            if self.status_var.get() != "Saved preset":
                self.status_var.set("Idle")
            self.started_at = None

    def start_button(self):
        if self.running_mode is not None:
            return

        if self.clicktype_var.get() == "Hold":
            self.start_hold_mode()
        else:
            self.start_click_mode()

    def start_click_mode(self):
        if self.running_mode is not None:
            return

        interval = self.parse_float(self.interval_var.get(), 0.01, minimum=0.001)
        delay = self.parse_float(self.delay_var.get(), 0.0, minimum=0.0, maximum=30.0)
        click_type = self.clicktype_var.get()
        if click_type == "Hold":
            click_type = "Single"

        repeat_count = None
        if self.repeat_mode_var.get() == "Repeat Count":
            repeat_count = self.parse_repeat_count()

        self.stop_event.clear()
        self.running_mode = "click"
        self.set_running_ui_state(True)
        self.status_var.set("Running click mode")

        self.worker_thread = threading.Thread(
            target=self.click_worker,
            args=(click_type, interval, delay, repeat_count),
            daemon=True,
        )
        self.worker_thread.start()

    def start_hold_mode(self):
        if self.running_mode is not None:
            return

        delay = self.parse_float(self.delay_var.get(), 0.0, minimum=0.0, maximum=30.0)
        self.stop_event.clear()
        self.running_mode = "hold"
        self.set_running_ui_state(True)
        self.status_var.set("Running hold mode")

        self.worker_thread = threading.Thread(
            target=self.hold_worker,
            args=(delay,),
            daemon=True,
        )
        self.worker_thread.start()

    def perform_click(self, click_type, target):
        if click_type == "Single":
            count = 1
        elif click_type == "Double":
            count = 2
        else:
            count = 3

        if target in {"left", "middle", "right"}:
            for _ in range(count):
                pydirectinput.click(button=target)
                self.total_actions += 1
        else:
            for _ in range(count):
                pydirectinput.press(target)
                self.total_actions += 1

        self.total_actions_var.set(str(self.total_actions))

    def click_worker(self, click_type, interval, delay, repeat_count):
        if delay > 0:
            started = time.monotonic()
            while not self.stop_event.is_set() and time.monotonic() - started < delay:
                time.sleep(0.02)

        target = self.get_target()
        completed = 0

        while not self.stop_event.is_set():
            self.perform_click(click_type, target)
            completed += 1

            if repeat_count is not None and completed >= repeat_count:
                break

            sleep_for = interval
            started = time.monotonic()
            while not self.stop_event.is_set() and time.monotonic() - started < sleep_for:
                time.sleep(0.002)

        self.after(0, self.stop_button, True)

    def hold_worker(self, delay):
        if delay > 0:
            started = time.monotonic()
            while not self.stop_event.is_set() and time.monotonic() - started < delay:
                time.sleep(0.02)

        target = self.get_target()
        if target in {"left", "middle", "right"}:
            pydirectinput.mouseDown(button=target)
        else:
            pydirectinput.keyDown(target)

        while not self.stop_event.is_set():
            time.sleep(0.01)

        if target in {"left", "middle", "right"}:
            pydirectinput.mouseUp(button=target)
        else:
            pydirectinput.keyUp(target)

        self.after(0, self.stop_button, True)

    def stop_button(self, from_worker=False):
        self.stop_event.set()

        if not from_worker and self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=0.25)

        self.running_mode = None
        self.worker_thread = None
        self.set_running_ui_state(False)

    def load_presets_data(self):
        if not os.path.exists(self.preset_file):
            return {}
        try:
            with open(self.preset_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict):
                return data
            return {}
        except (json.JSONDecodeError, OSError):
            return {}

    def save_presets_data(self, data):
        with open(self.preset_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def refresh_presets(self):
        data = self.load_presets_data()
        names = sorted(data.keys())
        if not names:
            names = ["Select preset"]
        self.preset_select.configure(values=names)

        if self.preset_selected_var.get() not in names:
            self.preset_selected_var.set(names[0])

    def snapshot_settings(self):
        return {
            "button": self.button_var.get(),
            "click_type": self.clicktype_var.get(),
            "keyboard_key": self.keyboard_key_var.get(),
            "interval": self.interval_var.get(),
            "delay": self.delay_var.get(),
            "repeat_mode": self.repeat_mode_var.get(),
            "repeat_count": str(self.parse_repeat_count()),
            "theme": self.theme_var.get(),
            "topmost": bool(self.topmost_var.get()),
            "hotkey_click": self.hotkey_click_var.get(),
            "hotkey_hold": self.hotkey_hold_var.get(),
        }

    def apply_settings(self, settings):
        self.button_var.set(settings.get("button", "Left"))
        self.clicktype_var.set(settings.get("click_type", "Single"))
        self.keyboard_key_var.set(settings.get("keyboard_key", "w"))
        self.interval_var.set(settings.get("interval", "0.01"))
        self.delay_var.set(settings.get("delay", "0"))
        self.repeat_mode_var.set(settings.get("repeat_mode", "Until Stopped"))
        self.hotkey_click_var.set(settings.get("hotkey_click", "f5"))
        self.hotkey_hold_var.set(settings.get("hotkey_hold", "f6"))
        self.apply_hotkeys(show_status=False)

        repeat_count = settings.get("repeat_count", "1")
        self.repeattimes.set(self.parse_float(repeat_count, 1, minimum=1))

        theme = settings.get("theme", "Dark")
        self.theme_var.set(theme)
        self.change_theme(theme)

        topmost = bool(settings.get("topmost", True))
        self.topmost_var.set(topmost)
        if topmost:
            self.topmost_switch.select()
        else:
            self.topmost_switch.deselect()
        self.toggle_topmost()

        self.on_button_change(self.button_var.get())

    def open_credits(self):
        if self.credits_window is not None and self.credits_window.winfo_exists():
            self.credits_window.focus()
            return

        self.credits_window = customtkinter.CTkToplevel(self)
        self.credits_window.title("Credits")
        self.credits_window.geometry("430x250")
        self.credits_window.resizable(False, False)
        self.credits_window.attributes("-topmost", bool(self.topmost_var.get()))

        frame = customtkinter.CTkFrame(self.credits_window)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        customtkinter.CTkLabel(frame, text="Credits", font=("Roboto Medium", 22)).pack(anchor="w", padx=12, pady=(12, 4))
        customtkinter.CTkLabel(
            frame,
            text="This project is based on:\nhttps://github.com/zSynctic/AutoClicker\n\nThis version contains additional improvements.",
            justify="left",
            font=("Roboto Medium", 13),
            wraplength=390,
        ).pack(anchor="w", padx=12, pady=(0, 10))

        buttons = customtkinter.CTkFrame(frame, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(0, 12))

        customtkinter.CTkButton(
            buttons,
            text="Open Original Repo",
            command=lambda: webbrowser.open("https://github.com/zSynctic/AutoClicker"),
        ).pack(side="left")

        customtkinter.CTkButton(buttons, text="Close", command=self.credits_window.destroy).pack(side="right")

    def save_preset(self):
        name = self.preset_name_var.get().strip()
        if not name:
            self.status_var.set("Enter preset name")
            return

        data = self.load_presets_data()
        data[name] = self.snapshot_settings()
        self.save_presets_data(data)
        self.refresh_presets()
        self.preset_selected_var.set(name)
        self.status_var.set("Saved preset")

    def load_preset(self, preset_name):
        if not preset_name or preset_name == "Select preset":
            return
        data = self.load_presets_data()
        settings = data.get(preset_name)
        if not settings:
            self.status_var.set("Preset not found")
            return
        self.apply_settings(settings)
        self.status_var.set(f"Loaded {preset_name}")

    def on_close(self, event=0):
        self.stop_event.set()
        if self.listener is not None:
            self.listener.stop()
        self.destroy()

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    app = App()
    app.start()
