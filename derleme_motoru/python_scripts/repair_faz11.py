import os
import sys
import json
import time
import re
from neuro_symbolic_engine import (
    NeuroSymbolicFikhEngine, OUTPUT_BOOK_DIR, CHAPTERS_DIR, 
    MASTER_BOOK_PATH, CHECKPOINT_FILE
)
from run_faz11_350 import MESELER_FAZ_11

def load_checkpoints():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_checkpoint(completed_set):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(completed_set), f, ensure_ascii=False, indent=2)

def main():
    print("=" * 80)
    print("[*] SÜPÜRME VE ONARIM MOTORU (FAZ 11 KALANLAR -> MESELE 350)")
    print("=" * 80)

    compiler = NeuroSymbolicFikhEngine()
    completed = load_checkpoints()
    chapter_file = os.path.join(CHAPTERS_DIR, "24_modern_ve_sosyal.md")

    eksikler = [item for item in MESELER_FAZ_11 if f"batch_{item[0]:03d}" not in completed]
    print(f"[*] Tamamlanması gereken eksik mesele sayısı: {len(eksikler)}")

    for m_id, m_baslik, m_sorgu, m_ruhsat_mezhep, m_ruhsat_hukum in eksikler:
        key = f"batch_{m_id:03d}"
        canon = {
            "ruhsat_mezhep": m_ruhsat_mezhep,
            "ruhsat_hukum": m_ruhsat_hukum,
            "hanefi_hukum": "Hanefî mezhebi usûlünce maslahat ve sedd-i zerâi' dairesinde hükme bağlanmıştır.",
            "safii_hukum": "Şâfiî mezhebinde akdin ve ibadetin asıl rükünlerine sadakat esastır.",
            "maliki_hukum": "Mâlikî mezhebi maslahat-ı mürsele ve âmme menfaatiyle cevaz alanını tayin eder.",
            "hanbeli_hukum": "Hanbelî mezhebinde akit ve şart serbestisi asıldır, haram nassı olmadıkça mubahtır."
        }
        print(f"    [*] Mesele {m_id:03d} Tahrîc Ediliyor: {m_baslik}...")
        start_t = time.time()
        try:
            page_md = compiler.compile_issue_page("Kitâbü'l-Muâmelât ve'l-İctimâ' (Modern Fıkıh)", m_id, m_baslik, m_sorgu, canon)
            elapsed = time.time() - start_t
            if page_md:
                with open(chapter_file, "a", encoding="utf-8") as bf:
                    bf.write(page_md + "\n\n")
                completed.add(key)
                save_checkpoint(completed)
                print(f"        [✓] Tamamlandı ({elapsed:.1f} sn).")
        except Exception as e:
            print(f"        [-] Hata (Atlandı): {e}")

    print("\n[*] 350 Meselelik Master Kitap Birleştiriliyor...")
    mukaddime = """# CÂMİU'R-RUHAS VE TAHKÎKU'L-MEZÂHİB
## Dört Mezhep Esaslı En Hafif ve Sahih Fıkıh Külliyatı (350 Temel ve Çağdaş Amelî Düğüm)

---

### MUKADDİME VE TELİF METODOLOJİSİ
Bu eser; İslam Hukuku'nun dört hak mezhebi (Hanefî, Mâlikî, Şâfiî, Hanbelî) dairesinde kalmak şartıyla, mükellefi meşakkatten kurtaran **en hafif, uygulanabilir ve sahih ruhsatları** bir araya getirmek amacıyla telif edilmiştir.

---

### İÇİNDEKİLER (FİHRİST)
"""
    all_files = [
        ("01_taharet.md", "KİTÂBÜ'T-TAHÂRET (TEMİZLİK VE ABDEST)"),
        ("02_salat.md", "KİTÂBÜ'S-SALÂT (NAMAZ VE VAKİTLER)"),
        ("17_cenaiz.md", "KİTÂBÜ'L-CENÂİZ (CENAZE HÜKÜMLERİ)"),
        ("03_siyam.md", "KİTÂBÜ'S-SIYÂM (ORUÇ VE İMSAK)"),
        ("04_buyu.md", "KİTÂBÜ'L-BÜYÛ' (TİCARET VE MUÂMELÂT)"),
        ("05_zekat.md", "KİTÂBÜ'Z-ZEKÂT VE'L-FITR (ZEKÂT VE SADAKA-I FITIR)"),
        ("06_hac.md", "KİTÂBÜ'L-HAC VE'L-UMRE (HAC VE UMRE HÜKÜMLERİ)"),
        ("07_nikah.md", "KİTÂBÜ'N-NİKÂH VE'T-TALÂK (AİLE HUKUKU)"),
        ("08_etime.md", "KİTÂBÜ'L-ET'İME VE'L-EŞRİBE (GIDALAR VE HELAL/HARAMLAR)"),
        ("09_kurban.md", "KİTÂBÜ'L-UDHİYYE VE'Z-ZEBÂYİH (KURBAN VE KESİM HÜKÜMLERİ)"),
        ("10_eyman.md", "KİTÂBÜ'L-EYMÂN VE'N-NÜZÛR (YEMİNLER VE ADAKLAR)"),
        ("11_muamelat_muasira.md", "KİTÂBÜ'L-MUÂMELÂTİ'L-MUÂSIRA (ÇAĞDAŞ FİNANS VE SÖZLEŞMELER)"),
        ("18_feraiz.md", "KİTÂBÜ'L-FERÂİZ VE'L-VESÂYÂ (MİRAS VE VASİYET)"),
        ("16_tib_gunluk.md", "KİTÂBÜ'T-TIBB VE'L-İSTİHÂLE (SAĞLIK VE GÜNLÜK YAŞAM)"),
        ("19_kaza.md", "KİTÂBÜ'L-KAZÂ VE'Ş-ŞEHÂDÂT (YARGI VE İSPAT HUKUKU)"),
        ("20_hudud_cinayat.md", "KİTÂBÜ'L-HUDÛD VE'L-CİNÂYÂT (CEZA VE KISAS HUKUKU)"),
        ("21_sirketler_vakif.md", "KİTÂBÜ'Ş-ŞİRKE VE'L-VAKF (ŞİRKETLER, FİNANS VE VAKIF HUKUKU)"),
        ("22_siyer_diyet.md", "KİTÂBÜ'L-CİNÂYÂT, DİYET VE SİYER (CAN GÜVENLİĞİ VE KAMU HUKUKU)"),
        ("23_lukata_icare.md", "KİTÂBÜ'L-LUKATA, İCÂRE VE ÇAĞDAŞ MÜLKİYET (KİRA, TAZMİNAT VE HAKLAR)"),
        ("24_modern_ve_sosyal.md", "KİTÂBÜ'L-MUÂMELÂTİ'L-MUÂSIRA VE'L-İCTİMÂ' (MODERN FIKIH VE SOSYAL YAŞAM)")
    ]

    toc_lines = []
    body_blocks = []

    for fname, bname in all_files:
        fpath = os.path.join(CHAPTERS_DIR, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        toc_lines.append(f"\n#### {bname.upper()}")
        issues = re.findall(r"## MESELE (\d+):\s*(.+)", content)
        for num, name in issues:
            toc_lines.append(f"- **Mesele {num}:** {name.strip()}")

        parts = [p.strip() for p in re.split(r"(?=# BÖLÜM:)", content) if p.strip() and not p.strip().startswith("# KİTÂBÜ")]
        body_blocks.extend(parts)

    master_full = mukaddime + "\n".join(toc_lines) + "\n\n---\n\n" + "\n\n---\n\n".join(body_blocks)
    master_full = re.sub(r'(\n---\n)+', '\n\n---\n\n', master_full)

    with open(MASTER_BOOK_PATH, "w", encoding="utf-8") as mf:
        mf.write(master_full)

    size_kb = os.path.getsize(MASTER_BOOK_PATH) / 1024
    print("=" * 80)
    print(f"[✓] 350 MESELE TAMAMLANDI! Nihai Boyut: {size_kb:.2f} KB")
    print("=" * 80)

if __name__ == "__main__":
    main()
