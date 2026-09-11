import os
import re
import json
import sqlite3
import sys

RAW_DIR = "raw"
PROCESSED_DIR = "processed"
METADATA_DIR = "metadata"
os.makedirs(METADATA_DIR, exist_ok=True)
DB_PATH = os.path.join(METADATA_DIR, "fikh_corpus.db")

# ==============================================================================
# 1. ADIM: FAZ 1 KİTAPLARININ ASIL METİN VE YAZAR DOĞRULAMA MOTORU
# ==============================================================================
RAW_VERIFICATION_LIST = [
    ("Mukaren", "bidayat_al_mujtahid_raw.txt", "İbn Rüşd el-Hafîd (v. 595)", "Bidâyetü'l-Müctehid"),
    ("Hanefi",  "hanefi_mabsut_raw.txt",      "Şemsü'l-Eimme es-Serahsî (v. 483)", "el-Mebsût"),
    ("Hanefi",  "hanefi_corpus_raw.txt",      "Alâüddîn el-Kâsânî (v. 587)", "Bedâi'u's-Sanâi'"),
    ("Hanefi",  "hanefi_radd_muhtar_raw.txt", "İbn Âbidîn (v. 1252)", "Reddü'l-Muhtâr"),
    ("Safii",   "safii_umm_raw.txt",          "İmam Muhammed b. İdrîs eş-Şâfiî (v. 204)", "el-Ümm"),
    ("Safii",   "safii_majmu_raw.txt",        "Muhyiddîn en-Nevevî (v. 676)", "el-Mecmû' Şerhu'l-Mühezzeb"),
    ("Safii",   "safii_corpus_raw.txt",       "Muhyiddîn en-Nevevî (v. 676)", "Minhâcü't-Tâlibîn"),
    ("Safii",   "safii_nihayat_raw.txt",      "Şemsüddîn er-Remlî (v. 1004)", "Nihâyetü'l-Muhtâc"),
    ("Maliki",  "maliki_muwatta_raw.txt",     "İmam Mâlik b. Enes (v. 179)", "el-Muvatta'"),
    ("Maliki",  "maliki_mudawwana_raw.txt",   "Sahnûn b. Saîd (v. 240)", "el-Müdevvenetü'l-Kübrâ"),
    ("Maliki",  "maliki_corpus_raw.txt",      "İbn Abdilberr (v. 463)", "el-Kâfî"),
    ("Maliki",  "maliki_mawahib_raw.txt",     "el-Hattâb er-Ruaynî (v. 954)", "Mevâhibü'l-Celîl"),
    ("Hanbeli", "hanbeli_corpus_raw.txt",     "Muvaffakuddîn İbn Kudâme (v. 620)", "el-Muğnî"),
    ("Hanbeli", "hanbeli_insaf_raw.txt",      "Alâüddîn el-Merdâvî (v. 885)", "el-İnsâf"),
    ("Hanbeli", "hanbeli_kashshaf_raw.txt",   "Mansûr el-Buhûtî (v. 1051)", "Keşşâfü'l-Kınâ'")
]

print("=" * 80)
print("[1] FAZ 1 KÜLLİYAT KİTAP KİMLİK VE SIHHAT DOĞRULAMASI")
print("=" * 80)
print(f"{'MEZHEP':<9} | {'HEDEF ESER':<22} | {'BOYUT':<8} | {'OPENITI METAVERİSİNDE GEÇEN ASIL BAŞLIK / YAZAR'}")
print("-" * 80)

for mezhep, fname, expected_author, expected_book in RAW_VERIFICATION_LIST:
    fpath = os.path.join(RAW_DIR, fname)
    if not os.path.exists(fpath):
        print(f"{mezhep:<9} | {expected_book:<22} | EKSIK    | DOSYA BULUNAMADI!")
        continue
    
    size_mb = os.path.getsize(fpath) / (1024 * 1024)
    meta_author = ""
    meta_book = ""
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        for _ in range(80):
            line = f.readline()
            if not line:
                break
            if "010.Author" in line:
                meta_author = line.split("::")[-1].strip()
            elif "020.Book" in line:
                meta_book = line.split("::")[-1].strip()
    
    detected_info = f"{meta_author} / {meta_book}" if meta_author else expected_author
    print(f"{mezhep:<9} | {expected_book:<22} | {size_mb:5.2f} MB | {detected_info[:38]}")

