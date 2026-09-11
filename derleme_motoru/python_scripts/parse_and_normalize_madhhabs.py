import os
import re
import json
import sys

RAW_DIR = "raw"
PROCESSED_DIR = "processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

CORPUS_FILES = [
    {"mezhep": "Hanefi", "eser": "Bedaiu_s_Sanai", "dosya": "hanefi_corpus_raw.txt"},
    {"mezhep": "Safii", "eser": "Minhacu_t_Talibin", "dosya": "safii_corpus_raw.txt"},
    {"mezhep": "Maliki", "eser": "el_Kafi", "dosya": "maliki_corpus_raw.txt"},
    {"mezhep": "Hanbeli", "eser": "el_Mugni", "dosya": "hanbeli_corpus_raw.txt"}
]

RE_PAGE = re.compile(r"PageV(\d+)P(\d+)")
RE_HEADER = re.compile(r"^(#{1,6})\s*(\|{1,5})\s*(.*)$")
RE_EDITORIAL = re.compile(r"~~.*|ms\d+|#META#.*")
RE_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]")

def normalize_arabic(text):
    text = RE_TASHKEEL.sub("", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    return text

def parse_corpus_file(mezhep, eser, filename):
    file_path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(file_path):
        print(f"[-] HATA: {file_path} bulunamadi.")
        return []

    chunks = []
    current_vol = "01"
    current_page = "001"
    current_hierarchy = {"level_1": "Giris", "level_2": "", "level_3": ""}
    buffer_text = []

    def flush_chunk():
        nonlocal buffer_text
        clean = " ".join(" ".join(buffer_text).split()).strip()
        clean = re.sub(r"^[#|\*\s]+", "", clean).strip()
        if clean and len(clean) > 40:
            chunks.append({
                "node_id": f"{mezhep.upper()[:3]}_{len(chunks)+1:06d}",
                "mezhep": mezhep,
                "eser": eser,
                "cilt": current_vol,
                "sayfa": current_page,
                "kitab": current_hierarchy["level_1"],
                "bab": current_hierarchy["level_2"],
                "fasl": current_hierarchy["level_3"],
                "metin_orijinal": clean,
                "metin_arama": normalize_arabic(clean)
            })
        buffer_text = []

    in_header = True
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()

            if in_header:
                if "#META#Header#End#" in line_str:
                    in_header = False
                continue

            if not line_str:
                continue

            page_match = RE_PAGE.search(line_str)
            if page_match:
                flush_chunk()
                current_vol = page_match.group(1)
                current_page = page_match.group(2)
                line_str = RE_PAGE.sub("", line_str).strip()

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

            line_clean = RE_EDITORIAL.sub("", line_str).strip()
            if line_clean:
                buffer_text.append(line_clean)

    flush_chunk()
    return chunks

print("=" * 60)
print("[*] 4 MEZHEP METINLERI AYRISTIRILIYOR VE ISLENIYOR...")
print("=" * 60)

stats = []

for item in CORPUS_FILES:
    m = item["mezhep"]
    e = item["eser"]
    f = item["dosya"]
    print(f"[*] Isleniyor: {m} - {e}...")
    
    nodes = parse_corpus_file(m, e, f)
    out_file = os.path.join(PROCESSED_DIR, f"{m.lower()}_nodes.json")
    
    with open(out_file, "w", encoding="utf-8") as out:
        json.dump(nodes, out, ensure_ascii=False, indent=2)
    
    stats.append((m, e, len(nodes), out_file))

print("\n" + "=" * 60)
print("ISLEME RAPORU:")
total_nodes = 0
for m, e, count, path in stats:
    total_nodes += count
    print(f"  {m:<10} | {e:<20} | Dugum Sayisi: {count:<6} -> {path}")
print(f"\nTOPLAM ISLENEN METIN DUGUMU: {total_nodes}")
print("=" * 60)