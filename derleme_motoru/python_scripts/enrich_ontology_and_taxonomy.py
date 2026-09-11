import os
import re
import sqlite3
from tqdm import tqdm

DB_PATH = os.path.join("metadata", "fikh_corpus.db")

print("=" * 80)
print("[*] ADIM 2.A (DÜZELTME) & ADIM 2.C: MESELE_ID VE KANONİK ONTOLOJİ İNŞASI")
print("=" * 80)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Müellif Eşleşme Onarımı
print("\n[1] EKSİK MÜELLİFLERİN TEŞHİS VE ONARIMI...")
cur.execute("SELECT DISTINCT eser FROM fikh_nodes WHERE muellif = 'Bilinmeyen Müellif';")
bilinmeyenler = [r[0] for r in cur.fetchall()]
print(f"[*] Eşleşmeyen eser adları: {bilinmeyenler}")

cur.execute("""
UPDATE fikh_nodes 
SET muellif = 'İmam Mâlik b. Enes (v. 179)' 
WHERE eser LIKE '%muvatt%' OR eser LIKE '%muwatt%' OR eser LIKE '%malik%';
""")

cur.execute("""
UPDATE fikh_nodes 
SET muellif = 'Mansûr el-Buhûtî (v. 1051)' 
WHERE eser LIKE '%kash%' OR eser LIKE '%kes%' OR eser LIKE '%buhut%' OR eser LIKE '%qina%';
""")

cur.execute("""
UPDATE fikh_nodes 
SET muellif = 'Muhyiddîn en-Nevevî (v. 676)' 
WHERE (eser LIKE '%minhaj%' OR eser LIKE '%minhac%') AND muellif = 'Bilinmeyen Müellif';
""")

conn.commit()

# Müellif Durum Denetimi
cur.execute("SELECT muellif, COUNT(*) FROM fikh_nodes GROUP BY muellif ORDER BY COUNT(*) DESC;")
print("\n" + "-" * 80)
print(f"{'MÜELLİF':<45} | {'DÜĞÜM SAYISI'}")
print("-" * 80)
for auth, cnt in cur.fetchall():
    print(f"{auth:<45} | {cnt:<8,}")
print("-" * 80)

# 2. Şemaya mesele_id Eklenmesi
cur.execute("PRAGMA table_info(fikh_nodes);")
cols = [c[1] for c in cur.fetchall()]
if "mesele_id" not in cols:
    print("[*] 'mesele_id' kolonu fikh_nodes tablosuna ekleniyor...")
    cur.execute("ALTER TABLE fikh_nodes ADD COLUMN mesele_id TEXT;")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mesele_id ON fikh_nodes(mesele_id);")

# 3. Kanonik Fıkıh Mesele Kataloğu (Master Taxonomy) Tablosu
cur.execute("""
CREATE TABLE IF NOT EXISTS fikh_meseleler (
    mesele_id TEXT PRIMARY KEY,
    ana_bolum TEXT,
    mesele_adi_tr TEXT,
    mesele_adi_ar TEXT,
    anahtar_kalıplar TEXT
);
""")
cur.execute("DELETE FROM fikh_meseleler;")

