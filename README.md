# WoW Font Replacer

WoW Font Replacer is a premium, dark-themed desktop application built using Python and CustomTkinter. It automates the process of swapping World of Warcraft's default fonts with high-legibility, open-source readability fonts or custom fonts of your choice.

This utility supports all versions of WoW (Retail, Classic, Classic Era, and Private / Legacy Servers) on Windows.

---

## Features

- 🔍 **Auto-detect WoW Path:** Scans common Windows installation directories on startup.
- ⚙️ **Private Server / Legacy Support:** Installs fonts directly to your root WoW folder (under a root `/Fonts/` folder) automatically verifying that `wow.exe` or `Wow.exe` is present in the chosen directory.
- 📦 **Pre-packaged Readability Fonts:** Comes with four highly recommended, open-source legibility fonts ready to apply instantly:
  - **Lexend Regular:** Specifically designed to improve reading proficiency and reduce visual stress.
  - **OpenDyslexic Regular:** Designed with heavy-weighted bottoms to assist readers with dyslexia.
  - **Atkinson Hyperlegible:** Designed by the Braille Institute to increase character distinction for low-vision readers.
  - **Comic Neue:** A clean, readable, and elegant alternative to Comic Sans.
- 🎨 **Live Font Preview:** Temporarily registers and renders chosen fonts inside a WoW-themed preview window without installing them system-wide.
- 💾 **Persistent Settings:** Automatically saves and restores your configuration (paths, selections, and versions) to a local `config.json` file.
- 🔠 **Cyrillic Support:** A simple checkbox toggle automatically duplicates and renames font files with `_CYR` extensions for Cyrillic and Greek alphabet users.
- 🔄 **Restore to Defaults:** A single button removes all custom replacements and restores default WoW atmospheric fonts.

---

## File Structure & WoW Naming Rules

WoW expects specific, case-sensitive filenames inside a `Fonts/` folder (located in the game version directory for official WoW, or in the game's root directory for private servers). WoW Font Replacer handles all of this naming and directory management automatically:

- **Friz Quadrata** (General UI, quest text, nameplates, etc.) &rarr; `FRIZQT__.ttf` (2 underscores)
- **Morpheus** (Mail text, books, and quest titles) &rarr; `MORPHEUS.ttf`
- **Arial Narrow** (In-game chat, experience, and money) &rarr; `ARIALN.ttf`
- **Skurri** (Combat damage text) &rarr; `skurri.ttf` (lowercase)

If Cyrillic support is checked, the app also generates matching `_CYR` files:
- `FRIZQT___CYR.ttf` (3 underscores)
- `MORPHEUS_CYR.ttf`
- `ARIALN_CYR.ttf`
- `skurri_CYR.ttf`

---

## Getting Started

### Run in Development

1. **Install Dependencies:**
   Ensure you have Python 3.10+ installed. Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```

2. **Download Font Assets:**
   Run the utility script to download the pre-packaged fonts into a local `fonts/` directory:
   ```bash
   python download_fonts.py
   ```

3. **Run the Application:**
   ```bash
   python main.py
   ```

### Build Standing Standalone Executable (.exe)

You can compile the app into a single, standalone executable that bundles all dependencies and fonts using PyInstaller:

```bash
python build.py
```

Once compilation completes, the packaged executable will be available at:
`dist/WoWFontReplacer.exe`

### Automated Builds & Releases (GitHub Actions)

This repository includes a GitHub Actions CI/CD workflow that builds and releases the standalone executable automatically for free:

1. **How it works:** Whenever you push a git tag matching `v*` (e.g., `v1.0.0`) to GitHub, the workflow automatically runs.
2. **Build Process:** A Windows Runner checkouts the repo, sets up Python, installs dependencies, downloads the required fonts, and compiles the executable.
3. **Release:** A new GitHub Release is created for that tag, and the compiled `WoWFontReplacer.exe` is uploaded directly to the release page.

To push a new release tag:
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## Licensing

- **Lexend:** SIL Open Font License (OFL)
- **OpenDyslexic:** SIL Open Font License (OFL)
- **Atkinson Hyperlegible:** SIL Open Font License (OFL)
- **Comic Neue:** SIL Open Font License (OFL)
- All script code is open for personal use and modification.
