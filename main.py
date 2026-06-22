"""
WoW Font Replacer — A premium CustomTkinter desktop app for replacing
World of Warcraft fonts for readability and style.

Automates copying and renaming .ttf/.otf font files into the correct
WoW Fonts folder with exact naming conventions.
"""

import os
import sys
import shutil
import ctypes
import json
import tkinter as tk
from tkinter import filedialog, font as tkfont
from pathlib import Path

import customtkinter as ctk
from PIL import Image

def get_config_path() -> str:
    """Return path to config.json file in the application directory."""
    try:
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    except Exception:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "config.json")

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, working for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

BUNDLED_FONTS = {
    "[Bundled] Lexend Regular": "Lexend-Regular.ttf",
    "[Bundled] OpenDyslexic Regular": "OpenDyslexic-Regular.otf",
    "[Bundled] Atkinson Hyperlegible": "AtkinsonHyperlegible-Regular.ttf",
    "[Bundled] Comic Neue": "ComicNeue-Regular.ttf",
}



# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APP_TITLE = "WoW Font Replacer"
APP_SIZE = (820, 880)

# Exact filenames WoW expects (case-sensitive)
FONT_SLOTS = {
    "friz": {
        "target": "FRIZQT__.ttf",          # 2 underscores
        "cyr_target": "FRIZQT___CYR.ttf",  # 3 underscores
        "display_name": "Friz Quadrata",
        "subtitle": "The \"Everything Else\" Font",
        "description": "Quest text, nameplates, vendor dialogues, server lists, and nearly all other in-game text.",
    },
    "morpheus": {
        "target": "MORPHEUS.ttf",
        "cyr_target": "MORPHEUS_CYR.ttf",
        "display_name": "Morpheus",
        "subtitle": "The Ornamental Font",
        "description": "Quest titles, mail text, and interactable book text.",
    },
    "arialn": {
        "target": "ARIALN.ttf",
        "cyr_target": "ARIALN_CYR.ttf",
        "display_name": "Arial Narrow",
        "subtitle": "The Chat Font",
        "description": "In-game chat, money displays, and experience text.",
    },
    "skurri": {
        "target": "skurri.ttf",
        "cyr_target": "skurri_CYR.ttf",
        "display_name": "Skurri",
        "subtitle": "The Combat Font",
        "description": "Floating damage numbers over combat portraits.",
    },
}

GAME_VERSIONS = {
    "Retail": "_retail_",
    "Classic": "_classic_",
    "Classic Era": "_classic_era_",
}

# Design tokens
COLORS = {
    "bg_dark":       "#0f0f1a",
    "bg_card":       "#181830",
    "bg_card_hover": "#1e1e3a",
    "bg_input":      "#12122a",
    "accent":        "#c4392f",
    "accent_hover":  "#a83028",
    "accent_gold":   "#d4a843",
    "accent_gold_dim": "#a8863a",
    "text_primary":  "#e8e6e3",
    "text_secondary":"#7a7f96",
    "text_muted":    "#4e5268",
    "success":       "#3db87a",
    "warning":       "#d4a843",
    "error":         "#c4392f",
    "border":        "#2a2a4a",
    "border_light":  "#353560",
}

# Common WoW install locations to auto-detect
COMMON_WOW_PATHS = [
    r"C:\Program Files (x86)\World of Warcraft",
    r"C:\Program Files\World of Warcraft",
    r"D:\World of Warcraft",
    r"D:\Games\World of Warcraft",
    r"E:\World of Warcraft",
    r"E:\Games\World of Warcraft",
    r"C:\Games\World of Warcraft",
]


# ---------------------------------------------------------------------------
# Windows Font Registration (for preview)
# ---------------------------------------------------------------------------

FR_PRIVATE = 0x10

def _register_font_win(font_path: str) -> bool:
    """Temporarily register a font on Windows using AddFontResourceExW."""
    try:
        gdi32 = ctypes.windll.gdi32
        result = gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
        return result > 0
    except Exception:
        return False


def _unregister_font_win(font_path: str):
    """Remove a temporarily registered font on Windows."""
    try:
        gdi32 = ctypes.windll.gdi32
        gdi32.RemoveFontResourceExW(font_path, FR_PRIVATE, 0)
    except Exception:
        pass


