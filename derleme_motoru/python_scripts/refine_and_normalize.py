import os
import re
import json
import sys

INPUT_FILE = os.path.join("processed", "bidayat_al_mujtahid_parsed.json")
OUTPUT_FILE = os.path.join("processed", "bidayat_al_mujtahid_refined.json")

if not os.path.exists(INPUT_FILE):
    print(f"[-] HATA: {INPUT_FILE} bulunamadi.", file=sys.stderr)
    sys.exit(1)

# Arapça Normalizasyon Fonksiyonları
RE_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]") # Harekeler ve tatvil (kashida)

def normalize_arabic(text):
    # Harekeleri kaldir
    text = RE_TASHKEEL.sub("", text)
    # Elif/Hemze varyasyonlarini teke indir
    text = re.sub(r"[إأآا]", "ا", text)
    # Te-i Merbuta standardizasyonu
    text = re.sub(r"ة", "ه", text)
    # Ye / Elif-i Maksure standardizasyonu
    text = re.sub(r"ى", "ي", text)
    return text

# Mezhep / Fakih Varlık Tespiti
ENTITIES = {
    "Hanefi": [r"أبو\s+حنيفة", r"أبي\s+حنيفة", r"أصحاب\s+أبي\s+حنيفة", r"محمد\s+بن\s+الحسن", r"أبو\s+يوسف", r"الحنفية"],
    "Maliki": [r"مالك", r"ابن\s+القاسم", r"أشهب", r"المالكية", r"أهل\s+المدينة"],
    "Safii": [r"الشافعي", r"الشافعية", r"أصحاب\s+الشافعي"],
    "Hanbeli": [r"أحمد", r"ابن\s+حنبل", r"الحنابلة"],
    "Zahiri": [r"داود", r"داود\s+الظاهري", r"أهل\s+الظاهر"],
    "Cumhur": [r"الجمهور", r"أكثر\s+العلماء", r"عامة\s+الفقهاء"]
}

RE_SPLIT_MASALA = re.compile(r"(?=#\s*(?:المسألة|فصل|فرع|القول في))")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw_chunks = json.load(f)

refined_nodes = []
counter = 1

for chunk in raw_chunks:
    raw_text = chunk["metin"]
    # Satir ici mes'ele/fasl basliklarina gore alt parcalara bol
    sub_segments = RE_SPLIT_MASALA.split(raw_text)

    for seg in sub_segments:
        clean_seg = seg.strip()
        # Markdown artiklarini temizle
        clean_seg = re.sub(r"^[#|\*\s]+", "", clean_seg).strip()
        clean_seg = re.sub(r"\s*#\s*", " ", clean_seg)

        if len(clean_seg) < 40:
            continue

        # Baslik tespiti (ornek: المسألة التاسعة)
        masala_header = ""
        masala_match = re.match(r"^(المسألة\s+[^\.\:\،\n]+|فصل[^\.\:\،\n]+)", clean_seg)
        if masala_match:
            masala_header = masala_match.group(1).strip()

        # Bahsi gecen mezhepleri tespit et
        detected_entities = []
        for mezhep, patterns in ENTITIES.items():
            for pat in patterns:
                if re.search(pat, clean_seg):
                    detected_entities.append(mezhep)
                    break

        norm_text = normalize_arabic(clean_seg)

        refined_nodes.append({
            "node_id": f"BM_NODE_{counter:05d}",
            "cilt": chunk["cilt"],
            "sayfa": chunk["sayfa"],
            "kitab": chunk["kitab"],
            "bab": chunk["bab"],
            "mesele_baslik": masala_header if masala_header else chunk["fasl_mesele"],
            "metin_orijinal": clean_seg,
            "metin_arama": norm_text,
            "tespit_edilen_mezhepler": detected_entities
        })
        counter += 1

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(refined_nodes, f, ensure_ascii=False, indent=2)

print("=" * 50)
print("DURUM              : REFINEMENT_TAMAMLANDI")
print(f"CIKTI DOSYASI      : {OUTPUT_FILE}")
print(f"ISLENEN DUGUM SAYISI: {len(refined_nodes)}")

if refined_nodes:
    # Birden fazla mezhep gecen ornek bir dugum bul
    multi_madhhab_sample = next((n for n in refined_nodes if len(n["tespit_edilen_mezhepler"]) >= 3), refined_nodes[0])
    print("\nORNEK DUGUM (ANLAMSAL BIRIM):")
    print(f"ID           : {multi_madhhab_sample['node_id']}")
    print(f"Mesele       : {multi_madhhab_sample['mesele_baslik']}")
    print(f"Mezhepler    : {', '.join(multi_madhhab_sample['tespit_edilen_mezhepler'])}")
    print(f"Metin Ozet   : {multi_madhhab_sample['metin_orijinal'][:130]}...")
print("=" * 50)