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

DUGUMLER_FAZ_5 = [
    {
        "bolum_id": "05_zekat_derin",
        "bolum_adi": "Kitâbü'z-Zekât (Kalan Amelî Düğümler)",
        "dosya": "05_zekat.md",
        "meseleler": [
            (53, "Şüpheli ve Batık Alacakların Zekâtı Ne Zaman Verilir?", "زكاة الدين المرجو وغير المرجو والضمار", {
                "ruhsat_mezhep": "Mâlikî Mezhebi (Kabzedilince tek yıl zekât)",
                "ruhsat_hukum": "Yıllarca tahsil edilemeyen şüpheli veya batık alacaklar için geriye dönük her yıl zekât verilmez; alacak tahsil edildiği gün sadece son 1 yılın zekâtı ödenir.",
                "hanefi_hukum": "Kuvvetli alacak tahsil edilince geçmiş bütün yılların zekâtı toptan ödenir.",
                "safii_hukum": "Borçlu inkâr etse dahi tahsil edildiğinde geçmiş tüm yılların zekâtı hesaplanıp verilir.",
                "maliki_hukum": "Tahsil edilmeyen borçta zekât yoktur; ele geçince yalnız 1 yıllık zekât ödenir.",
                "hanbeli_hukum": "Ümit kesilen borç ele geçerse sadece tahsil edildiği yılın zekâtı verilir."
            }),
            (54, "Kiraya Verilen Gayrimenkullerin ve Üretim Araçlarının Zekâtı", "زكاة العقارات المؤجرة والمصانع والآلات الإنتاجية", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Kiraya verilen ev, iş yeri, fabrika binası veya üretim makinelerinin piyasa değeri üzerinden zekât verilmez; yalnızca bunlardan elde edilen net nakit kira geliri nisaba ulaşırsa zekâta tâbidir.",
                "hanefi_hukum": "Kira getiren mülklerin aslına zekât düşmez, sadece biriken net nakit zekâta tâbidir.",
                "safii_hukum": "Üretim ve kira araçlarının bizzat kendisi zekâttan muaftır.",
                "maliki_hukum": "Taşınmazın aynında zekât yoktur; elde edilen gelir üzerinden yıl geçerse verilir.",
                "hanbeli_hukum": "Kira mülklerinin aslı zekâttan hariçtir; nakit gelire tâbidir."
            }),
            (55, "Zekât Verilecek Kimselere Temlik Şartı ve Hayır Kurumlarına Zekât", "اشتراط التمليك في الزكاة وصرفها في سبل الخير العامة", {
                "ruhsat_mezhep": "İmam Kāsım b. Sellâm ve Bazı Hanbelî Tahrîcleri ('Fî Sebîlillâh' Tevsîi)",
                "ruhsat_hukum": "Zekâtın bizzat fakirin eline nakden teslim edilmesi (temlik) tek yol değildir; fakirlerin barınma, tedavi, aşevi, eğitim ve dînî tebliğ masraflarını karşılayan vakıf ve kamu yararı kurumlarına zekât fonu aktarılabilir.",
                "hanefi_hukum": "Zekâtın sıhhati için fakirin mülkiyetine verilmesi (temlik) şarttır; köprü, bina ve kamu hizmetine zekât harcanmaz.",
                "safii_hukum": "Zekât Kur'an'daki 8 sınıftan mevcut olanlara bizzat dağıtılmalıdır; tüzel kişiliklere temliksiz verilemez.",
                "maliki_hukum": "Fî sebîlillâh cihad ve mücahidlere mahsustur; genel kamu hizmetlerine harcanmaz.",
                "hanbeli_hukum": "Klasik kavilde temlik şarttır; çağdaş tahrîcte ise kamu maslahatı ve İslam tebliği fî sebîlillâh kapsamına alınmıştır."
            })
        ]
    },
    {
        "bolum_id": "06_hac_derin",
        "bolum_adi": "Kitâbü'l-Hac ve'l-Umre (Kalan Amelî Düğümler)",
        "dosya": "06_hac.md",
        "meseleler": [
            (56, "İhram Yasakları İhlal Edildiğinde Ceza Olarak Koyun Kesmek (Dem) mi Yoksa Oruç/Sadaka mı?", "التخيير في فدية الأذى ومحظورات الإحرام", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Muhayyerlik Ruhsatı)",
                "ruhsat_hukum": "Tıraş olmak, koku sürünmek, dikişli elbise giymek gibi ihram yasaklarını kasten veya zarureten ihlal eden kimse doğrudan kurban kesmek zorunda değildir; dilerse 3 gün oruç tutar, dilerse 6 fakiri doyurur.",
                "hanefi_hukum": "Tam bir gün dikişli giyen veya tam uzva koku süren için ceza doğrudan koyun kesmektir (dem); oruca dönüşme zarurette geçerlidir.",
                "safii_hukum": "Fidye-i ezâ âyeti gereğince mükellef kurban, 3 gün oruç veya 6 fakire sadaka arasında tamamen muhayyerdir.",
                "maliki_hukum": "İhram yasaklarında kurban, oruç ve sadaka arasında muhayyerlik esastır.",
                "hanbeli_hukum": "Nassın açık hükmü gereğince kişi 3 seçenek arasında serbesttir."
            }),
            (57, "Âdet Kanaması Olan Kadının Tavâf-ı İfâda Yapması", "طواف الإفاضة للحائض عند تعذر المقام وضيق الوقت", {
                "ruhsat_mezhep": "İbn Teymiyye ve Hanefî Zaruret Tahrîci",
                "ruhsat_hukum": "Âdeti devam eden ve kafilesi hareket etmek zorunda olan kadın, temizlenmeyi bekleme imkânı yoksa iyice sarınıp tavâf-ı ifâdasını yapar; tavâfı geçerlidir, kaza veya ceza gerekmez.",
                "hanefi_hukum": "Hayızlı tavâf geçerlidir fakat tahrîmen mekruhtur; telafisi için büyükbaş kurban (bedene) kesmesi gerekir.",
                "safii_hukum": "Tavâfta tahâret rükündür; hayızlı kadının tavâfı kat'iyyen bâtıldır, temizlenmeden Kâbe'ye giremez.",
                "maliki_hukum": "Hadesten tahâret tavâfın şartıdır; hayızlı tavâf bâtıldır.",
                "hanbeli_hukum": "Klasik mezhepte bâtıldır; İbn Teymiyye tahrîcine göre ise zaruret anında abdest şartı düşer ve tavâf sahihtir."
            }),
            (58, "Tavâf-ı Vedâ'nın (Veda Tavafı) Hükmü ve Terki", "حكم طواف الوداع وسقوطه عن الحائض والمعذور", {
                "ruhsat_mezhep": "Mâlikî Mezhebi (Sünnet olması) ve Cumhur (Özürlüden düşmesi)",
                "ruhsat_hukum": "Tavâf-ı vedâ vacip değil sünnettir; terk edilmesinde kurban gerekmez. Âdetli kadın ve mazeret sahiplerinden ise ittifakla tamamen düşer.",
                "hanefi_hukum": "Âfâkî için veda tavafı vaciptir; mazeretsiz terk eden koyun kurbanı keser, hayızlı kadından düşer.",
                "safii_hukum": "Veda tavafı vaciptir; terkine dem gerekir; hayızlıdan düşer.",
                "maliki_hukum": "Veda tavafı sünnettir; terk edilmesinde ceza kurbanı gerekmez.",
                "hanbeli_hukum": "Veda tavafı vaciptir; ancak mazeretlilerden düşer."
            })
        ]
    },
    {
        "bolum_id": "07_nikah_derin",
        "bolum_adi": "Kitâbü'n-Nikâh ve'l-Mühr (Kalan Amelî Düğümler)",
        "dosya": "07_nikah.md",
        "meseleler": [
            (59, "Gizli Tutulan ve Şahitlerin Ketmettiği Nikâhın Sıhhati", "نكاح السر وتواصي الشهود بالكتمان", {
                "ruhsat_mezhep": "Hanefî ve Şâfiî Mezhepleri (İlanın sıhhat şartı olmaması)",
                "ruhsat_hukum": "Nikâh esnasında 2 erkek şahit hazır bulunmuşsa, taraflar şahitlere 'bunu gizli tutun' deseler dahi nikâh akdi hukuken sahihtir; cemiyete ilân etmek şart değil sünnettir.",
                "hanefi_hukum": "Şahitlerin huzurunda icap ve kabul ile akit tamamlanır; gizlilik vasiyeti akdi iptal etmez.",
                "safii_hukum": "İki âdil şahit hazırsa nikâh sahihtir; ilânın terki akdi ifsad etmez.",
                "maliki_hukum": "Şahitlere gizleme şartı koşulan nikâh (nikâh-ı sırr) fâsittir; zifaftan önce feshedilir.",
                "hanbeli_hukum": "Şahitler varsa akit geçerlidir; ilân etmek menduptur."
            }),
            (60, "Evlilik Engeli Doğan Süt Emzirme Sayısı (1 Damla mı, 5 Doyum mu?)", "عدد الرضعات المحرمة للنكاح بين المصة والمصتين والخمس", {
                "ruhsat_mezhep": "Şâfiî ve Hanbelî Mezhepleri (5 doyum şartıyla haramlığın daraltılması)",
                "ruhsat_hukum": "Süt kardeşliği ve evlilik yasağı, ancak ilk 2 yaş içinde gerçekleşen ve kesin olarak bilinen en az 5 ayrı doyurucu emzirme ile sabit olur; 1-2 damla veya şüpheli emmelerle evlilik haram olmaz.",
                "hanefi_hukum": "Boğaza ve mideye ulaşan tek bir damla süt dahi olsa mutlak surette evlilik haramlığı doğurur.",
                "safii_hukum": "Aişe hadisi nassı gereğince 5 ayrı ve doyurucu emzirme olmaksızın süt hısımlığı doğmaz.",
                "maliki_hukum": "Az veya çok mideye giren her süt haramlık oluşturur.",
                "hanbeli_hukum": "Kesin bilinen 5 ayrı emzirme şarttır; şüpheyle hürmet sabit olmaz."
            }),
            (61, "Mehrin Alt ve Üst Sınırının Belirlenmesi", "تحديد أقل المهر وأكثره في النكاح", {
                "ruhsat_mezhep": "Şâfiî ve Hanbelî Mezhepleri (Alt sınırın olmaması)",
                "ruhsat_hukum": "Mehrin belirlenmesinde dinen hiçbir alt sınır yoktur; maddi değeri olan en küçük bir eşya, yüzük hatta Kur'an öğretimi dahi geçerli bir mehir sayılır.",
                "hanefi_hukum": "Mehrin alt sınırı 10 dirhem gümüştür; bunun altında belirlenen mehir 10 dirheme tamamlanır.",
                "safii_hukum": "Maddi kıymeti olan her şey mehir olabilir, alt veya üst sınır yoktur.",
                "maliki_hukum": "Mehrin alt sınırı en az 3 dirhem gümüş veya çeyrek altındır.",
                "hanbeli_hukum": "Kıymeti olan her nesne mehir yapılabilir; alt sınır tayin edilmemiştir."
            }),
            (62, "Şarta Bağlı (Ta'lîkî) Boşamanın Hükmü ve Yemin Sayılması", "الطلاق المعلق على شرط وحكمه عند وقوع الشرط", {
                "ruhsat_mezhep": "İbn Teymiyye ve Hanbelî Tahrîci (Yemin keffareti ruhsatı)",
                "ruhsat_hukum": "Bir kimse eşini tehdit veya ikna amacıyla 'Şuraya gidersen boşsun' gibi bir şarta bağlasa, niyeti gerçekten boşamak değil de sadece engellemek ise şart gerçekleştiğinde talak vaki olmaz; yemin keffareti ödemesi yeterlidir.",
                "hanefi_hukum": "Şart gerçekleştiği anda talak lafzı kesin olarak düşer, niyete bakılmaz.",
                "safii_hukum": "Şart vuku bulduğunda talak derhal gerçekleşir.",
                "maliki_hukum": "Ta'lik edilen şart gerçekleşince talak vaki olur.",
                "hanbeli_hukum": "Klasik kavilde vaki olur; İbn Teymiyye tahkikine göre niyet yemin ve tehdit ise talak düşmez, keffaret gerekir."
            })
        ]
    },
    {
        "bolum_id": "04_buyu_derin",
        "bolum_adi": "Kitâbü'l-Büyû' (Kalan Amelî Düğümler)",
        "dosya": "04_buyu.md",
        "meseleler": [
            (63, "Erken Ödeme İskontosu Yapmak (Da' ve Te'accel)", "حكم ضع وتعجل في الديون والنزول عن بعض الدين للتعجيل", {
                "ruhsat_mezhep": "İbn Abbâs, İbn Teymiyye ve Hanbelî Tahrîci",
                "ruhsat_hukum": "Alacaklının, borcun vadesi gelmeden önce peşin ödenmesi karşılığında borçludan bir miktar alacağından feragat etmesi (iskonto) caizdir; ribâ sayılmaz.",
                "hanefi_hukum": "Vade karşılığı indirim yapmak faize benzediği için caiz görülmez.",
                "safii_hukum": "Vadeyi parayla satmak sayıldığı için meşhur kavilde caiz değildir.",
                "maliki_hukum": "Da' ve te'accel kural olarak men edilmiştir.",
                "hanbeli_hukum": "İbn Abbas'ın fetvası ve İbn Teymiyye tercihiyle ihtiyaç ve maslahat gereği caizdir."
            }),
            (64, "Cayma Tazminatı Olarak Kaporanın Satıcıda Kalması (Bey'u'l-Urbûn)", "بيع العربون وحكم احتفاظ البائع بالعربون عند الفسخ", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (İmam Ahmed b. Hanbel)",
                "ruhsat_hukum": "Bir mal satın alırken verilen kaporanın, alıcının akitten vazgeçmesi halinde satıcıda tazminat olarak kalması şartı sahihtir; helaldir.",
                "hanefi_hukum": "Kapora akdi fâsittir; alıcı vazgeçerse kapora aynen iade edilmelidir.",
                "safii_hukum": "Sebepsiz zenginleşme ve garar sebebiyle bâtıldır, satıcı kaporayı alamaz.",
                "maliki_hukum": "Kaporanın satıcıda kalması caiz görülmez.",
                "hanbeli_hukum": "Hz. Ömer'in uygulaması gereğince kapora akdi sahihtir; vazgeçilirse satıcının hakkıdır."
            }),
            (65, "İnternet ve Mesafeli Satışlarda Cayma Hakkı (Hıyâru'ş-Şart ve'r-Rü'yet)", "خيار الرؤية وخيار الشرط في المعاملات المعاصرة والتجارة الإلكترونية", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Görmeden satın almada mutlak rü'yet muhayyerliği)",
                "ruhsat_hukum": "İnternetten veya katalogdan sipariş edilen malı teslim alıp bizzat gören alıcı, malda hiçbir ayıp/kusur olmasa dahi hiçbir gerekçe göstermeksizin akdi feshedip parasını geri alma hakkına sahiptir.",
                "hanefi_hukum": "Görülmeyen malın satışında görme muhayyerliği (hıyâru'r-rü'yet) sabittir; görünce feshetmek mutlak haktır.",
                "safii_hukum": "Görülmeyen malın satışı bâtıldır; vasfı anlatılarak selem şeklinde yapılmışsa fesih hakkı kusura bağlıdır.",
                "maliki_hukum": "Vasıflarına uygun gelmişse cayma hakkı düşer; uymazsa feshedilir.",
                "hanbeli_hukum": "Vasıflandırma yapılmışsa bağlayıcıdır; görme muhayyerliği sadece vasıf uyuşmazlığında geçerlidir."
            })
        ]
    },
    {
        "bolum_id": "18_ferâiz",
        "bolum_adi": "Kitâbü'l-Ferâiz ve'l-Vesâyâ (Miras ve Vasiyet Hükümleri)",
        "dosya": "18_feraiz.md",
        "meseleler": [
            (66, "Vârise Vasiyet Edilmesi ve Diğer Vârislerin Rızası", "الوصية للوارث وحكم إجازة سائر الورثة لها", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Diğer vârislerin icâzetiyle geçerlilik)",
                "ruhsat_hukum": "'Vârise vasiyet yoktur' hadisi genel kural olmakla birlikte, miras bırakanın bir vârisi lehine yaptığı vasiyet, vefattan sonra diğer vârislerin rızası/onayı ile kesin olarak geçerli hale gelir.",
                "hanefi_hukum": "Diğer vârisler akıl baliğ olup izin verirse vârise vasiyet sahihtir ve infaz edilir.",
                "safii_hukum": "Vârislerin tamamı icazet verirse vasiyet geçerlidir; icazet hibedir.",
                "maliki_hukum": "Mirasçıların rızası ile vârise vasiyet caiz ve nafizdir.",
                "hanbeli_hukum": "Vârislerin onayı ile vasiyet yürürlüğe girer."
            }),
            (67, "Gayrimüslim Akrabadan Miras Alınması veya Vasiyet Yoluyla İntikal", "توارث أهل الملتين والوصية لغير المسلم ومنه", {
                "ruhsat_mezhep": "Hanefî ve Hanbelî Mezhepleri (Vasiyet cevazı) ve Muâz b. Cebel Tahrîci",
                "ruhsat_hukum": "Farklı dinden olanlar arasında doğrudan mirasçılık cereyan etmese de, gayrimüslim bir akrabanın müslümana (veya müslümanın gayrimüslime) malının üçte birine kadar vasiyet etmesi ittifakla sahihtir; bu yolla mal intikal edebilir.",
                "hanefi_hukum": "Müslüman ile gayrimüslim birbirine vasiyet edebilir, üçte bir sınırıyla nafizdir.",
                "safii_hukum": "Dinde vasiyet hibe gibidir; gayrimüslime veya ondan müslümana vasiyet caizdir.",
                "maliki_hukum": "Harbî olmayan gayrimüslimle vasiyetleşmek sahihtir.",
                "hanbeli_hukum": "Vasiyette din birliği şart değildir, vasiyet geçerlidir."
            })
        ]
    }
]

def main():
    print("=" * 80)
    print("[*] FAZ 5: 150 DÜĞÜMÜN TAMAMLANMASI (MESELE 053 - 067)")
    print("=" * 80)

    compiler = ProductionFikhCompiler()
    completed = load_checkpoints()
    print(f"[+] Başlangıçtaki Doğrulanmış Mesele Sayısı: {len(completed)}")

    for bolum in DUGUMLER_FAZ_5:
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
        ("11_muamelat_muasira.md", "KİTÂBÜ'L-MUÂMELÂTİ'L-MUÂSIRA (ÇAĞDAŞ FİNANS VE SÖZLEŞMELER)"),
        ("18_feraiz.md", "KİTÂBÜ'L-FERÂİZ VE'L-VESÂYÂ (MİRAS VE VASİYET)")
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
    print(f"[+] FAZ 5 BAŞARIYLA TAMAMLANDI:")
    print(f"    Master Kitap: {MASTER_BOOK_PATH}")
    print(f"    Toplam Boyut: {size_kb:.2f} KB")
    print(f"    Toplam Mesele Sayısı: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