def _get_font_family_name(font_path: str) -> str | None:
    """
    Extract the font family name from a TTF/OTF file by reading the
    name table directly. Returns None on failure.
    """
    try:
        with open(font_path, "rb") as f:
            data = f.read()

        # Find the 'name' table
        num_tables = int.from_bytes(data[4:6], "big")
        name_table_offset = None
        for i in range(num_tables):
            record_start = 12 + i * 16
            tag = data[record_start:record_start + 4]
            if tag == b"name":
                name_table_offset = int.from_bytes(data[record_start + 8:record_start + 12], "big")
                break

        if name_table_offset is None:
            return None

        # Parse name table
        storage_offset = int.from_bytes(data[name_table_offset + 4:name_table_offset + 6], "big")
        num_records = int.from_bytes(data[name_table_offset + 2:name_table_offset + 4], "big")

        for i in range(num_records):
            rec_start = name_table_offset + 6 + i * 12
            platform_id = int.from_bytes(data[rec_start:rec_start + 2], "big")
            encoding_id = int.from_bytes(data[rec_start + 2:rec_start + 4], "big")
            name_id = int.from_bytes(data[rec_start + 6:rec_start + 8], "big")
            length = int.from_bytes(data[rec_start + 8:rec_start + 10], "big")
            offset = int.from_bytes(data[rec_start + 10:rec_start + 12], "big")

            # name_id 1 = Font Family
            if name_id == 1:
                string_data = data[name_table_offset + storage_offset + offset:
                                   name_table_offset + storage_offset + offset + length]
                if platform_id == 3:  # Windows
                    return string_data.decode("utf-16-be", errors="ignore")
                elif platform_id == 1:  # Mac
                    return string_data.decode("latin-1", errors="ignore")

    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# FontManager — file operations
# ---------------------------------------------------------------------------

class FontManager:
    """Handles all font file operations: validation, copying, cleanup."""

    @staticmethod
    def detect_wow_path() -> str | None:
        """Try to auto-detect WoW install folder."""
        for path in COMMON_WOW_PATHS:
            if os.path.isdir(path):
                return path
        return None

    @staticmethod
    def get_fonts_dir(wow_path: str, version_subfolder: str) -> Path:
        """Return the Fonts directory path for a given WoW version."""
        return Path(wow_path) / version_subfolder / "Fonts"

    @staticmethod
    def validate_font_file(filepath: str) -> tuple[bool, str]:
        """Check that a file is a valid .ttf or .otf font."""
        if not os.path.isfile(filepath):
            return False, "File does not exist."

        ext = os.path.splitext(filepath)[1].lower()
        if ext not in (".ttf", ".otf"):
            return False, f"Invalid format '{ext}'. Only .ttf and .otf files are supported."

        # Basic magic number check
        try:
            with open(filepath, "rb") as f:
                header = f.read(4)
            # TrueType: 00 01 00 00 or 'true'
            # OpenType: 'OTTO'
            valid_headers = [b"\x00\x01\x00\x00", b"true", b"OTTO"]
            if header not in valid_headers:
                return False, "File does not appear to be a valid TrueType or OpenType font."
        except Exception as e:
            return False, f"Could not read file: {e}"

        return True, "Valid font file."

    @staticmethod
    def validate_wow_path(wow_path: str, version_subfolder: str) -> tuple[bool, str]:
        """Check that the WoW path and version subfolder exist."""
        base = Path(wow_path)
        if not base.is_dir():
            return False, "WoW folder does not exist."

        version_dir = base / version_subfolder
        if not version_dir.is_dir():
            return False, f"Version folder '{version_subfolder}' not found inside WoW directory."

        return True, "Valid path."

    @staticmethod
    def apply_fonts(
        wow_path: str,
        version_subfolder: str,
        assignments: dict[str, str | None],
        include_cyrillic: bool,
    ) -> tuple[bool, str]:
        """
        Copy and rename font files into the WoW Fonts folder.

        assignments: dict mapping slot key -> source font filepath (or None to skip)
        """
        fonts_dir = FontManager.get_fonts_dir(wow_path, version_subfolder)

        # Create Fonts folder if needed
        try:
            fonts_dir.mkdir(parents=False, exist_ok=True)
        except Exception as e:
            return False, f"Could not create Fonts folder: {e}"

        applied = []
        errors = []

        for slot_key, source_path in assignments.items():
            if source_path is None:
                continue

            slot = FONT_SLOTS[slot_key]
            target_name = slot["target"]

            try:
                dest = fonts_dir / target_name
                shutil.copy2(source_path, dest)
                applied.append(target_name)

                # Cyrillic variant
                if include_cyrillic:
                    cyr_name = slot["cyr_target"]
                    cyr_dest = fonts_dir / cyr_name
                    shutil.copy2(source_path, cyr_dest)
                    applied.append(cyr_name)

            except Exception as e:
                errors.append(f"{slot['display_name']}: {e}")

        if errors:
            return False, f"Applied {len(applied)} file(s) with errors:\n" + "\n".join(errors)

        if not applied:
            return False, "No fonts were selected to apply."

        return True, f"Successfully applied {len(applied)} font file(s) to:\n{fonts_dir}"

    @staticmethod
    def restore_defaults(wow_path: str, version_subfolder: str) -> tuple[bool, str]:
        """Remove all custom font replacement files from the Fonts folder."""
        fonts_dir = FontManager.get_fonts_dir(wow_path, version_subfolder)

        if not fonts_dir.is_dir():
            return True, "No Fonts folder found — defaults already active."

        removed = []
        all_targets = []
        for slot in FONT_SLOTS.values():
            all_targets.append(slot["target"])
            all_targets.append(slot["cyr_target"])

        for target in all_targets:
            target_path = fonts_dir / target
            if target_path.exists():
                try:
                    target_path.unlink()
                    removed.append(target)
                except Exception as e:
                    return False, f"Could not remove {target}: {e}"

        if not removed:
            return True, "No custom fonts found — defaults already active."

        return True, f"Removed {len(removed)} custom font file(s). Defaults restored."

    @staticmethod
    def get_existing_replacements(wow_path: str, version_subfolder: str) -> dict[str, bool]:
        """Check which font slots already have replacements installed."""
        fonts_dir = FontManager.get_fonts_dir(wow_path, version_subfolder)
        result = {}
        for slot_key, slot in FONT_SLOTS.items():
            target_path = fonts_dir / slot["target"]
            result[slot_key] = target_path.exists()
        return result


