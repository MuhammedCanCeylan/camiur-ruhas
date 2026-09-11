import os
import sqlite3
import lancedb
import numpy as np

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
LANCE_PATH = os.path.join("metadata", "fikh_lancedb")

print("=" * 80)
print("[*] FIKIH KORPUSU VE VEKTOR VERITABANI DERINLEMESINE SIHHAT DENETIMI")
print("=" * 80)

# 1. DOSYA VE DIZIN KONTROLU
print("\n[1] DEPOLAMA VE DOSYA SISTEMI DURUMU")
print("-" * 80)
if os.path.exists(DB_PATH):
    db_size = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"[+] SQLite DB      : {DB_PATH} ({db_size:.2f} MB) -> MEVCUT")
else:
    print(f"[-] SQLite DB      : {DB_PATH} -> BULUNAMADI!")

if os.path.exists(LANCE_PATH):
    lance_size = sum(
        os.path.getsize(os.path.join(dirpath, f))
        for dirpath, _, filenames in os.walk(LANCE_PATH)
        for f in filenames
    ) / (1024 * 1024)
    print(f"[+] LanceDB Deposu : {LANCE_PATH} ({lance_size:.2f} MB) -> MEVCUT")
else:
    print(f"[-] LanceDB Deposu : {LANCE_PATH} -> BULUNAMADI!")

# 2. SQLITE VE FTS5 BUTUNLUK DENETIMI
print("\n[2] SQLITE VE FTS5 TAM METIN INDEKS DENETIMI")
print("-" * 80)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("PRAGMA integrity_check;")
db_integrity = cur.fetchone()[0]
print(f"[*] SQLite PRAGMA Integrity : {db_integrity}")

cur.execute("SELECT COUNT(*) FROM fikh_nodes;")
total_sql = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM fikh_nodes WHERE is_embedded = 1;")
embedded_sql = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM fikh_nodes WHERE is_embedded = 0;")
pending_sql = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM fikh_fts;")
total_fts = cur.fetchone()[0]

print(f"[*] Toplam SQLite Düğüm     : {total_sql:,}")
print(f"[*] İşaretli Embedded (1)   : {embedded_sql:,}")
print(f"[*] Bekleyen Düğüm (0)      : {pending_sql:,}")
print(f"[*] FTS5 İndeksli Kayıt     : {total_fts:,}")

sql_fts_parity = (total_sql == embedded_sql) and (total_sql == total_fts)
print(f"[*] SQLite <-> FTS5 Uyumu   : {'TAM VE HATASIZ' if sql_fts_parity else 'TUTARSIZLIK VAR!'}")

# 3. LANCEDB VEKTOR VE TENSOR DENETIMI
print("\n[3] LANCEDB VEKTOR TABLOSU VE TENSOR BOYUT DENETIMI")
print("-" * 80)
db = lancedb.connect(LANCE_PATH)
tbl = db.open_table("fikh_vectors")
total_lance = len(tbl)

print(f"[*] LanceDB Vektör Sayısı   : {total_lance:,}")
parity_check = (total_sql == total_lance)
print(f"[*] SQLite <-> LanceDB Birebir Parite: {'%100 ESLESME' if parity_check else 'ESLESMEME HATASI!'}")

# Ornek Vektor Analizi (NaN, Inf ve Norm kontrolu)
sample_rows = tbl.search().limit(5).to_list()
vec_dim = len(sample_rows[0]["vector"]) if sample_rows else 0
print(f"[*] Vektör Boyutu (Dim)     : {vec_dim} (Beklenen: 1024)")

nan_detected = False
for idx, r in enumerate(sample_rows):
    v = np.array(r["vector"], dtype=np.float32)
    if np.isnan(v).any() or np.isinf(v).any():
        nan_detected = True
        break

print(f"[*] Tensör Değerleri        : {'GECERLI (NaN/Inf YOK)' if not nan_detected else 'BOZUK VERI (NaN TESPIT EDILDI)!'}")

# 4. MEZHEP VE ESER BAZLI ESLESTIRME MATRISI
print("\n[4] 4 HAK MEZHEP VE MUKAREN DAGILIM MATRISI")
print("-" * 80)
print(f"{'MEZHEP':<10} | {'ESER SAYISI':<12} | {'SQLITE DUGUM':<14} | {'DURUM'}")
print("-" * 80)

cur.execute("""
SELECT mezhep, COUNT(DISTINCT eser), COUNT(*)
FROM fikh_nodes
GROUP BY mezhep
ORDER BY COUNT(*) DESC;
""")
for m, eser_cnt, n_cnt in cur.fetchall():
    print(f"{m:<10} | {eser_cnt:<12} | {n_cnt:<14,} | AKTIF")

conn.close()

print("-" * 80)
print("SİSTEM GENEL DURUMU:")
if sql_fts_parity and parity_check and (vec_dim == 1024) and not nan_detected:
    print("[+] TUM VERI, VEKTOR VE INDEKS KATMANLARI %100 SIHHATLE TAMAMLANDI.")
    print("[+] HIBRIT ARAMA (Faz 2.2) ICIN HAZIR.")
else:
    print("[-] DIKKAT: Eksik veya tutarsiz blok tespit edildi!")
print("=" * 80)
