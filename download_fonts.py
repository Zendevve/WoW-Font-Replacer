"""
Download recommended readability fonts for the WoW Font Replacer.
Downloads fonts into the local 'fonts/' directory.
"""

import os
import requests

FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# Clean URLs for downloading fonts
FONT_URLS = {
    "Lexend-Regular.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/lexend/static/Lexend-Regular.ttf",
        "https://github.com/googlefonts/lexend/raw/main/fonts/lexend/ttf/Lexend-Regular.ttf",
        "https://github.com/google/fonts/raw/main/ofl/lexend/Lexend-Regular.ttf"
    ],
    "OpenDyslexic-Regular.otf": [
        "https://github.com/antijingoist/open-dyslexic/raw/master/otf/OpenDyslexic-Regular.otf",
        "https://github.com/antijingoist/opendyslexic/raw/master/compiled/OpenDyslexic-Regular.otf"
    ],
    "AtkinsonHyperlegible-Regular.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Regular.ttf"
    ],
    "ComicNeue-Regular.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/comicneue/ComicNeue-Regular.ttf"
    ]
}

def download_file(urls, filename):
    filepath = os.path.join(FONTS_DIR, filename)
    
    # Check if already exists and is non-empty
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        print(f"[OK] {filename} already exists.")
        return True

    print(f"Downloading {filename}...")
    for url in urls:
        try:
            response = requests.get(url, stream=True, timeout=15)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"[OK] Successfully downloaded {filename} from {url}")
                return True
            else:
                print(f"[ERROR] Failed {url} (status code: {response.status_code})")
        except Exception as e:
            print(f"[ERROR] Error downloading from {url}: {e}")
            
    print(f"[FAIL] Failed to download {filename} from all sources.")
    return False

def main():
    os.makedirs(FONTS_DIR, exist_ok=True)
    success = True
    for filename, urls in FONT_URLS.items():
        if not download_file(urls, filename):
            success = False
            
    if success:
        print("\nAll pre-packaged fonts are ready!")
    else:
        print("\nSome fonts failed to download. Please check your internet connection.")
        exit(1)

if __name__ == "__main__":
    main()