# ---------------------------------------------------------------------------
# FontSlotCard — reusable card widget for each font slot
# ---------------------------------------------------------------------------

class FontSlotCard(ctk.CTkFrame):
    """A card representing one of WoW's four font slots."""

    def __init__(self, master, slot_key: str, slot_info: dict, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs,
        )

        self.slot_key = slot_key
        self.slot_info = slot_info
        self.source_path: str | None = None
        self._preview_window = None

        # --- Header row ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(16, 0))

        # Accent bar
        accent_bar = ctk.CTkFrame(
            header_frame,
            fg_color=COLORS["accent_gold"],
            width=4,
            height=40,
            corner_radius=2,
        )
        accent_bar.pack(side="left", padx=(0, 12))
        accent_bar.pack_propagate(False)

        title_block = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_block.pack(side="left", fill="x", expand=True)

        self.title_label = ctk.CTkLabel(
            title_block,
            text=slot_info["display_name"],
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            title_block,
            text=slot_info["subtitle"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["accent_gold_dim"],
            anchor="w",
        )
        self.subtitle_label.pack(anchor="w")

        # --- Description ---
        self.desc_label = ctk.CTkLabel(
            self,
            text=slot_info["description"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"],
            anchor="w",
            wraplength=700,
            justify="left",
        )
        self.desc_label.pack(fill="x", padx=20, pady=(8, 0))

        # --- Status ---
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=20, pady=(10, 0))

        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="\u25cf",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
            width=16,
        )
        self.status_dot.pack(side="left")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="No replacement selected",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        self.status_label.pack(side="left", padx=(4, 0))

        # --- Buttons row ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(12, 16))

        self.font_select = ctk.CTkOptionMenu(
            btn_frame,
            values=[
                "Select font...",
                "[Bundled] Lexend Regular",
                "[Bundled] OpenDyslexic Regular",
                "[Bundled] Atkinson Hyperlegible",
                "[Bundled] Comic Neue",
                "Custom Font... (Browse)"
            ],
            width=230,
            height=32,
            corner_radius=8,
            fg_color=COLORS["accent"],
            button_color=COLORS["accent_hover"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["border"],
            dropdown_text_color=COLORS["text_primary"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._on_font_select,
        )
        self.font_select.pack(side="left", padx=(0, 8))

        self.preview_btn = ctk.CTkButton(
            btn_frame,
            text="Preview",
            width=90,
            height=32,
            corner_radius=8,
            fg_color=COLORS["border"],
            hover_color=COLORS["border_light"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._preview_font,
            state="disabled",
        )
        self.preview_btn.pack(side="left", padx=(0, 8))

        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear",
            width=70,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._clear_font,
            state="disabled",
        )
        self.clear_btn.pack(side="left")

        # --- Target filename badge ---
        target_label = ctk.CTkLabel(
            btn_frame,
            text=f"  {slot_info['target']}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["text_muted"],
            anchor="e",
        )
        target_label.pack(side="right")

    def _on_font_select(self, val: str):
        """Handle font selection from dropdown."""
        if val == "Select font...":
            self._clear_font()
        elif val == "Custom Font... (Browse)":
            self._choose_font()
        elif val in BUNDLED_FONTS:
            filename = BUNDLED_FONTS[val]
            filepath = get_resource_path(os.path.join("fonts", filename))
            if not os.path.isfile(filepath):
                self._show_error(f"Bundled font file {filename} not found.")
                self.font_select.set("Select font...")
                self._clear_font()
                return

            self.source_path = filepath
            self._update_status(val, assigned=True)
            self.preview_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")

    def _choose_font(self):
        """Open file dialog to pick a replacement font."""
        filepath = filedialog.askopenfilename(
            title=f"Choose replacement for {self.slot_info['display_name']}",
            filetypes=[
                ("Font files", "*.ttf *.otf"),
                ("TrueType", "*.ttf"),
                ("OpenType", "*.otf"),
                ("All files", "*.*"),
            ],
        )
        if not filepath:
            # Revert optionmenu to match state
            if self.source_path:
                is_bundled = False
                for name, filename in BUNDLED_FONTS.items():
                    target_path = get_resource_path(os.path.join("fonts", filename))
                    if self.source_path == target_path:
                        self.font_select.set(name)
                        is_bundled = True
                        break
                if not is_bundled:
                    self.font_select.set("Custom Font... (Browse)")
            else:
                self.font_select.set("Select font...")
            return

        valid, msg = FontManager.validate_font_file(filepath)
        if not valid:
            self._show_error(msg)
            self.font_select.set("Select font...")
            self._clear_font()
            return

        self.source_path = filepath
        font_name = os.path.basename(filepath)
        self._update_status(font_name, assigned=True)
        self.font_select.set("Custom Font... (Browse)")
        self.preview_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")

    def _preview_font(self):
        """Show a preview window with sample text in the selected font."""
        if not self.source_path:
            return

        # Close existing preview
        if self._preview_window and self._preview_window.winfo_exists():
            self._preview_window.destroy()

        # Try to register font temporarily
        abs_path = os.path.abspath(self.source_path)
        registered = _register_font_win(abs_path)
        family_name = _get_font_family_name(abs_path) if registered else None

        # Build preview window
        preview = ctk.CTkToplevel(self)
        preview.title(f"Preview — {os.path.basename(self.source_path)}")
        preview.geometry("560x420")
        preview.resizable(False, False)
        preview.configure(fg_color=COLORS["bg_dark"])
        self._preview_window = preview

        # Header
        header = ctk.CTkLabel(
            preview,
            text=f"Previewing: {os.path.basename(self.source_path)}",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["accent_gold"],
        )
        header.pack(pady=(20, 4))

        if family_name:
            family_label = ctk.CTkLabel(
                preview,
                text=f"Font Family: {family_name}",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLORS["text_secondary"],
            )
            family_label.pack(pady=(0, 12))

        # Sample text container
        sample_frame = ctk.CTkFrame(
            preview,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        sample_frame.pack(fill="both", expand=True, padx=24, pady=(4, 20))

        # Determine which font to use for samples
        use_family = family_name if family_name else "Segoe UI"

        samples = [
            ("The quick brown fox jumps over the lazy dog.", 20),
            ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 18),
            ("abcdefghijklmnopqrstuvwxyz", 18),
            ("0123456789 !@#$%^&*()_+-=<>?", 16),
            ("Greetings, Champion of Azeroth!", 22),
            ("Quest Accepted: The Warchief's Command", 16),
            ("[Guild] <Party> {Raid} |cff00ff00 colored|r", 14),
        ]

        for text, size in samples:
            label = ctk.CTkLabel(
                sample_frame,
                text=text,
                font=ctk.CTkFont(family=use_family, size=size),
                text_color=COLORS["text_primary"],
                anchor="w",
            )
            label.pack(fill="x", padx=20, pady=4)

        if not registered:
            note = ctk.CTkLabel(
                preview,
                text="Could not load font for preview. Actual appearance will be visible in-game.",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=COLORS["warning"],
                wraplength=500,
            )
            note.pack(pady=(0, 12))

        # Cleanup on close
        def _on_close():
            if registered:
                _unregister_font_win(abs_path)
            preview.destroy()

        preview.protocol("WM_DELETE_WINDOW", _on_close)

    def _clear_font(self):
        """Remove the assigned font from this slot."""
        self.source_path = None
        self._update_status("No replacement selected", assigned=False)
        self.font_select.set("Select font...")
        self.preview_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")

    def _update_status(self, text: str, assigned: bool):
        """Update the status display."""
        if assigned:
            self.status_dot.configure(text_color=COLORS["success"])
            self.status_label.configure(
                text=text,
                text_color=COLORS["success"],
            )
        else:
            self.status_dot.configure(text_color=COLORS["text_muted"])
            self.status_label.configure(
                text=text,
                text_color=COLORS["text_muted"],
            )

    def _show_error(self, message: str):
        """Show an error popup."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Invalid Font File")
        dialog.geometry("400x160")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLORS["bg_dark"])
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Invalid Font File",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["error"],
        ).pack(pady=(24, 8))

        ctk.CTkLabel(
            dialog,
            text=message,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"],
            wraplength=360,
        ).pack(pady=(0, 16))

        ctk.CTkButton(
            dialog,
            text="OK",
            width=80,
            height=32,
            corner_radius=8,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=dialog.destroy,
        ).pack()


# ---------------------------------------------------------------------------
# Main Application Window
# ---------------------------------------------------------------------------

class WoWFontReplacer(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title(APP_TITLE)
        self.geometry(f"{APP_SIZE[0]}x{APP_SIZE[1]}")
        self.minsize(750, 700)
        self.configure(fg_color=COLORS["bg_dark"])

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Try to set window icon (optional)
        try:
            if sys.platform == "win32":
                self.iconbitmap(default="")
        except Exception:
            pass

        self.font_cards: dict[str, FontSlotCard] = {}
        self._build_ui()
        
        # Load saved configuration or auto-detect
        self._load_config()
        if not self.path_entry.get().strip():
            self._auto_detect_path()
        else:
            self._on_version_change()

        # Handle window close event to save settings
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)


    def _build_ui(self):
        """Construct the full UI layout."""

        # ===================== SCROLLABLE CONTAINER =====================
        self.main_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["border_light"],
        )
        self.main_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        container = self.main_scroll

        # ===================== HEADER =====================
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", padx=28, pady=(24, 0))

        # Title with decorative element
        title_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_row.pack(fill="x")

        sword_label = ctk.CTkLabel(
            title_row,
            text="\u2694",
            font=ctk.CTkFont(size=28),
            text_color=COLORS["accent_gold"],
        )
        sword_label.pack(side="left", padx=(0, 10))

        title_label = ctk.CTkLabel(
            title_row,
            text="WoW Font Replacer",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        title_label.pack(side="left")

        version_label = ctk.CTkLabel(
            title_row,
            text="v1.0",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_muted"],
        )
        version_label.pack(side="left", padx=(8, 0), pady=(8, 0))

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Replace default fonts for better readability or a custom look",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        # Thin divider
        divider = ctk.CTkFrame(container, fg_color=COLORS["border"], height=1)
        divider.pack(fill="x", padx=28, pady=(16, 0))

        # ===================== PATH SECTION =====================
        path_section = ctk.CTkFrame(container, fg_color="transparent")
        path_section.pack(fill="x", padx=28, pady=(20, 0))

        path_label = ctk.CTkLabel(
            path_section,
            text="WoW Installation Path",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        path_label.pack(anchor="w", pady=(0, 6))

        path_row = ctk.CTkFrame(path_section, fg_color="transparent")
        path_row.pack(fill="x")

        self.path_entry = ctk.CTkEntry(
            path_row,
            placeholder_text="Browse to your World of Warcraft folder...",
            height=38,
            corner_radius=8,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(
            path_row,
            text="Browse",
            width=90,
            height=38,
            corner_radius=8,
            fg_color=COLORS["border"],
            hover_color=COLORS["border_light"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=self._browse_path,
        )
        browse_btn.pack(side="right")

        # ===================== VERSION SELECTOR =====================
        version_section = ctk.CTkFrame(container, fg_color="transparent")
        version_section.pack(fill="x", padx=28, pady=(16, 0))

        version_label = ctk.CTkLabel(
            version_section,
            text="Game Version",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        version_label.pack(anchor="w", pady=(0, 8))

        version_row = ctk.CTkFrame(version_section, fg_color="transparent")
        version_row.pack(anchor="w")

        self.version_var = ctk.StringVar(value="Retail")

        for version_name in GAME_VERSIONS:
            rb = ctk.CTkRadioButton(
                version_row,
                text=version_name,
                variable=self.version_var,
                value=version_name,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=COLORS["text_primary"],
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                border_color=COLORS["border_light"],
                command=self._on_version_change,
            )
            rb.pack(side="left", padx=(0, 24))

        # Version status
        self.version_status = ctk.CTkLabel(
            version_section,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        self.version_status.pack(anchor="w", pady=(6, 0))

        # Divider
        divider2 = ctk.CTkFrame(container, fg_color=COLORS["border"], height=1)
        divider2.pack(fill="x", padx=28, pady=(20, 0))

        # ===================== FONT SECTION HEADER =====================
        fonts_header = ctk.CTkFrame(container, fg_color="transparent")
        fonts_header.pack(fill="x", padx=28, pady=(20, 4))

        ctk.CTkLabel(
            fonts_header,
            text="Font Replacements",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        ).pack(side="left")

        # "Apply same font to all" button
        self.apply_all_btn = ctk.CTkButton(
            fonts_header,
            text="Apply One Font to All",
            width=160,
            height=30,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._apply_one_to_all,
        )
        self.apply_all_btn.pack(side="right")

        # ===================== FONT SLOT CARDS =====================
        for slot_key, slot_info in FONT_SLOTS.items():
            card = FontSlotCard(container, slot_key, slot_info)
            card.pack(fill="x", padx=28, pady=(10, 0))
            self.font_cards[slot_key] = card

        # ===================== OPTIONS =====================
        options_frame = ctk.CTkFrame(container, fg_color="transparent")
        options_frame.pack(fill="x", padx=28, pady=(20, 0))

        self.cyrillic_var = ctk.BooleanVar(value=False)
        cyrillic_cb = ctk.CTkCheckBox(
            options_frame,
            text="Also create Cyrillic (_CYR) alphabet variants",
            variable=self.cyrillic_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_primary"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border_light"],
            checkmark_color=COLORS["text_primary"],
        )
        cyrillic_cb.pack(anchor="w")

        cyrillic_note = ctk.CTkLabel(
            options_frame,
            text="Enable this if you play with Cyrillic or Greek alphabets",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        cyrillic_note.pack(anchor="w", padx=(28, 0), pady=(2, 0))

        # ===================== ACTION BUTTONS =====================
        action_frame = ctk.CTkFrame(container, fg_color="transparent")
        action_frame.pack(fill="x", padx=28, pady=(24, 0))

        self.apply_btn = ctk.CTkButton(
            action_frame,
            text="Apply Fonts",
            width=180,
            height=44,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            command=self._apply_fonts,
        )
        self.apply_btn.pack(side="left", padx=(0, 12))

        self.restore_btn = ctk.CTkButton(
            action_frame,
            text="Restore Defaults",
            width=160,
            height=44,
            corner_radius=10,
            fg_color="transparent",
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["border_light"],
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            command=self._restore_defaults,
        )
        self.restore_btn.pack(side="left")

        # ===================== STATUS BAR =====================
        status_frame = ctk.CTkFrame(
            container,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        status_frame.pack(fill="x", padx=28, pady=(20, 28))

        self.status_icon = ctk.CTkLabel(
            status_frame,
            text="\u25cf",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
            width=20,
        )
        self.status_icon.pack(side="left", padx=(16, 4), pady=12)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready — select your WoW folder and choose replacement fonts",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.status_label.pack(side="left", fill="x", expand=True, pady=12)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _auto_detect_path(self):
        """Try to auto-detect the WoW installation path."""
        detected = FontManager.detect_wow_path()
        if detected:
            self.path_entry.insert(0, detected)
            self._set_status(f"Auto-detected WoW at: {detected}", "info")
            self._on_version_change()

    def _browse_path(self):
        """Open folder picker for WoW install directory."""
        folder = filedialog.askdirectory(title="Select World of Warcraft installation folder")
        if folder:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)
            self._on_version_change()

    def _on_version_change(self):
        """Update version status when radio button changes."""
        wow_path = self.path_entry.get().strip()
        if not wow_path:
            self.version_status.configure(text="", text_color=COLORS["text_muted"])
            return

        version_subfolder = GAME_VERSIONS[self.version_var.get()]
        valid, msg = FontManager.validate_wow_path(wow_path, version_subfolder)

        if valid:
            # Check existing replacements
            existing = FontManager.get_existing_replacements(wow_path, version_subfolder)
            count = sum(1 for v in existing.values() if v)
            if count > 0:
                self.version_status.configure(
                    text=f"Found {count} existing font replacement(s) installed",
                    text_color=COLORS["accent_gold"],
                )
            else:
                self.version_status.configure(
                    text=f"Path valid — {version_subfolder} folder found",
                    text_color=COLORS["success"],
                )
        else:
            self.version_status.configure(
                text=msg,
                text_color=COLORS["error"],
            )

    def _apply_one_to_all(self):
        """Show a dialog to apply one font to all slots."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Apply One Font to All")
        dialog.geometry("380x200")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLORS["bg_dark"])
        dialog.grab_set()
        dialog.transient(self)

        ctk.CTkLabel(
            dialog,
            text="Apply One Font to All Slots",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            dialog,
            text="Select a font to assign to Friz, Morpheus, Arial, and Skurri:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"],
        ).pack(pady=(0, 16))

        # Dropdown
        selected_font = ctk.StringVar(value="Select font...")
        font_menu = ctk.CTkOptionMenu(
            dialog,
            variable=selected_font,
            values=[
                "[Bundled] Lexend Regular",
                "[Bundled] OpenDyslexic Regular",
                "[Bundled] Atkinson Hyperlegible",
                "[Bundled] Comic Neue",
                "Custom Font... (Browse)"
            ],
            width=260,
            height=36,
            corner_radius=8,
            fg_color=COLORS["border"],
            button_color=COLORS["border_light"],
            button_hover_color=COLORS["border_light"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["border"],
            dropdown_text_color=COLORS["text_primary"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        font_menu.pack(pady=(0, 20))

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack()

        def _do_apply_all():
            val = selected_font.get()
            dialog.destroy()
            
            if val == "Custom Font... (Browse)":
                filepath = filedialog.askopenfilename(
                    title="Choose one font to apply to all slots",
                    filetypes=[
                        ("Font files", "*.ttf *.otf"),
                        ("TrueType", "*.ttf"),
                        ("OpenType", "*.otf"),
                    ],
                )
                if not filepath:
                    return
                valid, msg = FontManager.validate_font_file(filepath)
                if not valid:
                    self._set_status(f"Invalid font: {msg}", "error")
                    return
                
                # Apply custom
                for card in self.font_cards.values():
                    card.source_path = filepath
                    card._update_status(os.path.basename(filepath), assigned=True)
                    card.font_select.set("Custom Font... (Browse)")
                    card.preview_btn.configure(state="normal")
                    card.clear_btn.configure(state="normal")
                self._set_status(f"Applied {os.path.basename(filepath)} to all slots", "success")
            elif val in BUNDLED_FONTS:
                filename = BUNDLED_FONTS[val]
                filepath = get_resource_path(os.path.join("fonts", filename))
                if not os.path.isfile(filepath):
                    self._set_status(f"Bundled font {filename} not found.", "error")
                    return
                
                # Apply bundled
                for card in self.font_cards.values():
                    card.source_path = filepath
                    card._update_status(val, assigned=True)
                    card.font_select.set(val)
                    card.preview_btn.configure(state="normal")
                    card.clear_btn.configure(state="normal")
                self._set_status(f"Applied {val} to all slots", "success")

        ctk.CTkButton(
            btn_row,
            text="Apply All",
            width=100,
            height=34,
            corner_radius=8,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=_do_apply_all,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=80,
            height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=dialog.destroy,
        ).pack(side="left")

    def _apply_fonts(self):
        """Copy and rename selected fonts into the WoW Fonts folder."""
        wow_path = self.path_entry.get().strip()
        if not wow_path:
            self._set_status("Please select your WoW installation folder first", "error")
            return

        version_subfolder = GAME_VERSIONS[self.version_var.get()]
        valid, msg = FontManager.validate_wow_path(wow_path, version_subfolder)
        if not valid:
            self._set_status(msg, "error")
            return

        # Gather assignments
        assignments = {}
        for slot_key, card in self.font_cards.items():
            assignments[slot_key] = card.source_path

        if all(v is None for v in assignments.values()):
            self._set_status("No fonts selected — choose at least one replacement font", "warning")
            return

        include_cyr = self.cyrillic_var.get()
        success, msg = FontManager.apply_fonts(wow_path, version_subfolder, assignments, include_cyr)

        if success:
            self._set_status(msg, "success")
        else:
            self._set_status(msg, "error")

        self._on_version_change()

    def _restore_defaults(self):
        """Remove all custom fonts from the Fonts folder."""
        wow_path = self.path_entry.get().strip()
        if not wow_path:
            self._set_status("Please select your WoW installation folder first", "error")
            return

        version_subfolder = GAME_VERSIONS[self.version_var.get()]

        # Confirmation dialog
        confirm = ctk.CTkToplevel(self)
        confirm.title("Confirm Restore")
        confirm.geometry("440x180")
        confirm.resizable(False, False)
        confirm.configure(fg_color=COLORS["bg_dark"])
        confirm.grab_set()

        # Center on parent
        confirm.transient(self)

        ctk.CTkLabel(
            confirm,
            text="Restore Default Fonts?",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=(28, 8))

        ctk.CTkLabel(
            confirm,
            text="This will remove all custom font files from your\nWoW Fonts folder. The game will use its defaults.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"],
            justify="center",
        ).pack(pady=(0, 20))

        btn_row = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_row.pack()

        def _do_restore():
            confirm.destroy()
            success, msg = FontManager.restore_defaults(wow_path, version_subfolder)
            if success:
                self._set_status(msg, "success")
                # Clear all card states
                for card in self.font_cards.values():
                    card._clear_font()
            else:
                self._set_status(msg, "error")
            self._on_version_change()

        ctk.CTkButton(
            btn_row,
            text="Restore Defaults",
            width=140,
            height=36,
            corner_radius=8,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=_do_restore,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=90,
            height=36,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=confirm.destroy,
        ).pack(side="left")

    def _set_status(self, message: str, level: str = "info"):
        """Update the status bar."""
        color_map = {
            "info": COLORS["text_secondary"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["error"],
        }
        dot_color = color_map.get(level, COLORS["text_secondary"])

        # Truncate long messages for the status bar
        display = message.split("\n")[0]
        if len(display) > 100:
            display = display[:97] + "..."

        self.status_icon.configure(text_color=dot_color)
        self.status_label.configure(text=display, text_color=dot_color)

    def _load_config(self):
        """Load settings and previous font assignments from config.json."""
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # Restore path
                wow_path = config.get("wow_path", "")
                if wow_path:
                    self.path_entry.delete(0, "end")
                    self.path_entry.insert(0, wow_path)

                # Restore version
                game_version = config.get("game_version", "Retail")
                if game_version in GAME_VERSIONS:
                    self.version_var.set(game_version)

                # Restore cyrillic option
                include_cyrillic = config.get("include_cyrillic", False)
                self.cyrillic_var.set(include_cyrillic)

                # Restore font assignments
                assignments = config.get("assignments", {})
                for slot_key, filepath in assignments.items():
                    if slot_key in self.font_cards and filepath:
                        is_bundled = False
                        for name, filename in BUNDLED_FONTS.items():
                            bundled_path = get_resource_path(os.path.join("fonts", filename))
                            if os.path.abspath(filepath) == os.path.abspath(bundled_path):
                                if os.path.isfile(bundled_path):
                                    self.font_cards[slot_key].source_path = bundled_path
                                    self.font_cards[slot_key]._update_status(name, assigned=True)
                                    self.font_cards[slot_key].font_select.set(name)
                                    self.font_cards[slot_key].preview_btn.configure(state="normal")
                                    self.font_cards[slot_key].clear_btn.configure(state="normal")
                                    is_bundled = True
                                    break
                        if not is_bundled and os.path.isfile(filepath):
                            self.font_cards[slot_key].source_path = filepath
                            self.font_cards[slot_key]._update_status(os.path.basename(filepath), assigned=True)
                            self.font_cards[slot_key].font_select.set("Custom Font... (Browse)")
                            self.font_cards[slot_key].preview_btn.configure(state="normal")
                            self.font_cards[slot_key].clear_btn.configure(state="normal")
            except Exception as e:
                print(f"Failed to load config: {e}")

    def _save_config(self):
        """Save settings and current font assignments to config.json."""
        config_path = get_config_path()
        try:
            assignments = {}
            for slot_key, card in self.font_cards.items():
                assignments[slot_key] = card.source_path

            config = {
                "wow_path": self.path_entry.get().strip(),
                "game_version": self.version_var.get(),
                "include_cyrillic": self.cyrillic_var.get(),
                "assignments": assignments
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def _on_window_close(self):
        """Handle saving config before exiting."""
        self._save_config()
        self.destroy()



# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = WoWFontReplacer()
    app.mainloop()


if __name__ == "__main__":
    main()