# 16 Kanonik Ana Bölüm İçin Örnek Standart Fıkhi Mesele Haritası
KANONIK_MESELELER = [
    # Tahâret
    ("TAH_001", "Tahare", "Abdestte Niyetin Farziyeti ve Sıhhat Şartı Olması", "اشتراط النية في الوضوء", "نية|قصد|طهارة تعبدية"),
    ("TAH_002", "Tahare", "Müstamel Suyun Hükmü ve Temizleyicilik Vasfı", "حكم الماء المستعمل في الطهارة", "مستعمل|طاهر غير طهور|ازالة نجس"),
    ("TAH_003", "Tahare", "Mestler Üzerine Meshte Süre ve Caizlik", "المسح على الخفين للمقيم والمسافر", "مسح|خف|خفاف|يوم وليلة|ثلاثة ايام"),
    ("TAH_004", "Tahare", "Teyemmümün Meşruiyeti ve Toprağın Cinsi", "اشتراط الصعيد الطيب في التيمم", "تيمم|صعيد|تراب|ضربتين"),
    
    # Salât (Namaz)
    ("SAL_001", "Salat", "Namazda İftitah Tekbirinin Hükmü ve Rükün Oluşu", "تكبيرة الإحرام والافتتاح في الصلاة", "تكبيرة|احرام|افتتاح|فرض الصلاة"),
    ("SAL_002", "Salat", "İmama Uyan Kişinin Fâtiha Okumasının Hükmü", "قراءة المأموم للفاتحة خلف الإمام", "فاتحة|خلف الامام|انصات|قراءة"),
    ("SAL_003", "Salat", "Namazda Ta'dîl-i Erkânın Farziyeti ve Vücûbu", "تعديل الأركان والطمأنينة في الركوع والسجود", "تعديل|طمانينة|سجود|ركوع|اطمئن"),
    ("SAL_004", "Salat", "Sehiv Secdesinin Sebepleri ve Vakti", "محل سجود السهو قبل السلام أو بعده", "سهو|سجدتا|قبل السلام|بعد السلام"),
    
    # Zekât & Savm
    ("ZEK_001", "Zekat", "Zekât Nisâbı ve Hıyelnâme ile Düşürülmesi", "بلوغ النصاب وحولان الحول في الزكاة", "نصاب|حول|عشر|ذهب|فضة"),
    ("SAV_001", "Savm", "Ramazan Orucunda Geceden Niyet Şartı", "تبييت النية من الليل في صوم رمضان", "تبييت|نية الصوم|ليل|امساك"),
    
    # Büyû' (Muâmelât)
    ("BUY_001", "Buyu", "Kabz Edilmeden Önce Malın Satışı (Bey' Kable'l-Kabz)", "بيع المبيع قبل القبض", "قبل القبض|قبض|تخلية|نهى رسول"),
    ("BUY_002", "Buyu", "Borcun Borçla Satışı (Bey'u'l-Kâli' bi'l-Kâli')", "نهى عن بيع الكالئ بالكالئ وبيع الدين بالدين", "الكالئ|الدين بالدين|نسيئة بنسيئة"),
    ("BUY_003", "Buyu", "Ribâ-i Fadl ve Ribâ-i Nesîe İlletleri", "علة الربا في الأصناف الستة", "ربا|اصناف ستة|مكيل|موزون|طعم|نقدية"),
    ("BUY_004", "Buyu", "Muhayyerlik Şartı ve Süresi (Hıyâru'ş-Şart)", "مدة خيار الشرط في عقد البيع", "خيار الشرط|ثلاثة ايام|مجلس"),
    
    # Nikâh & Talâk
    ("NIK_001", "Nikah", "Velisiz Nikâhın Sıhhat ve Butlânı", "اشتراط الولي في صحة عقد النكاح", "لا نكاح الا بولي|نكاح بغير اذن|صداق"),
    ("NIK_002", "Nikah", "Nikâhta Şahitlik Şartı ve Şahitlerin Evsafı", "الشهادة في عقد النكاح", "شاهدي عدل|اشهاد|اعلان"),
    ("TAL_001", "Talak", "Bir Lafızla Verilen Üç Talâkın Vukuu", "حكم الطلاق الثلاث بلفظ واحد", "ثلاثا بلفظ واحد|بدعي|رجعية|بائنة"),
    
    # Cinâyât & Hudûd
    ("CIN_001", "Cinayat", "Kısasın Şartları ve Katilin Affı Durumunda Diyet", "شروط القصاص وسقوطه بالعفو والدية", "قصاص|عمد|شبه عمد|دية|عفو"),
    ("HUD_001", "Hudud", "Şüphe ile Hadlerin Düşürülmesi", "درء الحدود بالشبهات", "ادرؤوا الحدود|شبهات|بينة|اقرار")
]

for m_id, kat, bas_tr, bas_ar, pats in KANONIK_MESELELER:
    cur.execute("""
    INSERT INTO fikh_meseleler (mesele_id, ana_bolum, mesele_adi_tr, mesele_adi_ar, anahtar_kalıplar)
    VALUES (?, ?, ?, ?, ?);
    """, (m_id, kat, bas_tr, bas_ar, pats))

