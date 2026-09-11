import os
import re
import json

RAW_DIR = "raw"
PROCESSED_DIR = "processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

TARGETS = [
    {"mezhep": "Hanefi", "eser": "Bedaiu_s_Sanai", "dosya": "hanefi_corpus_raw.txt"},
    {"mezhep": "Safii", "eser": "Minhacu_t_Talibin", "dosya": "safii_corpus_raw.txt"},
    {"mezhep": "Maliki", "eser": "el_Kafi", "dosya": "maliki_corpus_raw.txt"},
    {"mezhep": "Hanbeli", "eser": "el_Mugni", "dosya": "hanbeli_corpus_raw.txt"}
]

RE_PAGE = re.compile(r"PageV(\d+)P(\d+)")
RE_PIPE_HEADER = re.compile(r"^(#{1,6})\s*(\|{1,5})\s*(.*)$")
RE_ARABIC_HEADER = re.compile(r"^(كتاب|باب|فصل|فرع|مسألة)\s+(.*)$")
RE_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]")

def normalize_arabic(text):
    text = RE_TASHKEEL.sub("", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    return text

def parse_fixed(mezhep, eser, filename):
    filepath = os.path.join(RAW_DIR, filename)
    if not os.path.exists(filepath):
        return []

    chunks = []
    current_vol = "01"
    current_page = "001"
    current_kitab = "Giris"
    current_bab = ""
    current_fasl = ""
    buffer = []

    def flush():
        nonlocal buffer
        text = " ".join(" ".join(buffer).split()).strip()
        if len(text) >= 50:
            chunks.append({
                "node_id": f"{mezhep.upper()[:3]}_{len(chunks)+1:06d}",
                "mezhep": mezhep,
                "eser": eser,
                "cilt": current_vol,
                "sayfa": current_page,
                "kitab": current_kitab,
                "bab": current_bab,
                "fasl": current_fasl,
                "metin_orijinal": text,
                "metin_arama": normalize_arabic(text)
            })
        buffer = []

    in_meta = True
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if in_meta:
                if "#META#Header#End#" in line:
                    in_meta = False
                continue

            if not line:
                continue

            # Sayfa tespiti
            pm = RE_PAGE.search(line)
            if pm:
                current_vol = pm.group(1)
                current_page = pm.group(2)
                line = RE_PAGE.sub("", line).strip()

            # OpenITI pipe başlığı (| Kitab, || Bab, ||| Fasl)
            ph = RE_PIPE_HEADER.match(line)
            if ph:
                flush()
                bars = ph.group(2)
                title = re.sub(r"[#|\*_]", "", ph.group(3)).strip()
                if len(bars) == 1:
                    current_kitab = title
                    current_bab = ""
                    current_fasl = ""
                elif len(bars) == 2:
                    current_bab = title
                    current_fasl = ""
                else:
                    current_fasl = title
                continue

            # Klasik Arapça başlık tespiti
            ah = RE_ARABIC_HEADER.match(line)
            if ah:
                flush()
                h_type = ah.group(1)
                h_title = line
                if h_type == "كتاب":
                    current_kitab = h_title
                    current_bab = ""
                    current_fasl = ""
                elif h_type == "باب":
                    current_bab = h_title
                    current_fasl = ""
                else:
                    current_fasl = h_title
                continue

            # mARkdown format imlerini metni yok etmeden temizle
            line = re.sub(r"^~~+", "", line).strip()
            line = re.sub(r"ms\d+", "", line).strip()
            line = re.sub(r"^#+\s*", "", line).strip()

            if line:
                buffer.append(line)

    flush()
    return chunks

for t in TARGETS:
    nodes = parse_fixed(t["mezhep"], t["eser"], t["dosya"])
    out_path = os.path.join(PROCESSED_DIR, f"{t['mezhep'].lower()}_nodes.json")
    with open(out_path, "w", encoding="utf-8") as out:
        json.dump(nodes, out, ensure_ascii=False, indent=2)

print("[+] Parser duzeltildi ve 4 dosya yeniden parse edildi.")