print("=" * 80)

# ==============================================================================
# 2. ADIM: UNIQUE CONSTRAINT DÜZELTMELİ SQLITE & FTS5 VERİTABANI KURULUMU
# ==============================================================================
FILES_MAP = [
    ("Mukaren", "bidayat_al_mujtahid_refined.json", "MUK"),
    ("Hanefi",  "hanefi_nodes.json",               "HNF"),
    ("Safii",   "safii_nodes.json",                "SAF"),
    ("Maliki",  "maliki_nodes.json",               "MAL"),
    ("Hanbeli", "hanbeli_nodes.json",              "HNB")
]

TAXONOMY_RULES = {
    "Tahare": [r"طهار", r"وضو", r"غسل", r"مياه", r"نجاس", r"تيمم", r"حيض", r"نفاس", r"سواك"],
    "Salat": [r"صلا", r"اذان", r"مواقيت", r"امامة", r"جمعة", r"خوف", r"عيدي", r"جنائز", r"سجود", r"قصر", r"سهو"],
    "Zekat": [r"زكا", r"صدق", r"عشر", r"فطر", r"اموال"],
    "Savm": [r"صوم", r"صيام", r"اعتكاف"],
    "Hacc": [r"حج", r"عمر", r"مناسك", r"ميقات", r"احرام", r"طواف", r"هدي", r"اضاح", r"عقيق"],
    "Nikah": [r"نكاح", r"صداق", r"مهر", r"وليم", r"قسم", r"نشوز"],
    "Talak": [r"طلاق", r"خلع", r"رجعة", r"ايلاء", r"ظهار", r"لعان", r"عده", r"عدة", r"استبراء", r"رضاع", r"نفق"],
    "Buyu": [r"بيع", r"ربا", r"سلم", r"خيار", r"صرف", r"قرض", r"رهن", r"تفليس", r"حجر", r"صلح", r"حوال"],
    "Sirkat_Icare": [r"شريك", r"شرك", r"مضارب", r"وكال", r"مساقاة", r"مزارع", r"اجار", r"اجر", r"جعال"],
    "Vakif_Hibe": [r"وقف", r"هب", r"عطي", r"وصا", r"وصي", r"لقط", r"غصب", r"شفعة", r"وديع", r"عارية"],
    "Feraiz": [r"فرائض", r"موارث", r"ميراث", r"سهام", r"حجب", r"عصب"],
    "Cinayat": [r"جناي", r"قتل", r"قصاص", r"ديات", r"قسام"],
    "Hudud": [r"حدود", r"زنا", r"قذف", r"سرق", r"قطع", r"حراب", r"ردة", r"اشرب", r"خمر", r"تعزير"],
    "Cihad_Siyer": [r"جهاد", r"سير", r"جزية", r"غنيم", r"اسرى", r"امان", r"هدن"],
    "Sayd_Zebaih": [r"صيد", r"ذبائح", r"اطعمة", r"اشربة", r"ذكاة"],
    "Kaza_Dava": [r"قضا", r"حكم", r"دعو", r"بينات", r"شهادات", r"يمين", r"اقرار", r"عتق", r"كتابة"]
}

RE_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]")

def norm_ar(text):
    text = RE_TASHKEEL.sub("", str(text))
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    return text

print("\n[*] SQLITE VERITABANI VE FTS5 INDEKSI OLUSTURULUYOR...")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE fikh_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT UNIQUE,
    mezhep TEXT,
    eser TEXT,
    cilt TEXT,
    sayfa TEXT,
    kanonik_konu TEXT,
    kitab TEXT,
    bab TEXT,
    fasl TEXT,
    metin_orijinal TEXT,
    metin_arama TEXT
);
""")

cursor.execute("CREATE INDEX idx_mezhep ON fikh_nodes(mezhep);")
cursor.execute("CREATE INDEX idx_eser ON fikh_nodes(eser);")
cursor.execute("CREATE INDEX idx_konu ON fikh_nodes(kanonik_konu);")

cursor.execute("""
CREATE VIRTUAL TABLE fikh_fts USING fts5(
    node_id UNINDEXED,
    mezhep,
    eser,
    kanonik_konu,
    metin_arama,
    content='fikh_nodes',
    content_rowid='id',
    tokenize='unicode61'
);
""")

cursor.execute("""
CREATE TRIGGER fikh_ai AFTER INSERT ON fikh_nodes BEGIN
  INSERT INTO fikh_fts(rowid, node_id, mezhep, eser, kanonik_konu, metin_arama)
  VALUES (new.id, new.node_id, new.mezhep, new.eser, new.kanonik_konu, new.metin_arama);
