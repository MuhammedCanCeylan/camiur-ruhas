import os
import re
import json
import sys

INPUT_FILE = os.path.join("raw", "bidayat_al_mujtahid_raw.txt")
OUTPUT_FILE = os.path.join("processed", "bidayat_al_mujtahid_parsed.json")

if not os.path.exists(INPUT_FILE):
    print(f"[-] Hata: {INPUT_FILE} bulunamadi.", file=sys.stderr)
    sys.exit(1)

os.makedirs("processed", exist_ok=True)

# Regex kaliplari
RE_PAGE = re.compile(r"PageV(\d+)P(\d+)")
RE_HEADER = re.compile(r"^(#{1,6})\s*(\|{1,5})\s*(.*)$")
RE_EDITORIAL = re.compile(r"~~.*|ms\d+|#META#.*")

metadata = {}
chunks = []

current_vol = "01"
current_page = "001"
current_hierarchy = {
    "level_1": "Giris",
    "level_2": "",
    "level_3": ""
}

buffer_text = []

def flush_chunk():
    global buffer_text
    clean_content = " ".join(" ".join(buffer_text).split()).strip()
    if clean_content and len(clean_content) > 30:
        chunks.append({
            "chunk_id": f"BM_V{current_vol}_P{current_page}_{len(chunks)+1:04d}",
            "cilt": current_vol,
            "sayfa": current_page,
            "kitab": current_hierarchy["level_1"],
            "bab": current_hierarchy["level_2"],
            "fasl_mesele": current_hierarchy["level_3"],
            "metin": clean_content
        })
    buffer_text = []

in_header = True

with open(INPUT_FILE, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line_str = line.strip()

        # OpenITI metadata basligini atla
        if in_header:
            if "#META#Header#End#" in line_str:
                in_header = False
            continue

        if not line_str:
            continue

        # Sayfa / Cilt tespiti
        page_match = RE_PAGE.search(line_str)
        if page_match:
            flush_chunk()
            current_vol = page_match.group(1)
            current_page = page_match.group(2)
            line_str = RE_PAGE.sub("", line_str).strip()

        # OpenITI yapisal baslik tespiti (### |, ### ||, ### |||)
        header_match = RE_HEADER.match(line_str)
        if header_match:
            flush_chunk()
            bars = header_match.group(2)
            title = header_match.group(3).strip()
            title = re.sub(r"[#|\*_]", "", title).strip()

            if len(bars) == 1:
                current_hierarchy["level_1"] = title
                current_hierarchy["level_2"] = ""
                current_hierarchy["level_3"] = ""
            elif len(bars) == 2:
                current_hierarchy["level_2"] = title
                current_hierarchy["level_3"] = ""
            else:
                current_hierarchy["level_3"] = title
            continue

        # Editöryal isaretleri temizle
        line_clean = RE_EDITORIAL.sub("", line_str).strip()
        if line_clean:
            buffer_text.append(line_clean)

# Kalan son parcayi yaz
flush_chunk()

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    json.dump(chunks, out, ensure_ascii=False, indent=2)

print("=" * 50)
print("DURUM           : AYRISTIRMA_BASARILI")
print(f"CIKTI DOSYASI   : {OUTPUT_FILE}")
print(f"TOPLAM CHUNK    : {len(chunks)}")
if chunks:
    sample = chunks[min(10, len(chunks)-1)]
    print("\nORNEK DUGUM (CHUNK):")
    print(f"ID      : {sample['chunk_id']}")
    print(f"Cilt/S. : {sample['cilt']} / {sample['sayfa']}")
    print(f"Kitab   : {sample['kitab']}")
    print(f"Bab     : {sample['bab']}")
    print(f"Fasl    : {sample['fasl_mesele']}")
    print(f"Metin   : {sample['metin'][:120]}...")
print("=" * 50)