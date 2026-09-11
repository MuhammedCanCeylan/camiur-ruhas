import os
import sys
import json
import time
import re
from neuro_symbolic_engine import NeuroSymbolicFikhEngine, OUTPUT_BOOK_DIR, CHAPTERS_DIR, MASTER_BOOK_PATH, CHECKPOINT_FILE

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

DUGUMLER_FAZ_6 = [
    {
        "bolum_id": "04_buyu_ileri",
        "bolum_adi": "Kitâbü'l-Büyû' (İleri Ticari Düğümler)",
        "dosya": "04_buyu.md",
        "meseleler": [
            (68, "Fiyatı Belirlenmeden Piyasa Rayicine Bırakılan Satışlar (Bey'u'l-Musterse)", "البيع بسعر السوق دون تحديد الثمن وقت العقد", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (İbn Teymiyye ve İbnü'l-Kayyim Tahrîci)",
                "ruhsat_hukum": "Fiyatı akit esnasında kuruşu kuruşuna telaffuz edilmeyip 'piyasada/borsada o gün neyse o fiyattan' denilerek yapılan düzenli mal alımları örfe ve maslahata binaen sahihtir; cehalet-i yesîre (önemsiz belirsizlik) akdi bozmaz.",
                "hanefi_hukum": "Akit anında semenin (fiyatın) tam olarak tayin edilmemesi garar doğurur, akit fâsittir.",
                "safii_hukum": "Fiyatın akit anında kesin bilinmemesi satışı kökten bâtıl kılar.",
                "maliki_hukum": "Piyasa fiyatı müstakar ve bilinen bir rayiç ise caiz sayan rivayetler mevcuttur.",
                "hanbeli_hukum": "İnsanların teamülüne ve piyasa rayicine göre yapılan satışlar geçerlidir."
            }),
            (69, "Bir Malı Henüz Teslim Almadan (Kabz Etmeden) Başkasına Satmak", "بيع المبيع قبل القبض في المنقول والعقار", {
                "ruhsat_mezhep": "Mâlikî Mezhebi (Yiyecek dışı mallarda kabz şartının aranmaması)",
                "ruhsat_hukum": "Ölçü ve tartıyla satılan temel gıda maddeleri haricindeki menkul mallar, gayrimenkuller ve hisseler, fiziksel olarak depoya girmeden veya teslim alınmadan önce kârıyla başkasına satılabilir.",
                "hanefi_hukum": "Gayrimenkulün kabzdan önce satışı caizdir; menkul malların kabz edilmeden satışı ise bâtıldır.",
                "safii_hukum": "İster gayrimenkul ister menkul olsun, kabz edilmeyen hiçbir malın satışı kesinlikle caiz değildir.",
                "maliki_hukum": "Kabz yasağı sadece ribevî yiyeceklere mahsustur; diğer malların kabz öncesi satışı sahihtir.",
                "hanbeli_hukum": "Ölçü, tartı ve sayıyla satılan mallarda kabz şarttır; diğerlerinde kabz aranmaz."
            }),
            (70, "Taksitli Satışta Vade Farkı Koymanın Hükmü", "الزيادة في الثمن لأجل الأجل والتقسيط", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Cumhur)",
                "ruhsat_hukum": "Akit esnasında peşin veya vadeli seçeneklerinden biri kesinleştirilip tek bir fiyatta mutabık kalındığı sürece, taksit süresi uzadıkça peşin fiyatın üzerinde bir meblağ belirlemek ittifakla helaldir; ribâ sayılmaz.",
                "hanefi_hukum": "Vade karşılığında fiyatın artırılması caizdir; akitte tek fiyat bağlanmalıdır.",
                "safii_hukum": "Peşin 100, vadeli 120 liralık fiyattan biri mecliste kesinleşirse akit sahihtir.",
                "maliki_hukum": "Vadeye pay ayrılması ticaretin doğasındandır, caizdir.",
                "hanbeli_hukum": "Taksitli satışta vade sebebiyle fiyatın yüksek tutulması ittifakla mubahtır."
            })
        ]
    },
    {
        "bolum_id": "07_aile_ileri",
        "bolum_adi": "Kitâbü'n-Nikâh ve't-Talâk (İleri Aile Düğümleri)",
        "dosya": "07_nikah.md",
        "meseleler": [
            (71, "Boşanan Kadının İddet Nafakası ve Mesken Hakkı", "نفقة المعتدة وسكناها في البائن والرجعي", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (Bâin talakta nafakanın düşmesi) ve Hanefî (Kadın lehine nafaka)",
                "ruhsat_hukum": "Üç talakla (bâin) boşanan hâmile olmayan kadına Hanbelî mezhebine (Fâtıma bnt. Kays hadisi) göre kocasından iddet nafakası ve mesken hakkı terettüp etmez; koca bu mali külfetten muaftır.",
                "hanefi_hukum": "Ric'î veya bâin her türlü boşanan kadına iddet süresince nafaka ve barınma sağlamak kocaya vaciptir.",
                "safii_hukum": "Bâin talakla boşanan kadına sadece mesken hakkı vardır, nafaka hakkı yoktur (hâmile değilse).",
                "maliki_hukum": "Bâin boşanan kadın hâmile değilse yalnız barınma hakkı verilir, nafaka düşer.",
                "hanbeli_hukum": "Bâin talakta hâmilelik yoksa ne nafaka ne de mesken vaciptir; koca tamamen serbesttir."
            }),
            (72, "Kocanın İktidarsızlığı veya Ciddi Hastalığı Sebebiyle Kadının Fesih Hakkı", "فسخ النكاح للعيوب الجنسية والمرضية في الزوج", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Kocada cinsel iktidarsızlık, cüzzam, delilik veya bulaşıcı ağır bir hastalık bulunması halinde kadın hâkimden nikâhın derhal feshini talep edebilir; 1 yıl mühlet bekleme zorunluluğu yoktur.",
                "hanefi_hukum": "Sadece cinsî iktidarsızlıkta kadına fesih hakkı tanınır ve kocaya 1 yıl tedavi mühleti verilir; diğer hastalıklarda kadının fesih hakkı yoktur.",
                "safii_hukum": "Evliliğin maksadını engelleyen her ağır hastalık ve kusur sebebiyle kadın nikâhı feshettirebilir.",
                "maliki_hukum": "Zarar ve kusur bulunan hallerde kadının fesih talebi kabul edilir.",
                "hanbeli_hukum": "Karı-kocadan birinde bulunan ayıp ve kusurlar diğer tarafa fesih hakkı bahşeder."
            }),
            (73, "Kocası Kaybolan (Mefkûd) Kadının Yeniden Evlenme Süresi", "عدة زوجة المفقود والمدة المشترطة لفسخ نكاحها", {
                "ruhsat_mezhep": "Mâlikî ve Hanbelî Mezhepleri (Hz. Ömer tahrîci - 4 yıl bekleme)",
                "ruhsat_hukum": "Kocasından hiçbir haber alınamayan kadın, 4 yıl araştırma süresinden sonra vefat iddeti (4 ay 10 gün) bekleyerek başkasıyla evlenebilir; akranlarının ölümünü (70-90 yaş) beklemek zorunda değildir.",
                "hanefi_hukum": "Mefkûd ancak akranlarının vefat edeceği yaşa (genellikle 90 yaş) ulaştığında ölmüş sayılır; o güne kadar kadın evlenemez.",
                "safii_hukum": "Eski kavilde 4 yıl; yeni kavilde ise ölüm kesinleşene veya kadı hükmedene kadar evlenemez.",
                "maliki_hukum": "Kayıp kocasını 4 yıl bekleyen kadın, iddetini tamamlayıp meşru şekilde başkasıyla evlenebilir.",
                "hanbeli_hukum": "Helak olma ihtimali yüksek yerde kaybolmuşsa 4 yıl sonra hükmen vefat kabul edilir ve kadın serbest kalır."
            })
        ]
    },
    {
        "bolum_id": "16_tib_gunluk",
        "bolum_adi": "Kitâbü't-Tıbb ve'l-İstihâle (Tıbbî ve Günlük Düğümler)",
        "dosya": "16_tib_gunluk.md",
        "meseleler": [
            (74, "Kimyasal Dönüşüm (İstihâle) Geçiren Maddelerin (Jelatin, Domuz Katkıları) Temizliği", "حكم الاستحالة الكيميائية للعين النجسة كالجيلاتين والخنزير", {
                "ruhsat_mezhep": "Hanefî ve Mâlikî Mezhepleri (İstihâle ile mutlak temizlenme)",
                "ruhsat_hukum": "Necis bir madde (domuz kemiği, leş vb.) kimyasal ve fiziksel bir süreçten geçerek zâtını ve niteliğini tamamen kaybedip yeni bir maddeye dönüşmüşse (jelatin, sabun vb.) temiz ve helal hale gelir; tüketimi caizdir.",
                "hanefi_hukum": "İstihâle necaseti temizler; şarabın sirkeye, tezeğin küle, domuzun tuza dönüşmesi gibi zâtı değişen her şey temizdir.",
                "safii_hukum": "İstihâle kural olarak temizlemez; yalnızca kendiliğinden sirkeleşen şarap ile tabaklanan deri temizlenir.",
                "maliki_hukum": "Kimyasal dönüşüm sonucu niteliği ve adı değişen madde temiz hükmünü alır.",
                "hanbeli_hukum": "Klasik mezhepte istihale temizlemez; İbn Teymiyye tahrîcine göre ise zâtı değişen madde temizdir."
            }),
            (75, "Anne Karnındaki Bebeğin Kürtaj Edilmesinin (Iskāt-ı Cenîn) Sınırı", "إسقاط الجنين لعذر قبل نفخ الروح وبعده", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Ruh üflenmeden önceki 120 gün ruhsatı)",
                "ruhsat_hukum": "Tıbbî bir zorunluluk, annenin hayatî tehlikesi veya ağır bir anomali durumunda, cenine ruh üflenmeden önce (ilk 120 gün / 17 hafta içinde) kürtaj yapılması caizdir; cinayet sayılmaz.",
                "hanefi_hukum": "Meşru bir mazeret ve özür bulunması şartıyla ilk 120 gün içinde kürtaj caizdir.",
                "safii_hukum": "Nutfenin rahme yerleşmesinden itibaren kürtaj haramdır; ancak 40 günden önce caiz gören zayıf kavil vardır.",
                "maliki_hukum": "Sperm rahme ulaştığı andan itibaren kürtaj mutlak surette haramdır.",
                "hanbeli_hukum": "İlk 40 gün içinde ilaçla düşürmek mubahtır; 40 günden sonra caiz görülmez."
            })
        ]
    }
]

