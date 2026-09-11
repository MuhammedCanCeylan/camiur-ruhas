import os
import sys
import json
import time
import re
from fikh_production_engine import ProductionFikhCompiler, OUTPUT_BOOK_DIR, CHAPTERS_DIR, MASTER_BOOK_PATH

CHECKPOINT_FILE = os.path.join(OUTPUT_BOOK_DIR, "checkpoint.json")

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

DUGUMLER_FAZ_4 = [
    {
        "bolum_id": "01_taharet_kalan",
        "bolum_adi": "Kitâbü't-Tahâret (Kalan Amelî Düğümler)",
        "dosya": "01_taharet.md",
        "meseleler": [
            (41, "Göz veya Kulağa Damlatılan İlacın Abdesti Bozması", "تقطير الدواء في العين والأذن هل ينقض الوضوء", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Göze veya kulağa damlatılan ilaçlar tabii menfezlerden (ön/arka yoldan) çıkmadığı için abdesti bozmaz.",
                "hanefi_hukum": "Kulağa damlatılan ilaç kulak zarı delikse boğaza inebilir; sahih kavilde abdesti bozmaz.",
                "safii_hukum": "İki yoldan çıkmayan hiçbir sıvı abdesti bozmaz.",
                "maliki_hukum": "Abdesti bozan haller ön ve arka yola münhasırdır, damla abdesti bozmaz.",
                "hanbeli_hukum": "Göz ve kulaktan çıkan veya giren maddeler abdesti bozmaz."
            }),
            (42, "Tırnaktaki Oje, Boya ve Yapıştırıcının Gusül ve Abdeste Engeli", "حكم طلاء الأظافر واللاصق والمانع من وصول الماء", {
                "ruhsat_mezhep": "Mâlikî ve Hanefî Zaruret/Umum-ı Belvâ Tahrîci",
                "ruhsat_hukum": "Çıkarılması aşırı meşakkat ve tırnakta zedelenme doğuran maddelerin altı yıkanmış sayılır; meşakkat halinde abdest ve gusül sahihtir.",
                "hanefi_hukum": "Su geçirmeyen katı tabaka temizlenmedikçe abdest ve gusül sahih olmaz; mesleki zaruretler muaftır.",
                "safii_hukum": "İğne ucu kadar yerin kuru kalması guslü ve abdesti bâtıl kılar, mutlak temizlik şarttır.",
                "maliki_hukum": "Zaruret ve çıkarılmasında fahiş zorluk bulunan kabuk ve boyalar affedilir.",
                "hanbeli_hukum": "Suyun temasını engelleyen tabaka kazınmalıdır; meşakkat varsa mesh kıyas edilir."
            }),
            (43, "İdrar veya Gaz Kaçıran (Özür Sahibi) Kimsenin Abdest Kolaylığı", "طهارة المعذور وسلس البول والريح", {
                "ruhsat_mezhep": "Mâlikî Mezhebi (En geniş özür ruhsatı)",
                "ruhsat_hukum": "İdrar kaçırma veya gaz tutamama hali günün çoğunda gayriihtiyari devam ediyorsa, her namaz için abdest yenilemek gerekmez; diğer hadesler olmadıkça abdest devam eder.",
                "hanefi_hukum": "Özür sahibi her farz namaz vakti için yeni abdest alır, vakit çıkınca abdest bozulur.",
                "safii_hukum": "Her bir farz namaz için müstakil abdest alınması şarttır.",
                "maliki_hukum": "Hastalık külfeti sebebiyle akıntı abdesti bozmaz; tek abdestle dilediği kadar farz ve nafile kılabilir.",
                "hanbeli_hukum": "Her namaz vakti için abdest yenilenir; ancak iki namazı cem' etme ruhsatı tanınır."
            }),
            (44, "Diş Dolgusu ve Kaplamasının Gusle ve Abdeste Engeli", "حكم حشو الأسنان وتركيبها في الغسل والوضوء", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Gusülde ağzın içini yıkamak (mazmaza) farz değil sünnettir; dolayısıyla dolgu ve kaplamanın altına su geçmemesi gusle kesinlikle mâni değildir.",
                "hanefi_hukum": "Ağzı yıkamak gusülde farzdır; ancak dolgu bedenle bütünleştiğinden zarureten suyun altına geçmesi aranmaz, gusül tamdır.",
                "safii_hukum": "Ağız ve burun içi zâhirî bedenden sayılmaz; yıkanması sünnettir, gusül sahihtir.",
                "maliki_hukum": "Mazmaza ve istinşak gusülde sünnettir; dolgunun altı gusle zarar vermez.",
                "hanbeli_hukum": "Ağız ve burun bedenden sayılır fakat zaruret bağı sebebiyle dolgu ve protez muaftır."
            })
        ]
    },
    {
        "bolum_id": "02_salat_kalan",
        "bolum_adi": "Kitâbü's-Salât (Kalan Amelî Düğümler)",
        "dosya": "02_salat.md",
        "meseleler": [
            (45, "Rekât Sayısında Şüpheye Düşen Kimsenin Ameli", "الشك في عدد ركعات الصلاة والبناء على اليقين أو التحري", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Galip zanna göre hareket etme ruhsatı)",
                "ruhsat_hukum": "Namazda şüpheye düşen kimse vesvese ehli ise en az rekâtı esas almak yerine kalbinin en çok meylettiği galip zanna göre namazını tamamlar, baştan kılmaz.",
                "hanefi_hukum": "Şüphe ilk kez oluyorsa namazı bozar; tekerrür ediyorsa galip zanna göre tamamlanır ve sehiv secdesi yapılır.",
                "safii_hukum": "Zanna bakılmaz; kesin olan en az rekât (yakîn) esas alınır ve eksik rekât tamamlanır.",
                "maliki_hukum": "En az rekât esas alınarak namaz bina edilir, selâmdan sonra sehiv secdesi yapılır.",
                "hanbeli_hukum": "Yalnız kılan yakîn (en az) üzerine bina eder ve sehiv secdesi yapar."
            }),
            (46, "Hareket Halindeki Araçta (Otobüs, Uçak, Tren) Farz Namaz Kılmak", "صلاة الفريضة على الراحلة والقطار والطائرة لعذر", {
                "ruhsat_mezhep": "Hanbelî ve Mâlikî Zaruret Ruhsatı",
                "ruhsat_hukum": "Vaktin çıkması korkusu ve aracın durdurulamaması halinde, kıbleye yönelme imkânı ölçüsünde oturarak veya îma ile farz namaz kılınabilir; sonradan kaza gerekmez.",
                "hanefi_hukum": "Zaruret olmaksızın binek üzerinde farz caiz değildir; inme imkânı yoksa kılınır ancak inince iadesi ihtiyattır.",
                "safii_hukum": "Hürmet-i vakit için kılınır, fakat araç durduğunda namaz mutlaka kaza edilir.",
                "maliki_hukum": "Zaruret ve vaktin fevti halinde oturarak ima ile kılınan namaz sahihtir, iade gerekmez.",
                "hanbeli_hukum": "Meşakkat ve can/mal güvenliği sebebiyle binek üzerinde kılınan farz kâfidir, iade edilmez."
            }),
            (47, "Sehiv Secdesini Unutup Selâm Verip Çıkan Kimsenin Namazı", "نسيان سجود السهو حتى طال الفصل أو خرج من المسجد", {
                "ruhsat_mezhep": "Şâfiî Mezhebi (Sehiv secdesinin sünnet olması)",
                "ruhsat_hukum": "Sehiv secdesi vacip değil sünnettir; selâmdan sonra unutulup namazdan çıkılsa dahi namaz bütünüyle sahihtir, kaza gerekmez.",
                "hanefi_hukum": "Sehiv secdesi vaciptir; unutulup konuşulursa secdesi düşer fakat namaz tahrîmen mekruh olarak geçerlidir.",
                "safii_hukum": "Sehiv secdesi sünnettir; terki veya unutulması namazın sıhhatine zarar vermez.",
                "maliki_hukum": "Selâmdan sonraki secde (ba'dî) unutulursa hatırlanınca yapılır, namaz bozulmaz.",
                "hanbeli_hukum": "Secde vaciptir; ancak fasıla uzarsa af kabul edilir, namaz iptal olmaz."
            }),
            (48, "Cuma Namazının Sahih Olması İçin Gereken Cemaat Sayısı", "العدد المشترط لصحة صلاة الجمعة", {
                "ruhsat_mezhep": "Hanefî Mezhebi (İmam Ebû Yûsuf ve Muhammed - 3 kişi) ve İmam Züfer (1 kişi)",
                "ruhsat_hukum": "Cuma namazının kılınması için 40 kişi şart değildir; imam haricinde 3 mükellef cemaat ile cuma namazı sahih olur.",
                "hanefi_hukum": "İmam hariç en az 3 akıl baliğ hür erkek cemaat ile cuma namazı kılınır.",
                "safii_hukum": "Cumanın sahih olması için o beldede mukim 40 hür mükellefin bulunması şarttır.",
                "maliki_hukum": "Cuma cemaati için köy veya şehirde en az 12 mukim mükellef bulunmalıdır.",
                "hanbeli_hukum": "Cuma için 40 kişinin hazır bulunması şarttır, eksik olursa öğle kılınır."
            })
        ]
    },
    {
        "bolum_id": "17_cenaiz",
        "bolum_adi": "Kitâbü'l-Cenâiz (Cenaze Hükümleri)",
        "dosya": "17_cenaiz.md",
        "meseleler": [
            (49, "Cenaze Namazında Fatiha Sûresi Okumanın Hükmü", "قراءة الفاتحة في صلاة الجنازة هل هي ركن أو دعاء", {
                "ruhsat_mezhep": "Hanefî ve Mâlikî Mezhepleri (Fatiha'nın rükün olmaması)",
                "ruhsat_hukum": "Cenaze namazı sırf dua ve şefaatten ibarettir; Fatiha okumak farz veya rükün değildir, dua kastıyla okunabilir veya sadece salavat ve dualarla namaz tamamlanır.",
                "hanefi_hukum": "Kıraat kastıyla Fatiha okunmaz; dua niyetiyle okunması caizdir, asıl olan duadır.",
                "safii_hukum": "İlk tekbirden sonra Fatiha okumak namazın sıhhat rüknüdür, Fatihasız cenaze namazı bâtıldır.",
                "maliki_hukum": "Cenaze namazında Fatiha okumak mekruhtur; tekbirler arası sadece dua edilir.",
                "hanbeli_hukum": "İlk tekbirden sonra eûzü çekilerek gizlice Fatiha okunması farzdır."
            }),
            (50, "Ölünün Arkasından Iskat-ı Salât ve Devir Muamelesi", "إسقاط الصلاة عن الميت والدور بالمال والحيل", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî - Devrin bâtıl olması)",
                "ruhsat_hukum": "Namaz bedenî bir ibadettir; para çevirerek (devir hilesiyle) kılınmamış namazların borcunun düşürülmesi dinde asılsızdır, caiz değildir. Vefat edenin arkasından yapılacak en hafif ve sahih amel doğrudan istiğfar, dua ve sevabı bağışlanan sadakadır.",
                "hanefi_hukum": "Oruç fidyeye kıyas edilerek namaz için vasiyet edilmişse ıskat caiz görülmüş, yetersiz mal için devir hilesi üretilmiştir.",
                "safii_hukum": "Namaz bedenî ibadettir; başkası adına ne kaza edilir ne de fidye/para ile borcu düşürülür, devir bâtıldır.",
                "maliki_hukum": "Namazın ıskatı ve devri asla caiz değildir; ölünün namaz borcu malla düşmez.",
                "hanbeli_hukum": "Namazın hiçbir şekilde ıskatı ve mali devri yoktur; sadece oruç için fidye vardır."
            })
        ]
    },
    {
        "bolum_id": "03_siyam_kalan",
        "bolum_adi": "Kitâbü's-Sıyâm (Kalan Amelî Düğümler)",
        "dosya": "03_siyam.md",
        "meseleler": [
            (51, "Yolculukta Oruç Tutmak mı Yoksa Ruhsatı Kullanıp Yemek mi Efdaldir?", "الأفضل في السفر الصوم أو الفطر للمسافر", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (Ruhsatı kullanmanın mutlak efdaliyeti)",
                "ruhsat_hukum": "Seferde meşakkat olmasa dahi oruç tutmayıp yemek ve sonradan kaza etmek sünnete daha uygundur ve efdaldir; Allah'ın ruhsatını kabul etmek esastır.",
                "hanefi_hukum": "Zarar ve aşırı meşakkat yoksa seferde oruç tutmak yemeye nispetle daha efdaldir.",
                "safii_hukum": "Meşakkat yoksa oruç tutmak efdaldir; meşakkat varsa açmak sünnettir.",
                "maliki_hukum": "Zarar vermeyen yolculukta oruç tutmak daha faziletlidir.",
                "hanbeli_hukum": "Meşakkat olmasa bile seferde oruç bozmak ve ruhsatı almak kesinlikle efdaldir."
            }),
            (52, "Cünüp Olarak Sabahlayanın Orucunun Sıhhati", "أصبح جنبا في رمضان هل يصح صومه", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Cumhur)",
                "ruhsat_hukum": "Fecr-i sâdık doğduğu anda cünüp olan kimsenin orucu kesinlikle sahihtir; sabah namazı için gusletmesi yeterlidir, oruca hiçbir halel gelmez.",
                "hanefi_hukum": "Guslü imsaktan sonraya bırakmak orucu bozmaz, oruç sahihtir.",
                "safii_hukum": "Resulullah cünüp olarak sabahlardı ve orucuna devam ederdi; oruç tamdır.",
                "maliki_hukum": "Cünüplük orucun sıhhat şartı değildir; oruç sahihtir.",
                "hanbeli_hukum": "Fecir vaktinde cünüp bulunmak oruca zarar vermez, ittifakla sahihtir."
            })
        ]
    }
]

def main():
    print("=" * 80)
    print("[*] FAZ 4: EKSİKSİZ AMELÎ DÜĞÜMLER MOTORU (MESELE 041 - 052)")
    print("=" * 80)

    compiler = ProductionFikhCompiler()
    completed = load_checkpoints()
    print(f"[+] Mevcut doğrulanmış mesele sayısı: {len(completed)}")

    for bolum in DUGUMLER_FAZ_4:
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
                print(f"        [✓] Tamamlandı ({elapsed:.1f} sn).")
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
        ("11_muamelat_muasira.md", "KİTÂBÜ'L-MUÂMELÂTİ'L-MUÂSIRA (ÇAĞDAŞ FİNANS VE SÖZLEŞMELER)")
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
    print(f"[+] FAZ 4 BAŞARIYLA TAMAMLANDI:")
    print(f"    Master Kitap: {MASTER_BOOK_PATH}")
    print(f"    Toplam Boyut: {size_kb:.2f} KB")
    print(f"    Toplam Mesele Sayısı: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