conn.commit()
print(f"[+] {len(KANONIK_MESELELER)} adet kanonik fıkıh meselesi ontoloji tablosuna kaydedildi.")

# 4. 95,149 Düğümün Mesele ID'leri ile Eşleştirilmesi
print("\n[*] Düğümler kanonik mesele kimlikleri (mesele_id) ile haritalanıyor...")

cur.execute("SELECT id, kanonik_konu, kitab, bab, fasl, metin_arama FROM fikh_nodes;")
nodes = cur.fetchall()

batch_updates = []
genel_count = 0
assigned_count = 0

for row in tqdm(nodes, desc="Mesele Ataması", unit="node"):
    node_db_id = row[0]
    kanonik_konu = row[1]
    header_text = f"{row[2]} {row[3]} {row[4]} {row[5][:150]}"
    
    assigned_m_id = None
    for m_id, kat, _, _, pat in KANONIK_MESELELER:
        if kat == kanonik_konu and re.search(pat, header_text):
            assigned_m_id = m_id
            break
            
    if not assigned_m_id:
        assigned_m_id = f"{kanonik_konu[:3].upper()}_GENEL"
        genel_count += 1
    else:
        assigned_count += 1
        
    batch_updates.append((assigned_m_id, node_db_id))
    
    if len(batch_updates) >= 5000:
        cur.executemany("UPDATE fikh_nodes SET mesele_id = ? WHERE id = ?;", batch_updates)
        conn.commit()
        batch_updates = []

if batch_updates:
    cur.executemany("UPDATE fikh_nodes SET mesele_id = ? WHERE id = ?;", batch_updates)
    conn.commit()

# 5. Bilgi Grafı (graph_relations) Tablosunun mesele_id ile Zenginleştirilmesi
print("\n[*] Bilgi grafı ilişkileri mesele_id ile bağlanıyor...")
cur.execute("PRAGMA table_info(graph_relations);")
rel_cols = [c[1] for c in cur.fetchall()]
if "mesele_id" not in rel_cols:
    cur.execute("ALTER TABLE graph_relations ADD COLUMN mesele_id TEXT;")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_rel_mesele ON graph_relations(mesele_id);")

cur.execute("""
UPDATE graph_relations 
SET mesele_id = (SELECT n.mesele_id FROM fikh_nodes n WHERE n.node_id = graph_relations.node_id);
""")
conn.commit()

# 6. FTS Tablosunun mesele_id ile Yenilenmesi
cur.execute("DROP TABLE IF EXISTS fikh_fts;")
cur.execute("""
CREATE VIRTUAL TABLE fikh_fts USING fts5(
    node_id UNINDEXED,
    mesele_id,
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
INSERT INTO fikh_fts(rowid, node_id, mesele_id, mezhep, muellif, eser, kanonik_konu, metin_arama, kok_dizini)
SELECT id, node_id, mesele_id, mezhep, muellif, eser, kanonik_konu, metin_arama, kok_dizini FROM fikh_nodes;
""")
conn.commit()

print("\n" + "=" * 80)
print("ONTOLOJİK DENETİM VE DURUM RAPORU:")
cur.execute("SELECT COUNT(*) FROM fikh_nodes WHERE muellif = 'Bilinmeyen Müellif';")
unknowns = cur.fetchone()[0]
print(f"  - Kalan Bilinmeyen Müellif Sayısı : {unknowns} (Hedef: 0)")
print(f"  - Doğrudan Kanonik Mesele Eşleşen : {assigned_count:,}")
print(f"  - Konu Bazlı Genel Mesele Atanan  : {genel_count:,}")

cur.execute("SELECT COUNT(*) FROM graph_relations WHERE mesele_id IS NOT NULL;")
rel_linked = cur.fetchone()[0]
print(f"  - Graf İlişkilerine Bağlanan Düğüm: {rel_linked:,}")
print("=" * 80)

conn.close()
