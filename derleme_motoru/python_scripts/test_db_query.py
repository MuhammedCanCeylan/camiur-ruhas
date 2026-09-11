import os
import sqlite3
import re

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
RE_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]")

def norm_ar(text):
    text = RE_TASHKEEL.sub("", str(text))
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    return text

if not os.path.exists(DB_PATH):
    print("[-] Veritabani bulunamadi.")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Külliyat Bütünlük Sayımı
print("=" * 80)
print("[*] 4 MEZHEP VERİTABANI NİHAİ DÜĞÜM DAĞILIMI")
print("=" * 80)
cursor.execute("""
SELECT mezhep, COUNT(DISTINCT eser), COUNT(*) 
FROM fikh_nodes 
GROUP BY mezhep 
ORDER BY COUNT(*) DESC;
""")
for m, eser_count, node_count in cursor.fetchall():
    print(f"  Mezhep: {m:<8} | Eser Sayısı: {eser_count} | Düğüm (Chunk) Sayısı: {node_count:<7,}")

# 2. Canlı Çapraz Fıkıh Sorgusu: Abdestte Niyetin Hükmü (النية الوضوء)
sorgu_terimi = norm_ar("النية الوضوء")
print("\n" + "=" * 80)
print(f"[*] CANLI ÇAPRAZ SORGULAMA: '{sorgu_terimi}' (Abdestte Niyet)")
print("=" * 80)

mezhepler = ["Hanefi", "Safii", "Maliki", "Hanbeli", "Mukaren"]

for m in mezhepler:
    cursor.execute("""
    SELECT n.mezhep, n.eser, n.cilt, n.sayfa, n.kitab, n.bab, n.metin_orijinal
    FROM fikh_fts f
    JOIN fikh_nodes n ON n.id = f.rowid
    WHERE fikh_fts MATCH ? AND n.mezhep = ?
    ORDER BY rank
    LIMIT 1;
    """, (sorgu_terimi, m))
    
    row = cursor.fetchone()
    if row:
        print(f"\n[{row[0].upper()}] - {row[1]} (Cilt: {row[2]}, Sayfa: {row[3]})")
        print(f"Bölüm  : {row[4]} / {row[5]}")
        snippet = " ".join(row[6].split()[:35])
        print(f"Metin  : {snippet}...")
    else:
        print(f"\n[{m.upper()}] - Eşleşen kayıt bulunamadı.")

conn.close()
print("\n" + "=" * 80)
print("[+] FAZ 1 RESMEN VE EKSİKSİZ TAMAMLANDI.")
print("=" * 80)
