import os
import re
import json
import sqlite3

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
OUTPUT_MATRIX = os.path.join("D:\\fikh_kitap", "fikh_hilaf_matrix.json")

def discover_hilaf_issues():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("[*] Mukayeseli Fıkıh ve İhtilaf Düğümleri Taranıyor...")

    # Bidâyetü'l-Müctehid ve ana fıkıh kitaplarındaki 'İhtelefe', 'Bâb', 'Fasl' ve 'Mes'ele' düğümlerini topla
    cur.execute("""
        SELECT id, node_id, mezhep, muellif, eser, kitab, bab, metin_orijinal
        FROM fikh_nodes
        WHERE (metin_orijinal LIKE '%اختلف%' OR metin_orijinal LIKE '%ذهب جمهور%' OR metin_orijinal LIKE '%وعند الشافعي%' OR metin_orijinal LIKE '%وعند أبي حنيفة%')
        AND kitab IS NOT NULL AND kitab != ''
        ORDER BY id ASC
        LIMIT 1000;
    """)
    rows = cur.fetchall()
    print(f"[+] Taranabilir potansiyel ihtilaf metni sayısı: {len(rows)}")

    discovered_issues = []
    seen_topics = set()

    for r in rows:
        node_id, mezhep, muellif, eser, kitab, bab, text = r[1], r[2], r[3], r[4], r[5], r[6], r[7]
        
        # Bab veya Kitap başlığını temizle
        clean_bab = bab.strip() if bab else ""
        clean_kitab = kitab.strip() if kitab else ""
        
        # Konu çekirdeğini izole et
        topic_key = f"{clean_kitab} - {clean_bab}"
        if len(clean_bab) < 4 or topic_key in seen_topics:
            continue

        seen_topics.add(topic_key)

        discovered_issues.append({
            "index": len(discovered_issues) + 1,
            "kitab": clean_kitab,
            "bab": clean_bab,
            "ornek_eser": f"{muellif} - {eser}",
            "orijinal_metin_kesit": text[:250].replace("\n", " ") + "...",
            "durum": "Doğrulama Bekliyor"
        })

    with open(OUTPUT_MATRIX, "w", encoding="utf-8") as f:
        json.dump(discovered_issues, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print(f"[+] İHTİLAF MATRİSİ BAŞARIYLA ÇIKARILDI:")
    print(f"    Dosya: {OUTPUT_MATRIX}")
    print(f"    Tespit Edilen Benzersiz Düğüm Sayısı: {len(discovered_issues)}")
    print("=" * 80)

if __name__ == "__main__":
    discover_hilaf_issues()