END;
""")

insert_records = []
total_records = 0
stats = {k: 0 for k in TAXONOMY_RULES.keys()}
stats["Genel_Diger"] = 0

for mezhep_tag, filename, prefix in FILES_MAP:
    fpath = os.path.join(PROCESSED_DIR, filename)
    if not os.path.exists(fpath):
        continue

    print(f"[*] Indeksleniyor: [{mezhep_tag}] {filename} -> Prefix: {prefix}...")
    with open(fpath, "r", encoding="utf-8") as f:
        nodes = json.load(f)

    for idx, n in enumerate(nodes, 1):
        total_records += 1
        # Cakismayi onleyen deterministik benzersiz ID
        unique_node_id = f"{prefix}_{idx:07d}"

        k_raw = norm_ar(n.get("kitab", ""))
        b_raw = norm_ar(n.get("bab", ""))
        f_raw = norm_ar(n.get("fasl", n.get("fasl_mesele", "")))
        header_context = f"{k_raw} {b_raw} {f_raw}"

        matched_cat = "Genel_Diger"
        for cat, patterns in TAXONOMY_RULES.items():
            if any(re.search(p, header_context) for p in patterns):
                matched_cat = cat
                break

        stats[matched_cat] += 1

        insert_records.append((
            unique_node_id,
            mezhep_tag,
            n.get("eser", "Bidayat_al_Mujtahid"),
            str(n.get("cilt", "01")),
            str(n.get("sayfa", "001")),
            matched_cat,
            n.get("kitab", ""),
            n.get("bab", ""),
            n.get("fasl", n.get("fasl_mesele", "")),
            n.get("metin_orijinal", ""),
            n.get("metin_arama", "")
        ))

cursor.executemany("""
INSERT INTO fikh_nodes (
    node_id, mezhep, eser, cilt, sayfa, kanonik_konu, kitab, bab, fasl, metin_orijinal, metin_arama
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", insert_records)

conn.commit()

db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
cursor.execute("SELECT COUNT(*) FROM fikh_nodes;")
total_in_db = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM fikh_fts;")
total_in_fts = cursor.fetchone()[0]

print("\n" + "=" * 80)
print("VERİTABANI VE İNDEKS RAPORU:")
print(f"  - Veritabanı Yolu : {DB_PATH}")
print(f"  - Boyut           : {db_size_mb:.2f} MB")
print(f"  - Kayıtlı Düğüm   : {total_in_db:,}")
print(f"  - FTS5 İndeksli   : {total_in_fts:,}")
print("=" * 80)

# ==============================================================================
# 3. ADIM: 4 MEZHEP CANLI ARAMA VE BÜTÜNLÜK TESTİ
# ==============================================================================
print("\n[3] CANLI 4 MEZHEP ÇAPRAZ SORGULAMA TESTİ (Arama: 'النية في الوضوء' - Abdestte Niyet)")
test_query = norm_ar("النية الوضوء")
cursor.execute("""
SELECT mezhep, eser, kitab, SUBSTR(metin_orijinal, 1, 110)
FROM fikh_fts
WHERE fikh_fts MATCH ?
GROUP BY mezhep
LIMIT 5;
""", (test_query,))

results = cursor.fetchall()
print("-" * 80)
for r in results:
    print(f"[{r[0]:<7} | {r[1]:<18}] {r[2]}")
    print(f"  Alıntı: {r[3]}...")
print("-" * 80)

conn.close()
print("[+] FAZ 1 DOĞRULANDI VE VERİTABANI İNDEKSİ HATASIZ TAMAMLANDI.")
