import os
import re

BOOK_DIR = r"D:\fikh_kitap"
CHAPTERS_DIR = os.path.join(BOOK_DIR, "bolumler")
MASTER_BOOK_PATH = os.path.join(BOOK_DIR, "Camiur_Ruhas_Nihai_Kulliyat.md")

files = [
    ("01_taharet.md", "KİTÂBÜ'T-TAHÂRET (TEMİZLİK VE ABDEST)"),
    ("02_salat.md", "KİTÂBÜ'S-SALÂT (NAMAZ VE VAKİTLER)"),
    ("03_siyam.md", "KİTÂBÜ'S-SIYÂM (ORUÇ VE İMSAK)"),
    ("04_buyu.md", "KİTÂBÜ'L-BÜYÛ' (TİCARET VE MUÂMELÂT)")
]

cleaned_chapters = {}

for fname, bname in files:
    fpath = os.path.join(CHAPTERS_DIR, fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # Mesele bloklarını ayıkla (## MESELE XXX: ...)
    raw_blocks = re.split(r"(?=# BÖLÜM:)", content)
    unique_issues = {}
    for block in raw_blocks:
        m = re.search(r"## MESELE (\d+):\s*(.+)", block)
        if m:
            m_id = int(m.group(1))
            # Her mesele numarasının en son (en güncel) halini sakla
            unique_issues[m_id] = block.strip()

    # Sıralı olarak bölüm dosyasını yeniden yaz
    sorted_blocks = [unique_issues[k] for k in sorted(unique_issues.keys())]
    cleaned_text = f"# {bname.upper()}\n\n" + "\n\n---\n\n".join(sorted_blocks) + "\n"
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    
    cleaned_chapters[fname] = (bname, sorted_blocks)

# Master kitabı derle
mukaddime = """# CÂMİU'R-RUHAS VE TAHKÎKU'L-MEZÂHİB
## Dört Mezhep Esaslı En Hafif ve Sahih Fıkıh Külliyatı (Lite Tatbikat)

---

### MUKADDİME VE TELİF METODOLOJİSİ
Bu eser; İslam Hukuku'nun dört hak mezhebi (Hanefî, Mâlikî, Şâfiî, Hanbelî) dairesinde kalmak şartıyla, mükellefi meşakkatten kurtaran **en hafif, uygulanabilir ve sahih ruhsatları** bir araya getirmek amacıyla telif edilmiştir.

**Metodolojik İlkeler:**
1. **Mezhep İçi Sıhhat:** Seçilen her ruhsat, dört mezhepten en az birinin müctehid imamları veya mezhep içi tercih ehli fukahâsı tarafından sahih kabul edilmiş bir nassa dayanır.
2. **Telfîk-i Bâtıl Güvencesi:** Ameller rastgele parçalanmamış; mezheplerin rükün ve şartları birbirine karıştırılarak hiçbir mezhepçe kabul edilmeyen icmâ-i mürekkep ihlalleri engellenmiştir.
3. **Şeffaf Tahrîc:** Her meselenin altında Hanefî (*el-Mebsût, Bedâi'*), Mâlikî (*el-Kâfî, Mevâhib*), Şâfiî (*el-Ümm, el-Mecmû'*) ve Hanbelî (*Keşşâfü'l-Kınâ', el-Muğnî*) asıl ibareleri cilt ve sayfa numaralarıyla verilmiştir.

---

### İÇİNDEKİLER (FİHRİST)
"""

toc_lines = []
all_sections = []

for fname, (bname, blocks) in cleaned_chapters.items():
    toc_lines.append(f"\n#### {bname.upper()}")
    for blk in blocks:
        m = re.search(r"## MESELE (\d+):\s*(.+)", blk)
        if m:
            toc_lines.append(f"- **Mesele {m.group(1)}:** {m.group(2).strip()}")
        all_sections.append(blk)

master_full = mukaddime + "\n".join(toc_lines) + "\n\n---\n\n" + "\n\n---\n\n".join(all_sections)

with open(MASTER_BOOK_PATH, "w", encoding="utf-8") as f:
    f.write(master_full)

print("=" * 80)
print(f"[+] Mükerrer kayıtlar temizlendi. Master kitap güncellendi:")
print(f"    Dosya: {MASTER_BOOK_PATH}")
print(f"    Boyut: {os.path.getsize(MASTER_BOOK_PATH) / 1024:.2f} KB")
print("=" * 80)
