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
RE_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]")
RE_PIPE_HEADER = re.compile(r"^(\|{1,5})\s*(.*)$")
RE_ARABIC_HEADER = re.compile(r"^(كتاب|باب|فصل|فرع|مسألة)\s*(.*)$")

def normalize_arabic(text):
    text = RE_TASHKEEL.sub("", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    return text

def parse_book(mezhep, eser, filename):
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
        raw_content = " ".join(" ".join(buffer).split()).strip()
        buffer = []
        if len(raw_content) < 40:
            return

        # Parça 2200 karakterden uzunsa anlamsal cümle/nokta sınırından alt parçalara böl
        sub_texts = []
        if len(raw_content) > 2200:
            sentences = re.split(r"(\.|\؛|\:|\n)", raw_content)
            temp = ""
            for s in sentences:
                temp += s
                if len(temp) >= 1200:
                    sub_texts.append(temp.strip())
                    temp = ""
            if temp.strip():
                if sub_texts and len(temp.strip()) < 300:
                    sub_texts[-1] += " " + temp.strip()
                else:
                    sub_texts.append(temp.strip())
        else:
            sub_texts = [raw_content]

        for st in sub_texts:
            if len(st) >= 40:
                chunks.append({
                    "node_id": f"{mezhep.upper()[:3]}_{len(chunks)+1:06d}",
                    "mezhep": mezhep,
                    "eser": eser,
                    "cilt": current_vol,
                    "sayfa": current_page,
                    "kitab": current_kitab,
                    "bab": current_bab,
                    "fasl": current_fasl,
                    "metin_orijinal": st,
                    "metin_arama": normalize_arabic(st)
                })

    in_meta = True
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_raw = line.strip()

            if in_meta:
                if "#META#Header#End#" in line_raw:
                    in_meta = False
                continue

            if not line_raw:
                continue

            # Sayfa tespiti
            pm = RE_PAGE.search(line_raw)
            if pm:
                current_vol = pm.group(1)
                current_page = pm.group(2)
                line_raw = RE_PAGE.sub("", line_raw).strip()

            # Format işaretlerini temizle
            clean_line = re.sub(r"^~~+", "", line_raw).strip()
            clean_line = re.sub(r"^#+\s*", "", clean_line).strip()
            clean_line = re.sub(r"ms\d+", "", clean_line).strip()

            if not clean_line:
                continue

            # 1. Pipe başlık formatı (| Kitab, || Bab, ||| Fasl)
            pipe_match = RE_PIPE_HEADER.match(clean_line)
            if pipe_match:
                flush()
                bars = pipe_match.group(1)
                title = pipe_match.group(2).strip()
                title = re.sub(r"[#|\*_]", "", title).strip()
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

            # 2. Doğrudan Arapça başlık tespiti
            ar_match = RE_ARABIC_HEADER.match(clean_line)
            if ar_match and len(clean_line) < 120:
                flush()
                h_type = ar_match.group(1)
                if h_type == "كتاب":
                    current_kitab = clean_line
                    current_bab = ""
                    current_fasl = ""
                elif h_type == "باب":
                    current_bab = clean_line
                    current_fasl = ""
                else:
                    current_fasl = clean_line
                continue

            buffer.append(clean_line)

    flush()
    return chunks

for t in TARGETS:
    nodes = parse_book(t["mezhep"], t["eser"], t["dosya"])
    out_path = os.path.join(PROCESSED_DIR, f"{t['mezhep'].lower()}_nodes.json")
    with open(out_path, "w", encoding="utf-8") as out:
        json.dump(nodes, out, ensure_ascii=False, indent=2)

print("[+] Tum mezhep metinleri yapisal baslik ve dengeli dugum boyutuyla yeniden islendi.")