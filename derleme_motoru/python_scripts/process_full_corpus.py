import os
import re
import json
import sys

RAW_DIR = "raw"
PROCESSED_DIR = "processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

# 4 Hak Mezhebin Eksiksiz Külliyat Haritasi
CORPUS_MAP = {
    "hanefi": [
        {"eser": "el_Mabsut", "dosya": "hanefi_mabsut_raw.txt"},
        {"eser": "Bedaiu_s_Sanai", "dosya": "hanefi_corpus_raw.txt"},
        {"eser": "Reddul_Muhtar", "dosya": "hanefi_radd_muhtar_raw.txt"}
    ],
    "safii": [
        {"eser": "el_Umm", "dosya": "safii_umm_raw.txt"},
        {"eser": "el_Mecmu", "dosya": "safii_majmu_raw.txt"},
        {"eser": "Minhacu_t_Talibin", "dosya": "safii_corpus_raw.txt"},
        {"eser": "Nihayetul_Muhtac", "dosya": "safii_nihayat_raw.txt"}
    ],
    "maliki": [
        {"eser": "el_Muvatta", "dosya": "maliki_muwatta_raw.txt"},
        {"eser": "el_Mudawwana", "dosya": "maliki_mudawwana_raw.txt"},
        {"eser": "el_Kafi", "dosya": "maliki_corpus_raw.txt"},
        {"eser": "Mawahibul_Jalil", "dosya": "maliki_mawahib_raw.txt"}
    ],
    "hanbeli": [
        {"eser": "el_Mugni", "dosya": "hanbeli_corpus_raw.txt"},
        {"eser": "el_Insaf", "dosya": "hanbeli_insaf_raw.txt"},
        {"eser": "Kassafu_l_Kina", "dosya": "hanbeli_kashshaf_raw.txt"}
    ]
}

RE_PAGE = re.compile(r"PageV(\d+)P(\d+)")
RE_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]")
RE_INLINE_KITAB = re.compile(r"(?:=\s*(كتاب[^\=\n]+)\s*=|#\s*(كتاب[^\$\n]+)\s*\$)")
RE_INLINE_BAB = re.compile(r"&\s*(باب[^\&\n]+)\s*&")
RE_TRANSITION = re.compile(r"\s+(?=(?:مسألة|فصل|فرع|وقال|وروي|ولنا|واحتج|ودليلنا|والأصل|روى|أما\s+)\b)")

