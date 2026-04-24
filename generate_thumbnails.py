#!/usr/bin/env python3
"""Generate thumbnails for map editor assets."""
import os
from PIL import Image

ASSETS_DIR = "/opt/crossriver/assets"
THUMB_DIR = "/opt/crossriver/assets/thumbnails"
THUMB_SIZE = 64

created = 0
skipped = 0

for root, dirs, files in os.walk(ASSETS_DIR):
    if "thumbnails" in root:
        continue
    for f in sorted(files):
        if not f.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        src = os.path.join(root, f)
        rel = os.path.relpath(src, ASSETS_DIR)
        dst = os.path.join(THUMB_DIR, rel)
        dst_dir = os.path.dirname(dst)

        if os.path.exists(dst):
            skipped += 1
            continue

        os.makedirs(dst_dir, exist_ok=True)
        try:
            img = Image.open(src)
            img.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
            img.save(dst, "PNG", optimize=True)
            created += 1
        except Exception as e:
            print(f"  ERROR {rel}: {e}")

print(f"Created {created} thumbnails, skipped {skipped} existing")

import subprocess
orig = subprocess.run(["du", "-sh", ASSETS_DIR + "/images"], capture_output=True, text=True).stdout.strip()
thumb = subprocess.run(["du", "-sh", THUMB_DIR], capture_output=True, text=True).stdout.strip()
print(f"Original: {orig}")
print(f"Thumbnails: {thumb}")
