import os
import re
import sqlite3
import nltk
from nltk.stem.isri import ISRIStemmer
from tqdm import tqdm

DB_PATH = os.path.join("metadata", "fikh_corpus.db")

print("=" * 80)
print("[*] FAZ 2.A & 2.B: MÜELLİF HARİTALAMA VE ARAPÇA KÖK (STEMMING) İNDEKSİ")
print("=" * 80)

# Müellif Haritası (Eser Adı / Varyantı -> Müellif)
AUTHOR_MAP = {
    # Hanefi
    "mabsut": "Şemsü'l-Eimme es-Serahsî (v. 483)",
    "bedai": "Alâüddîn el-Kâsânî (v. 587)",
    "sanai": "Alâüddîn el-Kâsânî (v. 587)",
    "kasani": "Alâüddîn el-Kâsânî (v. 587)",
    "radd": "İbn Âbidîn (v. 1252)",
    "muhtar": "İbn Âbidîn (v. 1252)",
    "abidin": "İbn Âbidîn (v. 1252)",
    
    # Safii
    "umm": "İmam Muhammed b. İdrîs eş-Şâfiî (v. 204)",
    "safii": "İmam Muhammed b. İdrîs eş-Şâfiî (v. 204)",
    "majmu": "Muhyiddîn en-Nevevî (v. 676)",
    "mecmu": "Muhyiddîn en-Nevevî (v. 676)",
    "minhaj": "Muhyiddîn en-Nevevî (v. 676)",
    "minhac": "Muhyiddîn en-Nevevî (v. 676)",
    "nihayat": "Şemsüddîn er-Remlî (v. 1004)",
    "nihaye": "Şemsüddîn er-Remlî (v. 1004)",
    
    # Maliki
    "muwatta": "İmam Mâlik b. Enes (v. 179)",
    "mudawwana": "Sahnûn b. Saîd (v. 240)",
    "mudavvene": "Sahnûn b. Saîd (v. 240)",
    "kafi": "İbn Abdilberr (v. 463)",
    "mawahib": "el-Hattâb er-Ruaynî (v. 954)",
    "jalil": "el-Hattâb er-Ruaynî (v. 954)",
    
    # Hanbeli
    "mugni": "Muvaffakuddîn İbn Kudâme (v. 620)",
    "kudama": "Muvaffakuddîn İbn Kudâme (v. 620)",
    "insaf": "Alâüddîn el-Merdâvî (v. 885)",
    "mardawi": "Alâüddîn el-Merdâvî (v. 885)",
    "kashshaf": "Mansûr el-Buhûtî (v. 1051)",
    "buhuti": "Mansûr el-Buhûtî (v. 1051)",
    
    # Mukaren
    "bidayat": "İbn Rüşd el-Hafîd (v. 595)",
    "mujtahid": "İbn Rüşd el-Hafîd (v. 595)",
    "rusd": "İbn Rüşd el-Hafîd (v. 595)"
}

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Şema Güncellemesi
cur.execute("PRAGMA table_info(fikh_nodes);")
cols = [c[1] for c in cur.fetchall()]

if "muellif" not in cols:
    print("[*] 'muellif' kolonu ekleniyor...")
    cur.execute("ALTER TABLE fikh_nodes ADD COLUMN muellif TEXT;")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_muellif ON fikh_nodes(muellif);")

if "kok_dizini" not in cols:
    print("[*] 'kok_dizini' kolonu ekleniyor...")
    cur.execute("ALTER TABLE fikh_nodes ADD COLUMN kok_dizini TEXT;")

conn.commit()

# 2. Müelliflerin Eşlenmesi
print("[*] Müellif bilgileri eser isimlerinden ayrıştırılıyor...")
cur.execute("SELECT DISTINCT eser FROM fikh_nodes;")
eserler = [r[0] for r in cur.fetchall()]

for e in eserler:
    matched_author = "Bilinmeyen Müellif"
    clean_e = e.lower()
    for key, auth in AUTHOR_MAP.items():
        if key in clean_e:
            matched_author = auth
            break
    cur.execute("UPDATE fikh_nodes SET muellif = ? WHERE eser = ?;", (matched_author, e))

conn.commit()

# Müellif Dağılım Kontrolü
print("\n" + "-" * 80)
print(f"{'MÜELLİF':<45} | {'DÜĞÜM SAYISI'}")
print("-" * 80)
cur.execute("SELECT muellif, COUNT(*) FROM fikh_nodes GROUP BY muellif ORDER BY COUNT(*) DESC;")
for auth, cnt in cur.fetchall():
    print(f"{auth:<45} | {cnt:<8,}")
print("-" * 80)

# 3. Morfolojik Kök Çıkarımı (ISRI Stemmer ile Başlık ve Anahtar Lafızlar)
print("\n[*] Arapça kök (ISRI Stemmer) analizi başlatılıyor...")
stemmer = ISRIStemmer()
RE_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]")

def extract_roots(text):
    text = RE_TASHKEEL.sub("", str(text))
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    words = re.findall(r"[\u0621-\u064A]{3,}", text)
    roots = set()
    for w in words[:40]:  # Her bloğun başlık ve ilk fıkhi lafızlarından kök çıkar
        r = stemmer.stem(w)
        if len(r) >= 3:
            roots.add(r)
    return " ".join(roots)

cur.execute("SELECT id, kitab, bab, fasl, metin_arama FROM fikh_nodes WHERE kok_dizini IS NULL OR kok_dizini = '';")
unstemmed = cur.fetchall()

if unstemmed:
    print(f"[*] Kök çıkarımı yapılacak kayıt sayısı: {len(unstemmed):,}")
    batch_updates = []
    for row_id, k, b, f, m in tqdm(unstemmed, desc="ISRI Stemming", unit="node"):
        context_text = f"{k} {b} {f} {m[:200]}"
        roots_str = extract_roots(context_text)
        batch_updates.append((roots_str, row_id))
        
        if len(batch_updates) >= 5000:
            cur.executemany("UPDATE fikh_nodes SET kok_dizini = ? WHERE id = ?;", batch_updates)
            conn.commit()
            batch_updates = []
            
    if batch_updates:
        cur.executemany("UPDATE fikh_nodes SET kok_dizini = ? WHERE id = ?;", batch_updates)
        conn.commit()
else:
    print("[+] Tüm düğümlerde kök dizini mevcut.")

# 4. FTS Tablosuna Kök Dizinini Dahil Etme
print("\n[*] FTS5 indeksi kök aramasıyla güncelleniyor...")
cur.execute("DROP TABLE IF EXISTS fikh_fts;")
cur.execute("""
CREATE VIRTUAL TABLE fikh_fts USING fts5(
    node_id UNINDEXED,
    mezhep,
    muellif,
    eser,
    kanonik_konu,
    metin_arama,
    kok_dizini,
    content='fikh_nodes',
    content_rowid='id',
    tokenize='unicode61'
);
""")

cur.execute("""
INSERT INTO fikh_fts(rowid, node_id, mezhep, muellif, eser, kanonik_konu, metin_arama, kok_dizini)
SELECT id, node_id, mezhep, muellif, eser, kanonik_konu, metin_arama, kok_dizini FROM fikh_nodes;
""")
conn.commit()

cur.execute("SELECT COUNT(*) FROM fikh_fts;")
fts_count = cur.fetchone()[0]
print(f"[+] Güncel FTS5 İndeksli Kayıt: {fts_count:,}")

conn.close()
print("=" * 80)
print("[+] ADIM 2.A & 2.B EKSİKSİZ TAMAMLANDI.")
print("=" * 80)
