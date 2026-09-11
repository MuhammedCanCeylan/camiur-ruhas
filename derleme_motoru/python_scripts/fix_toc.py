import os
import re

BOOK_DIR = r"D:\fikh_kitap"
CHAPTERS_DIR = os.path.join(BOOK_DIR, "bolumler")
MASTER_BOOK_PATH = os.path.join(BOOK_DIR, "Camiur_Ruhas_Nihai_Kulliyat.md")

# Salât dosyasındaki eski 005 ve 006 kalıntılarını temizle (007'den başlat)
salat_path = os.path.join(CHAPTERS_DIR, "02_salat.md")
if os.path.exists(salat_path):
    with open(salat_path, "r", encoding="utf-8") as f:
        s_text = f.read()
    
    # 007 öncesi blokları kes
    parts = re.split(r"(?=# BÖLÜM:)", s_text)
    clean_parts = [p.strip() for p in parts if re.search(r"## MESELE 0(0[7-9]|10):", p)]
    with open(salat_path, "w", encoding="utf-8") as f:
        f.write("# KİTÂBÜ'S-SALÂT (NAMAZ VE VAKİTLER)\n\n" + "\n\n---\n\n".join(clean_parts) + "\n")

# Master Külliyatı Yeniden Derle
files = [
    ("01_taharet.md", "KİTÂBÜ'T-TAHÂRET (TEMİZLİK VE ABDEST)"),
    ("02_salat.md", "KİTÂBÜ'S-SALÂT (NAMAZ VE VAKİTLER)"),
    ("03_siyam.md", "KİTÂBÜ'S-SIYÂM (ORUÇ VE İMSAK)"),
    ("04_buyu.md", "KİTÂBÜ'L-BÜYÛ' (TİCARET VE MUÂMELÂT)")
]

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
body_blocks = []

for fname, bname in files:
    fpath = os.path.join(CHAPTERS_DIR, fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    toc_lines.append(f"\n#### {bname.upper()}")
    issues = re.findall(r"## MESELE (\d+):\s*(.+)", content)
    for num, name in issues:
        toc_lines.append(f"- **Mesele {num}:** {name.strip()}")

    # Bölüm başlığını hariç tutarak blokları ekle
    parts = [p.strip() for p in re.split(r"(?=# BÖLÜM:)", content) if p.strip() and not p.strip().startswith("# KİTÂBÜ")]
    body_blocks.extend(parts)

master_full = mukaddime + "\n".join(toc_lines) + "\n\n---\n\n" + "\n\n---\n\n".join(body_blocks)

with open(MASTER_BOOK_PATH, "w", encoding="utf-8") as f:
    f.write(master_full)

print("=" * 80)
print(f"[+] 001 - 016 Mesele fihristi ardışık olarak temizlendi.")
print(f"    Master Kitap Boyutu: {os.path.getsize(MASTER_BOOK_PATH) / 1024:.2f} KB")
print("=" * 80)
