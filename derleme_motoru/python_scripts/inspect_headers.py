import os
import re

RAW_DIR = "raw"
FILES = [
    "hanefi_corpus_raw.txt",
    "safii_corpus_raw.txt",
    "maliki_corpus_raw.txt",
    "hanbeli_corpus_raw.txt"
]

print("=" * 70)
print("[*] HAM DOSYALARDAKI GERCEK BASLIK FORMATLARI")
print("=" * 70)

for fname in FILES:
    fpath = os.path.join(RAW_DIR, fname)
    if not os.path.exists(fpath):
        continue
    
    print(f"\n>>> DOSYA: {fname}")
    matches = []
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            # Header veya etiket iceren satirlari tara
            if any(k in line for k in ["###", "|", "كتاب", "باب", "فصل"]) and len(line.strip()) < 120:
                matches.append((i + 1, line.strip()))
                if len(matches) >= 8:
                    break
    
    for lnum, text in matches:
        print(f"  Satir {lnum:<6}: {text}")

print("=" * 70)