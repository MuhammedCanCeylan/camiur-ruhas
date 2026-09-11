import os
import re
import json
import sqlite3
import sys

PROCESSED_DIR = "processed"
METADATA_DIR = "metadata"
os.makedirs(METADATA_DIR, exist_ok=True)
DB_PATH = os.path.join(METADATA_DIR, "fikh_corpus.db")

FILES = [
    ("Mukaren", "bidayat_al_mujtahid_refined.json"),
    ("Hanefi", "hanefi_nodes.json"),
    ("Safii", "safii_nodes.json"),
    ("Maliki", "maliki_nodes.json"),
    ("Hanbeli", "hanbeli_nodes.json")
]

# 16 Kanonik Fıkıh Taksonomi Kuralı (Regex Sözlüğü)
TAXONOMY_RULES = {
    "Tahare": [r"طهار", r"وضو", r"غسل", r"مياه", r"انجاس", r"نجاس", r"تيمم", r"حيض", r"نفاس", r"سواك"],
    "Salat": [r"صلا", r"اذان", r"مواقيت", r"امامة", r"جمعة", r"خوف", r"عيدي", r"جنائز", r"سجود", r"قصر", r"سهو"],
    "Zekat": [r"زكا", r"صدق", r"عشر", r"فطر", r"اموال"],
    "Savm": [r"صوم", r"صيام", r"اعتكاف", r"فطر"],
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

print("=" * 75)
print("[*] SQLITE VERITABANI VE FTS5 INDEKSI OLUSTURULUYOR...")
print("=" * 75)

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ana Tablo
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

# Hızlı Filtreleme İndeksleri
cursor.execute("CREATE INDEX idx_mezhep ON fikh_nodes(mezhep);")
cursor.execute("CREATE INDEX idx_eser ON fikh_nodes(eser);")
cursor.execute("CREATE INDEX idx_konu ON fikh_nodes(kanonik_konu);")

# FTS5 Sanal Arama Tablosu (Full-Text Search)
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

# Triggers ile senkronizasyon
cursor.execute("""
CREATE TRIGGER fikh_ai AFTER INSERT ON fikh_nodes BEGIN
  INSERT INTO fikh_fts(rowid, node_id, mezhep, eser, kanonik_konu, metin_arama)
  VALUES (new.id, new.node_id, new.mezhep, new.eser, new.kanonik_konu, new.metin_arama);
END;
""")

insert_records = []
stats = {k: 0 for k in TAXONOMY_RULES.keys()}
stats["Genel_Diger"] = 0

for mezhep_tag, filename in FILES:
    fpath = os.path.join(PROCESSED_DIR, filename)
    if not os.path.exists(fpath):
        print(f"[-] Dosya bulunamadi: {fpath}")
        continue

    print(f"[*] Veritabanina aktariliyor: [{mezhep_tag}] {filename}...")
    with open(fpath, "r", encoding="utf-8") as f:
        nodes = json.load(f)

    for n in nodes:
        k_raw = norm_ar(n.get("kitab", ""))
        b_raw = norm_ar(n.get("bab", ""))
        f_raw = norm_ar(n.get("fasl", n.get("fasl_mesele", "")))
        header_context = f"{k_raw} {b_raw} {f_raw}"

        # Konu Tespiti
        matched_cat = "Genel_Diger"
        for cat, patterns in TAXONOMY_RULES.items():
            if any(re.search(p, header_context) for p in patterns):
                matched_cat = cat
                break

        stats[matched_cat] += 1

        insert_records.append((
            n["node_id"],
            n.get("mezhep", mezhep_tag),
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

conn.close()

print("\n" + "=" * 75)
print("VERITABANI VE INDEKSLEME RAPORU:")
print(f"  - Veritabanı Yolu : {DB_PATH}")
print(f"  - Boyut           : {db_size_mb:.2f} MB")
print(f"  - Kayıtlı Düğüm   : {total_in_db:,}")
print(f"  - FTS5 İndeksli   : {total_in_fts:,}")
print("-" * 75)
print("KANONIK KONU DAGILIMI:")
for cat, cnt in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    pct = (cnt / total_in_db) * 100 if total_in_db else 0
    print(f"  {cat:<16}: {cnt:<7,} (%{pct:.2f})")
print("=" * 75)
