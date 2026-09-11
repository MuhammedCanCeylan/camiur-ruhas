import os
import sqlite3

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=" * 80)
print("[*] EKSİK KALAN KASSAFU'L-KINA MÜELLİFİNİN DÜZELTİLMESİ")
print("=" * 80)

# Buhûtî eşlemesi (Kassaf varyantı)
cur.execute("""
UPDATE fikh_nodes 
SET muellif = 'Mansûr el-Buhûtî (v. 1051)' 
WHERE eser LIKE '%kassaf%' OR eser LIKE '%kina%';
""")
conn.commit()

# FTS tablosunu güncelle
cur.execute("""
UPDATE fikh_fts 
SET muellif = 'Mansûr el-Buhûtî (v. 1051)' 
WHERE eser LIKE '%kassaf%' OR eser LIKE '%kina%';
""")
conn.commit()

# Nihai Kontrol
cur.execute("SELECT muellif, COUNT(*) FROM fikh_nodes GROUP BY muellif ORDER BY COUNT(*) DESC;")
print(f"{'MÜELLİF':<45} | {'DÜĞÜM SAYISI'}")
print("-" * 80)
for auth, cnt in cur.fetchall():
    print(f"{auth:<45} | {cnt:<8,}")
print("-" * 80)

cur.execute("SELECT COUNT(*) FROM fikh_nodes WHERE muellif = 'Bilinmeyen Müellif';")
unknown_count = cur.fetchone()[0]
print(f"[*] Kalan Bilinmeyen Müellif: {unknown_count}")

conn.close()
if unknown_count == 0:
    print("[+] TÜM MÜELLİFLER %100 EŞLEŞTİ. FAZ 2 EKSİKSİZ KAPANDI.")
else:
    print("[-] Hâlâ eşleşmeyen kayıt var!")
print("=" * 80)