def main():
    print("=" * 80)
    print("[*] NÖRO-SEMBOLİK MOTOR İLE DERLEME: MESELE 068 - 075")
    print("=" * 80)

    compiler = NeuroSymbolicFikhEngine()
    completed = load_checkpoints()
    print(f"[+] Başlangıçtaki Doğrulanmış Mesele Sayısı: {len(completed)}")

    for bolum in DUGUMLER_FAZ_6:
        bolum_adi = bolum["bolum_adi"]
        dosya_adi = bolum["dosya"]
        dosya_yolu = os.path.join(CHAPTERS_DIR, dosya_adi)

        print(f"\n[+] BÖLÜM İŞLENİYOR: {bolum_adi}")
        chapter_pages = []

        for m_id, m_baslik, m_sorgu, m_canon in bolum["meseleler"]:
            key = f"{bolum['bolum_id']}_{m_id:03d}"
            
            if key in completed:
                print(f"    [>] Mesele {m_id:03d} atlandı (Daha önce derlenmiş).")
                continue

            print(f"    [*] Mesele {m_id:03d} Tahrîc Ediliyor: {m_baslik}...")
            start_t = time.time()
            page_md = compiler.compile_issue_page(bolum_adi, m_id, m_baslik, m_sorgu, m_canon)
            
            if page_md:
                chapter_pages.append(page_md)
                completed.add(key)
                save_checkpoint(completed)
                elapsed = time.time() - start_t
                print(f"        [✓] İzole RAG ve Sembolik Doğrulama Başarılı ({elapsed:.1f} sn).")
            else:
                print(f"        [-] HATA: Mesele {m_id:03d} korpusta bulunamadı.")

        if chapter_pages:
            mode = "a" if os.path.exists(dosya_yolu) else "w"
            with open(dosya_yolu, mode, encoding="utf-8") as bf:
                if mode == "w":
                    bf.write(f"# {bolum_adi.upper()}\n\n")
                for p in chapter_pages:
                    bf.write(p + "\n\n")

    # Master Kitap Dosyasını Fihristle Birlikte Yeniden Kurma
    print("\n[*] Master Külliyat Fihristle Birleştiriliyor...")
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
        ("16_tib_gunluk.md", "KİTÂBÜ'T-TIBB VE'L-İSTİHÂLE (SAĞLIK VE GÜNLÜK YAŞAM)")
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
    print(f"[+] FAZ 6 BAŞARIYLA TAMAMLANDI:")
    print(f"    Master Kitap: {MASTER_BOOK_PATH}")
    print(f"    Toplam Boyut: {size_kb:.2f} KB")
    print(f"    Toplam Mesele Sayısı: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
