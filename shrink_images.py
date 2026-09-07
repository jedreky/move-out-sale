#!/usr/bin/env python3
import sys
from pathlib import Path
from PIL import Image

EXTENSIONS = {".jpg", ".jpeg"}
FACTOR = 4

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/processed")

if not folder.is_dir():
    print(f"Error: folder '{folder}' not found")
    sys.exit(1)

files = [f for f in folder.rglob("*") if f.suffix.lower() in EXTENSIONS]

if not files:
    print("No images found.")
    sys.exit(0)

for path in files:
    with Image.open(path) as img:
        new_size = (img.width // FACTOR, img.height // FACTOR)
        resized = img.resize(new_size, Image.LANCZOS)
        resized.save(path)
    print(f"  {path}  {img.width}x{img.height} -> {new_size[0]}x{new_size[1]}")

print(f"\nDone. {len(files)} image(s) resized.")