def normalize_arabic(text):
    text = RE_TASHKEEL.sub("", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    return text

def parse_single_book(mezhep_name, eser_name, filename, global_counter):
    filepath = os.path.join(RAW_DIR, filename)
    if not os.path.exists(filepath):
        print(f"[-] UYARI: {filepath} bulunamadi, atlaniyor.")
        return [], global_counter

    chunks = []
    current_vol = "01"
    current_page = "001"
    current_kitab = "Giris"
    current_bab = "Genel"
    current_fasl = ""
    buffer = []

    def build_node(text_content):
        nonlocal global_counter
        node = {
            "node_id": f"{mezhep_name.upper()[:3]}_{global_counter:06d}",
            "mezhep": mezhep_name.capitalize(),
            "eser": eser_name,
            "cilt": current_vol,
            "sayfa": current_page,
            "kitab": current_kitab,
            "bab": current_bab,
            "fasl": current_fasl,
            "metin_orijinal": text_content,
            "metin_arama": normalize_arabic(text_content)
        }
        global_counter += 1
        return node

    def flush():
        nonlocal buffer
        raw_text = " ".join(" ".join(buffer).split()).strip()
        buffer = []
        if len(raw_text) < 40:
            return

        segments = RE_TRANSITION.split(raw_text) if len(raw_text) > 1200 else [raw_text]
        current_block = ""

        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue

            if len(seg) > 1400:
                words = seg.split()
                sub_word_block = []
                sub_len = 0
                for w in words:
                    sub_word_block.append(w)
                    sub_len += len(w) + 1
                    if sub_len >= 1100:
                        part = " ".join(sub_word_block).strip()
                        if len(part) >= 40:
                            chunks.append(build_node(part))
                        sub_word_block = []
                        sub_len = 0
                if sub_word_block:
                    remaining = " ".join(sub_word_block).strip()
                    if len(remaining) >= 40:
                        chunks.append(build_node(remaining))
                continue

            if len(current_block) + len(seg) < 1300:
                current_block += (" " if current_block else "") + seg
            else:
                if len(current_block) >= 40:
                    chunks.append(build_node(current_block))
                current_block = seg

        if len(current_block) >= 40:
            chunks.append(build_node(current_block))

    in_meta = True
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()

            if in_meta:
                if "#META#Header#End#" in line_str:
                    in_meta = False
                continue

            if not line_str:
                continue

            pm = RE_PAGE.search(line_str)
            if pm:
                current_vol = pm.group(1)
                current_page = pm.group(2)
                line_str = RE_PAGE.sub("", line_str).strip()

            km = RE_INLINE_KITAB.search(line_str)
            if km:
                flush()
                current_kitab = (km.group(1) or km.group(2)).strip()
                current_bab = "Genel"
                current_fasl = ""
                line_str = RE_INLINE_KITAB.sub("", line_str).strip()

            bm = RE_INLINE_BAB.search(line_str)
            if bm:
                flush()
                current_bab = bm.group(1).strip()
                current_fasl = ""
                line_str = RE_INLINE_BAB.sub("", line_str).strip()

            clean_hdr = re.sub(r"^(?:#+|\~\~+)\s*(?:\|+)?\s*", "", line_str).strip()
            clean_hdr = re.sub(r"ms\d+", "", clean_hdr).strip()

            is_header_line = False
            if len(clean_hdr) > 0 and len(clean_hdr) < 140:
                if clean_hdr.startswith("كتاب"):
                    flush()
                    current_kitab = clean_hdr
                    current_bab = "Genel"
                    current_fasl = ""
                    is_header_line = True
                elif clean_hdr.startswith("باب"):
                    flush()
                    current_bab = clean_hdr
                    current_fasl = ""
                    is_header_line = True
                elif clean_hdr.startswith(("فصل", "مبحث", "مسألة", "فرع")):
                    flush()
                    current_fasl = clean_hdr
                    is_header_line = True

            if is_header_line:
                continue

            body_line = re.sub(r"^(?:#+|\~\~+)\s*", "", line_str).strip()
            body_line = re.sub(r"ms\d+", "", body_line).strip()
            if body_line:
                buffer.append(body_line)

    flush()
    return chunks, global_counter

print("=" * 75)
print("[*] 4 HAK MEZHEBIN EKSIKSIZ KULLIYAT PARSE ISLEMI BASLATILDI")
print("=" * 75)

for mezhep, books in CORPUS_MAP.items():
    all_mezhep_nodes = []
    counter = 1
    print(f"\n[*] {mezhep.upper()} kitaplari birlestiriliyor:")
    for b in books:
        print(f"    - {b['eser']:<20} ({b['dosya']})...")
        nodes, counter = parse_single_book(mezhep, b["eser"], b["dosya"], counter)
        all_mezhep_nodes.extend(nodes)
        print(f"      -> {len(nodes):<6} anlamsal dugum cikarildi.")

    out_file = os.path.join(PROCESSED_DIR, f"{mezhep}_nodes.json")
    with open(out_file, "w", encoding="utf-8") as out:
        json.dump(all_mezhep_nodes, out, ensure_ascii=False, indent=2)
    print(f"[+] {mezhep.upper()} BITTI: Toplam {len(all_mezhep_nodes)} dugum -> {out_file}")

print("\n" + "=" * 75)
print("[+] 4 Mezhebin tahrir ve serh metinleri basariyla entegre edildi.")
print("=" * 75)
