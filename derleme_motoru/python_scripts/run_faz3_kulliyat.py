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

FAZ_3_PLANI = [
    {
        "bolum_id": "09_kurban",
        "bolum_adi": "Kitâbü'l-Udhiyye ve'z-Zebâyih (Kurban ve Kesim Hükümleri)",
        "dosya": "09_kurban.md",
        "meseleler": [
            (29, "Kurban Kesmenin Dînî Hükmü (Vacip mi, Sünnet-i Müekkede mi?)", "حكم الأضحية بين الوجوب والسنة المؤكدة", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Kurban kesmek zengin/mukim için dahi farz veya vacip değildir; sünnet-i müekkededir. Maddi gücü yeten kişi kesmediği takdirde günahkâr olmaz, kazası gerekmez.",
                "hanefi_hukum": "Nisaba mâlik mukim müslümana kurban kesmek vaciptir; terk eden günahkâr olur.",
                "safii_hukum": "Kifâî veya aynî müekked sünnettir; terk edilmesinde günah ve kaza yoktur.",
                "maliki_hukum": "Gücü yetene müekked sünnettir, vacip değildir.",
                "hanbeli_hukum": "Zengin olan için dahi sünnettir, terki caizdir."
            }),
            (30, "Büyükbaş Kurbana Ortak Olanların Niyet Farklılığı (Et ve Kurban Ayrımı)", "اشتراك سبعة في بدنة أو بقرة مع اختلاف النوايا", {
                "ruhsat_mezhep": "Şâfiî Mezhebi (Niyet bağımsızlığı ruhsatı)",
                "ruhsat_hukum": "Büyükbaş hayvana ortak olan 7 kişiden bazısı kurban, bazısı akîka, bazısı adak, hatta bazısı sadece kasaplık et niyeti taşısa bile diğer ortakların kurbanı sahihtir ve geçerlidir.",
                "hanefi_hukum": "Ortakların tamamı ibadet/kurbet niyeti taşımalıdır; biri sırf et kastederse hiçbirinin kurbanı sahih olmaz.",
                "safii_hukum": "Her bir hisse müstakildir; ortakların niyetinin farklı olması diğer hisselerin sıhhatine zarar vermez.",
                "maliki_hukum": "Büyükbaşta satın almadan önce kurbet ortaklığı şarttır; et kastıyla ortaklık kurbanı ifsad eder.",
                "hanbeli_hukum": "Ortakların niyetlerinin nafile, vacip veya akika olması caizdir; kurbet kastı esastır."
            }),
            (31, "Hayvan Kesiminde Kasten veya Unutarak Besmelenin Terki", "ترك التسمية على الذبيحة عمدا أو سهوا", {
                "ruhsat_mezhep": "Şâfiî Mezhebi (Zebîhanın mutlak helalliği)",
                "ruhsat_hukum": "Müslüman bir kimse hayvanı keserken besmeleyi unutarak veya kasten terk etse dahi kesilen hayvanın eti helaldir ve temizdir; besmele sünnettir.",
                "hanefi_hukum": "Unutarak terk edilirse helaldir; fakat kasten terk edilirse hayvan murdar olur, eti yenmez.",
                "safii_hukum": "Besmele sünnettir; müslümanın kalbindeki iman ismi kesimi helal kılmaya yeterlidir, kasten terk edilse de yenir.",
                "maliki_hukum": "Kasten veya unutularak terk edilirse meşhur kavle göre hayvan yenmez.",
                "hanbeli_hukum": "Unutarak terk caizdir; kasten terk edilen hayvan leş hükmündedir."
            }),
            (32, "Mekanik / Otomatik Kesim ve Bant Sisteminde Tek Besmelenin Hükmü", "الذبح الآلي الميكانيكي بالتسمية الواحدة", {
                "ruhsat_mezhep": "Çağdaş Fıkıh Heyetleri ve Hanefî/Şâfiî Tahrîci",
                "ruhsat_hukum": "Otomatik kesim makinelerinde düğmeye basan veya bıçağı çalıştıran müslümanın düğmeye basarken çektiği tek besmele, banttan kesintisiz geçen aynı parti hayvanların tamamı için geçerlidir.",
                "hanefi_hukum": "Aynı mecliste ve tek fiille hareket eden kesici alet tek bir eylem sayılır, tek besmele kâfidir.",
                "safii_hukum": "Her hayvan için ayrı niyet ve tesmiye sünnet olmakla beraber fiilin birliği halinde cevaz vardır.",
                "maliki_hukum": "Bizzat el ile kesim ve her hayvana tesmiye esastır; mekanik sistemde şüphe vardır.",
                "hanbeli_hukum": "Bıçağı sevk edenin iradesi ve tek fiili devam ettiği müddetçe av aletine kıyasen caizdir."
            })
        ]
    },
    {
        "bolum_id": "10_eyman",
        "bolum_adi": "Kitâbü'l-Eymân ve'n-Nüzûr (Yeminler ve Adaklar)",
        "dosya": "10_eyman.md",
        "meseleler": [
            (33, "Geçmişe Dair Yalan Yere Yemin Etmek (Yemîn-i Gamûs) ve Keffareti", "اليمين الغموس وحكم وجوب الكفارة فيها", {
                "ruhsat_mezhep": "Hanefî ve Mâlikî Mezhepleri (Mali keffaretin düşmesi)",
                "ruhsat_hukum": "Geçmişte bilerek yalan yere edilen yemîn-i gamûs için mali keffaret (oruç, köle azadı, fakir doyurma) gerekmez; günahı keffaretle temizlenmeyecek kadar büyüktür, tek çaresi pişmanlık, nasuh tevbe ve gasbedilen hakkı sahibine iade etmektir.",
                "hanefi_hukum": "Gamûs yeminine keffaret terettüp etmez; sadece tevbe ve istiğfar vaciptir.",
                "safii_hukum": "Yemin yalandır fakat ism-i celal anıldığı için 10 fakiri doyurmak veya 3 gün oruç tutmak suretiyle keffaret farzdır.",
                "maliki_hukum": "Gamûs yemininin keffareti yoktur; vebali büyüktür, tevbe gerekir.",
                "hanbeli_hukum": "İki rivayetten birine göre keffaret gerekmez, diğerine göre ise keffaret vaciptir."
            }),
            (34, "Haram veya Masiyet Üzerine Yapılan Adakların (Nezir) Hükmü", "نذر المعصية هل ينعقد وتجب فيه كفارة يمين", {
                "ruhsat_mezhep": "Şâfiî ve Mâlikî Mezhepleri (Mutlak hükümsüzlük)",
                "ruhsat_hukum": "Haram, günah veya dinen caiz olmayan bir fiili (örneğin akraba ile ilişkiyi kesmek, içki içmek vb.) adamak kesinlikle bâtıldır; bu adağı yerine getirmek haram olduğu gibi herhangi bir yemin keffareti de gerekmez.",
                "hanefi_hukum": "Masiyet adağı yerine getirilmez; ancak yemin akdedilmiş sayıldığından yemin keffareti ödenir.",
                "safii_hukum": "Masiyet adağı akdedilmemiştir, kökten bâtıldır; hiçbir keffaret gerekmez.",
                "maliki_hukum": "Günah adağı hükümsüzdür, ifa edilmez ve keffaret terettüp etmez.",
                "hanbeli_hukum": "Adağın ifası haramdır; fakat 'Günah adağının keffareti yemin keffaretidir' hadisi gereği keffaret ödenir."
            })
        ]
    },
    {
        "bolum_id": "11_muamelat_muasira",
        "bolum_adi": "Kitâbü'l-Muâmelâti'l-Muâsıra (Çağdaş Finans ve Sözleşmeler)",
        "dosya": "11_muamelat_muasira.md",
        "meseleler": [
            (35, "Enflasyonist Ortamda Paranın Değer Kaybının Borca İlavesi", "ربط الديون بتغير القوة الشرائية ومعدل التضخم", {
                "ruhsat_mezhep": "İmâm Ebû Yûsuf Tahrîci ve Mâlikî/Karafî usûlü",
                "ruhsat_hukum": "Aşırı enflasyon veya paranın değerini fahiş şekilde yitirmesi durumunda, borçlunun borcu verildiği gündeki alım gücü (altın veya ortak sepet değeri) üzerinden ödemesi zulmü ve zararı önlemek adına caizdir ve faiz sayılmaz.",
                "hanefi_hukum": "İmam Ebû Hanîfe'ye göre borç misliyle (sayısal miktarıyla) ödenir; Ebû Yûsuf'a göre ise tedavülden düşme/aşırı değer kaybında akit günündeki kıymeti ödenir.",
                "safii_hukum": "Borç alınan paranın nominal sayısı ne ise o iade edilir; alım gücü farkı talep etmek faiz şüphesi doğurur.",
                "maliki_hukum": "Fahiş zaruret ve gabn-i fahiş durumunda kıymetin tazmini maslahat gereğidir.",
                "hanbeli_hukum": "Para tedavülden tamamen kalkmadıkça nominal değer esastır; ancak karşılıklı sulh caizdir."
            }),
            (36, "Faiz Bulaşığı Olan Şirket Hisselerine Yatırım ve Temettü Arındırması", "تداول أسهم الشركات المساهمة المختلطة بالربا وتطهيرها", {
                "ruhsat_mezhep": "Çağdaş İctihad Heyetleri (AAOIFI ve Diyanet Kararları)",
                "ruhsat_hukum": "Ana faaliyet alanı helal olan (üretim, teknoloji, gıda vb.) ancak faizli kredi kullanan veya mevduat geliri olan şirketlerin hisselerini almak caizdir; elde edilen temettüden haram faiz oranı kadarı hesaplanıp sevap beklenmeksizin fakirlere tasadduk edilir (arındırma).",
                "hanefi_hukum": "Şirketin sermayesine ve akitlerine haram karışması sedd-i zerâi' gereğince mekruhtur; arındırma ile cevaz verilir.",
                "safii_hukum": "Akit ve sermaye bütünüyle temiz olmalıdır; faiz bulaşığı olan şirkete hisse ortaklığı caiz değildir.",
                "maliki_hukum": "Haram unsurların azınlıkta kalması ve ana gayenin helal olması halinde umum-ı belva ruhsatı tanınır.",
                "hanbeli_hukum": "Haram gelir ayrıştırılıp tasadduk edilmek şartıyla hisse alım satımı caiz görülmüştür."
            }),
            (37, "Banka Maaş Promosyonunun Hükmü ve Harcanması", "حكم فوائد البنوك وحوافز الرواتب المسماة بالبروموسيون", {
                "ruhsat_mezhep": "Müteahhirîn Fukahâsı (İkrah/Zaruret ve Mülkiyet Tahkiki)",
                "ruhsat_hukum": "Devlet veya işverenin zorunlu olarak maaşı bankaya yatırması sonucu verilen promosyon faiz şüphesi taşır; asıl olan sevap beklenmeksizin ihtiyaç sahiplerine verilmesidir. Ancak memur/çalışan bizzat muhtaç ve borçlu ise bunu kendi zaruri ihtiyaçları için harcayabilir.",
                "hanefi_hukum": "Şüpheli ve haram yoldan gelen malın mülkiyeti sabit olmaz, tasadduk edilmesi vaciptir; yoksul ise tüketebilir.",
                "safii_hukum": "Faiz gelirinden hiçbir surette kişisel menfaat temin edilemez; kamu yararına veya fakirlere terk edilir.",
                "maliki_hukum": "Kamu maslahatına veya zaruret halindeki müslümanın ihtiyacına sarf edilir.",
                "hanbeli_hukum": "Haram malın sahibi bilinmiyorsa amme menfaatine sarf edilir; bizzat muhtaç olan istifade edebilir."
            }),
            (38, "Ticari Sözleşmelerde Cezai Şart ve Gecikme Bedelinin Sıhhati", "الشرط الجزائي في العقود والتعويض عن الضرر المالي", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (Akit serbestisi ve şartlara riayet)",
                "ruhsat_hukum": "Borç para akitleri hariç olmak üzere, eser sözleşmesi, inşaat ve teslimat taahhütlerinde işin gecikmesinden doğan fiili zararı karşılamak üzere önceden belirlenen cezai şart sahihtir ve talep edilebilir.",
                "hanefi_hukum": "Mali ceza (ta'zîr bi'l-mâl) kural olarak caiz değildir; ancak istisnâ' akdinde örf gereği gecikme indirimi caizdir.",
                "safii_hukum": "Borçtan veya akitten kaynaklanan ceza şartı garar ve faiz şüphesi taşır, bâtıldır.",
                "maliki_hukum": "Fiili zararı aşmayan makul tazminat ve cezai şartlar maslahat gereği geçerlidir.",
                "hanbeli_hukum": "'Müslümanlar şartlarına bağlıdırlar' nassı gereği haramı helal kılmayan cezai şartlar geçerlidir."
            }),
            (39, "Kripto Varlıkların ve Dijital Paraların Fıkhî Mal Niteliği", "حكم العملات الرقمية والمشفرة والتعامل بها", {
                "ruhsat_mezhep": "Çağdaş Hanefî/Mâlikî Örf ve Semeniyet Tahrîci",
                "ruhsat_hukum": "Toplumda değişim aracı olarak kabul gören, arkasında meşru bir blokzincir teknolojisi ve piyasa değeri bulunan dijital varlıklar mütekavvim mal ve semen (para) hükmündedir; alım satımı ve zekâtı caizdir.",
                "hanefi_hukum": "Örf ve teamülde insanlar arasında mübadele aracı (semen-i örfî) olarak kabul edilen her şey para hükmündedir.",
                "safii_hukum": "Gözle görülmeyen ve zâtı bulunmayan dijital varlıklarda garar ve cehalet baskındır, mal sayılmaz.",
                "maliki_hukum": "İnsanların mal edindiği ve ziyan olduğunda tazmin ettirdiği her menfaat ve değer maldır.",
                "hanbeli_hukum": "Menfaati mubah olan ve piyasada kıymeti bulunan her nesne satış akdine konu olabilir."
            }),
            (40, "Bir Akit İçinde İki Satış ve Şart Birleştirmek (Bey'ateyn fî Bey'a)", "نهى عن بيعتين في بيعة والجمع بين عقدين مختلفين", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (İmam Ahmed b. Hanbel ve İbn Teymiyye)",
                "ruhsat_hukum": "Akitlerin birbirine bağlanması faize (ribâ) veya belirsizliğe (garar) yol açmadığı sürece, tek sözleşmede birden fazla mubah şart ve muamele birleştirilebilir (örneğin kiralama ve mülkiyet vaadi/finansal kiralama).",
                "hanefi_hukum": "Akit içinde akit veya akde yabancı şart koşmak fâsittir; ancak örfleşmiş şartlar müstesnadır.",
                "safii_hukum": "Bir akitte iki satış kesinlikle bâtıldır; akitlerin birbirinden tamamen tecrit edilmesi şarttır.",
                "maliki_hukum": "Ribâya vesile olmayan ve garar içermeyen şartlar geçerlidir, sedd-i zerâi' gözetilir.",
                "hanbeli_hukum": "Akitlerde asıl olan ibâhadır; haram bir illet içermeyen şartların tamamı bağlayıcıdır."
            })
        ]
    }
]

def main():
    print("=" * 80)
    print("[*] FAZ 3: KÜLLİYAT GENİŞLETME MOTORU (MESELE 029 - 040)")
    print("=" * 80)

    compiler = ProductionFikhCompiler()
    completed = load_checkpoints()
    print(f"[+] Mevcut tamamlanmış mesele sayısı: {len(completed)}")

    for bolum in FAZ_3_PLANI:
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

    # Çoklu ayraçları temizle
    master_full = re.sub(r'(\n---\n)+', '\n\n---\n\n', master_full)

    with open(MASTER_BOOK_PATH, "w", encoding="utf-8") as mf:
        mf.write(master_full)

    size_kb = os.path.getsize(MASTER_BOOK_PATH) / 1024
    print("=" * 80)
    print(f"[+] FAZ 3 BAŞARIYLA TAMAMLANDI:")
    print(f"    Master Kitap: {MASTER_BOOK_PATH}")
    print(f"    Dosya Boyutu: {size_kb:.2f} KB")
    print(f"    Toplam Mesele Sayısı: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
