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

DUGUMLER_FAZ_7 = [
    {
        "bolum_id": "03_siyam_derin",
        "bolum_adi": "Kitâbü's-Sıyâm (İleri Oruç Düğümleri)",
        "dosya": "03_siyam.md",
        "meseleler": [
            (76, "İmsak Vaktinin Belirlenmesi (Fecr-i Kâzib / Fecr-i Sâdık ve İhtiyat Payı)", "تحديد وقت الإمساك بين الفجر الكاذب والصادق والأخذ بالاحتياط", {
                "ruhsat_mezhep": "Cumhur Fukahâsı ve Sahabe Ruhsatı (Fecr-i Sâdıkın ufukta yayılmasına kadar yeme-içme)",
                "ruhsat_hukum": "Takvimlerdeki temkin ve ihtiyat dakikaları bağlayıcı farz değildir; ufukta beyazlık enlemesine yayılıncaya (fecr-i sâdık kesinleşinceye) kadar yiyip içmek caizdir, oruca halel gelmez.",
                "hanefi_hukum": "Fecr-i sâdıkın doğuşuyla imsak başlar; şüphe anında yemeyi bırakmak ihtiyaten vaciptir.",
                "safii_hukum": "İkinci fecrin doğuşuyla imsak girer; kesin vakit bilinmedikçe yemeye devam etmek mubahtır.",
                "maliki_hukum": "Fecrin tuluu ile oruç başlar; şüphe ile yiyene kaza gerekir.",
                "hanbeli_hukum": "Fecr-i sâdık açıkça belirinceye kadar yiyip içmek helaldir; şüphe halinde oruç bozulmaz."
            }),
            (77, "Oruçlu İken Tükürük, Balgam ve Ağız Çalkalama Artığı Suyun Yutulması", "بلع الريق والنخامة وبقايا ماء المضمضة للصائم", {
                "ruhsat_mezhep": "Hanefî ve Mâlikî Mezhepleri (Umum-ı belvâ sebebiyle mutlak muafiyet)",
                "ruhsat_hukum": "Ağızda biriken tükürüğü, genizden gelen balgamı veya abdest sonrası ağızda kalan ıslaklığı kasten veya gayriihtiyari yutmak orucu kesinlikle bozmaz.",
                "hanefi_hukum": "Tükürük ve ağız içi ıslaklığı yutmak orucu bozmaz; genizden inen balgam mideye gitse de orucu iptal etmez.",
                "safii_hukum": "Ağız dışına çıkmayan tükürük bozmaz; ancak ağız boşluğuna düşen balgamı kasten yutmak orucu bozar.",
                "maliki_hukum": "Balgam ve tabii salgılar necis olmadığından ve sakınılması güç olduğundan orucu bozmaz.",
                "hanbeli_hukum": "Ağız dışına çıkmadıkça tükürük ve balgam orucu ifsat etmez."
            }),
            (78, "Hamile ve Emziren Kadının Oruç Tutmaması (Kaza mı, Sadece Fidye mi?)", "حكم إفطار الحامل والمرضع وخوفهما على النفس أو الولد", {
                "ruhsat_mezhep": "İbn Abbâs ve İbn Ömer Mezhebi (Sadece fidye ile yetinme ruhsatı)",
                "ruhsat_hukum": "Kendisine veya bebeğine zarar gelmesinden endişe eden hamile ya da emzikli kadın oruç tutmayabilir; aralıksız çocuk sahibi olan/sürekli emziren kadın için kaza meşakkati varsa sadece her gün için bir fidye vermesi yeterlidir, kaza borcu düşer.",
                "hanefi_hukum": "Zarar tehlikesi varsa oruç açılır; ancak daha sonra yalnızca kaza edilir, fidye gerekmez.",
                "safii_hukum": "Çocuğu için korkarsa hem gününe gün kaza eder hem de her gün için bir fidye öder.",
                "maliki_hukum": "Hamileye sadece kaza; emzirene ise kaza ile birlikte fidye vaciptir.",
                "hanbeli_hukum": "Çocuk için korkulursa kaza ve fidye birlikte terettüp eder."
            }),
            (79, "Ağır İşlerde Çalışanların ve Aşırı Meşakkate Düşenlerin Oruç Açması", "إفطار أصحاب الأعمال الشاقة والعمال عند تعذر الجمع بين العمل والصوم", {
                "ruhsat_mezhep": "Hanefî ve Hanbelî Müteahhirîn Fukahâsı",
                "ruhsat_hukum": "Geçimini sağlamak için ağır işlerde (maden, fırın, ağır sanayi vb.) çalışmak zorunda olup oruca devam ettiği takdirde sağlığını yitirme tehlikesi bulunan kimse, güne niyetle başlar; meşakkat tahammül sınırını aştığında orucunu açar ve müsait zamanda kaza eder; keffâret gerekmez.",
                "hanefi_hukum": "Helak olma veya ağır hastalanma tehlikesi belirdiğinde oruç bozulur; sadece kaza gerekir.",
                "safii_hukum": "Güne mutlak niyetle başlanmalıdır; meşakkat zaruret sınırına vardığında iftar caiz olur.",
                "maliki_hukum": "Zaruret halinde iftar mubahtır, gününe gün kaza edilir.",
                "hanbeli_hukum": "Aşırı meşakkat ve sağlığın bozulması korkusu meşru bir iftar mazeretidir."
            })
        ]
    },
    {
        "bolum_id": "05_zekat_derin2",
        "bolum_adi": "Kitâbü'z-Zekât (Mali Değerleme Düğümleri)",
        "dosya": "05_zekat.md",
        "meseleler": [
            (80, "Ticaret Mallarında Zekât Hesaplanırken Maliyet mi, Satış Fiyatı mı Esastır?", "تقويم عروض التجارة بسعر التكلفة أو بسعر السوق يوم الوجوب", {
                "ruhsat_mezhep": "Cumhur Fukahâsı ve Çağdaş Fıkıh Heyetleri (Toptan satış/maliyet değeri ruhsatı)",
                "ruhsat_hukum": "Tüccar yıl sonundaki stoklarını perakende kâr eklenmiş fiyattan değil; toptan piyasa alım değeri veya maliyet bedeli üzerinden hesaplayarak zekât matrahını belirler; gerçekleşmemiş kârın zekâtı verilmez.",
                "hanefi_hukum": "Yıl sonundaki rayiç toptan piyasa değeri esas alınır.",
                "safii_hukum": "Senet sonundaki toptan satış kıymeti üzerinden değerleme yapılır.",
                "maliki_hukum": "Tüccar-ı müdîr (dönen ticaret) cari toptan rayiç bedeli üzerinden matrah çıkarır.",
                "hanbeli_hukum": "Yıl dolduğu gündeki piyasa alım/toptan kıymeti zekâta esas alınır."
            }),
            (81, "Bireysel Emeklilik (BES), Kıdem Tazminatı ve Emeklilik Fonlarının Zekâtı", "زكاة مكافأة نهاية الخدمة وصناديق التقاعد والتأمينات", {
                "ruhsat_mezhep": "Çağdaş Hanefî ve Mâlikî Tahrîci (Kabz şartı ruhsatı)",
                "ruhsat_hukum": "Çalışırken biriken ancak istifa, emeklilik veya işten ayrılma olmadan çekilemeyen kıdem tazminatı ve bloke emeklilik fonları tam mülkiyet altında olmadığından her yıl zekâta tâbi değildir; para ele geçtiğinde sadece o yılın zekâtı ödenir.",
                "hanefi_hukum": "Kuvvetsiz alacak ve gayrikabili rücû haklarda para fiilen tahsil edilmedikçe zekât gerekmez.",
                "safii_hukum": "Mülkiyet kesinleşmedikçe ve tasarruf imkânı bulunmadıkça zekât matrahına dâhil edilmez.",
                "maliki_hukum": "Kabzedilmeyen tazminat ve haklar için geriye dönük zekât aranmaz; kabz günü 1 yıl zekât verilir.",
                "hanbeli_hukum": "Tasarruf serbestisi olmayan fonlar ele geçtikten sonra zekâtlandırılır."
            }),
            (82, "Akrabaya, Anne-Babaya veya Eşe Zekât Verilmesinin Sınırları", "دفع الزكاة إلى الأقارب والزوجين ومن تجب نفقته", {
                "ruhsat_mezhep": "Şâfiî ve Hanbelî Mezhepleri (Zevcenin fakir kocasına zekât vermesi)",
                "ruhsat_hukum": "Koca zengin olan eşine zekât veremez (çünkü nafaka borçlusudur); fakat zengin kadın, nafaka mükellefiyeti bulunmayan fakir ve borçlu kocasına zekâtını verebilir; akrabaya verilen zekât hem sadaka hem sıla-i rahimdir.",
                "hanefi_hukum": "Karı-koca birbirine hiçbir surette zekât veremez; mülkiyet menfaati ortaktır (İmâmeyn ise kadının kocaya vermesini caiz görür).",
                "safii_hukum": "Kadının fakir kocasına zekât vermesi İbn Mes'ûd hadisi gereğince ittifakla caizdir.",
                "maliki_hukum": "Kadın kocasına verebilir, ancak kocanın bu parayla kadının nafakasını temin etmesi şart koşulamaz.",
                "hanbeli_hukum": "Kadının kocasına ve nafakasını üstlenmediği akrabalarına zekât vermesi sahihtir."
            })
        ]
    },
    {
        "bolum_id": "06_hac_derin2",
        "bolum_adi": "Kitâbü'l-Hac ve'l-Umre (Menasik Düğümleri)",
        "dosya": "06_hac.md",
        "meseleler": [
            (83, "Arafat Vakfesinin Zamanı ve Geceye Kadar Bekleme Mecburiyeti", "وقت الوقوف بعرفة والجمع بين الليل والنهار", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (Gündüzden geceye kalmama ruhsatı)",
                "ruhsat_hukum": "Arafat vakfesinde zevalden sonra bir an dahi durmak vakfenin rüknünü tamamlar; güneş batmadan önce Arafat'tan ayrılan kimsenin haccı sahihtir ve ceza kurbanı gerekmez.",
                "hanefi_hukum": "Gündüz Arafat'a girenin güneş batana kadar beklemesi vaciptir; erken ayrılan ceza kurbanı (dem) keser.",
                "safii_hukum": "Güneş batana kadar kalmak sünnettir; erken ayrılana herhangi bir ceza gerekmez.",
                "maliki_hukum": "Gündüzün ve gecenin bir cüzünde bulunmak vaciptir; geceye sarkmayan kurban keser.",
                "hanbeli_hukum": "Arafat'ta gündüz veya gece bir lahza bulunmak kâfidir; güneş batmadan çıkana dem vacip değildir."
            }),
            (84, "Say' İbadetinde Yürümek Şart mıdır? (Araç ve Sandalyeyle Say')", "المشي في السعي بين الصفا والمروة والركوب لغير عذر", {
                "ruhsat_mezhep": "Şâfiî ve Hanbelî Mezhepleri (Yürümenin rükün veya vacip olmaması)",
                "ruhsat_hukum": "Safâ ile Merve arasında sa'y ederken yürümek şart veya vacip değildir, sünnettir; mazeretsiz dahi olsa tekerlekli sandalye veya elektrikli araçla sa'y yapmak geçerlidir, ceza kurbanı gerekmez.",
                "hanefi_hukum": "Gücü yetenin bizzat yürümesi vaciptir; mazeretsiz araca binen koyun kurbanı keser.",
                "safii_hukum": "Sa'yde yürümek sünnettir; binek veya araçla yapılan sa'y mutlak caizdir.",
                "maliki_hukum": "Yürümek vaciptir; özürsüz binen sa'yi iade eder veya kurban keser.",
                "hanbeli_hukum": "Binek üzerinde sa'y yapmak sahihtir; Resulullah devesi üzerinde sa'y etmiştir."
            }),
            (85, "Hacda Şeytan Taşlamanın Zeval Vaktinden Önce Yapılması (İzdiham Ruhsatı)", "رمي الجمار قبل الزوال في أيام التشريق لدفع المشقة", {
                "ruhsat_mezhep": "İmam Ebû Hanîfe Rivayeti, Tâvus ve Atâ b. Ebî Rabâh Tahrîci",
                "ruhsat_hukum": "Teşrik günlerinde ezilme tehlikesi, aşırı sıcak veya kafile uçağına yetişme zarureti varsa, taşlar öğle (zeval) vakti girmeden önce sabah saatlerinde atılabilir; hac sahihtir, ceza gerekmez.",
                "hanefi_hukum": "Zevalden önce taşlama tahrîmen mekruhtur veya bâtıldır; ancak son gün (nefir günü) zevalden önce caizdir.",
                "safii_hukum": "Zevalden önce taş atmak geçersizdir; vakit zevalle başlar.",
                "maliki_hukum": "Zevalden evvel atılan taşlar hükümsüzdür, iadesi gerekir.",
                "hanbeli_hukum": "Aslolan zeval sonrasıdır; fakat aşırı izdiham ve meşakkatte zevalden önce cevaz veren müçtehitler vardır."
            })
        ]
    },
    {
        "bolum_id": "07_nikah_derin2",
        "bolum_adi": "Kitâbü'n-Nikâh ve Aile (Velayet ve Nesep Düğümleri)",
        "dosya": "07_nikah.md",
        "meseleler": [
            (86, "Boşanma Sonrası Çocuğun Hıdâne (Bakım ve Gözetim) Yaşı ve Mezhepler", "سن الحضانة للأم وانتقال الولاية إلى الأب أو التخيير", {
                "ruhsat_mezhep": "Mâlikî Mezhebi (Kız çocuğunda evlenene, erkekte büluğa kadar annede kalma ruhsatı)",
                "ruhsat_hukum": "Boşanma halinde anne evlenmediği sürece çocuğun bakım hakkı (hıdâne) en uzun Mâlikî mezhebinde korunur; erkek çocuk büluğa erene, kız çocuğu ise evlenip zifafa girene kadar annenin yanında kalabilir.",
                "hanefi_hukum": "Erkek çocuk 7-9 yaşına, kız çocuk 9-11 yaşına gelince hıdâne babaya intikal eder.",
                "safii_hukum": "Temyiz yaşına (7-8 yaş) ulaşan çocuk anne ile baba arasında muhayyer bırakılır, dilediğini seçer.",
                "maliki_hukum": "Erkek çocuk büluğa kadar, kız çocuğu evlenene kadar annenin yanında kalır (en geniş anne hakkı).",
                "hanbeli_hukum": "7 yaşına kadar anne bakar; 7 yaşından sonra çocuk muhayyer kılınır."
            }),
            (87, "Fasit veya Şüpheli Nikâh Sonrası Doğan Çocuğun Nesebi", "ثبوت النسب في النكاح الفاسد ونكاح الشبهة", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Çocuğun nesebinin korunması ilkesi)",
                "ruhsat_hukum": "Şahitsiz, velisiz veya akrabalık engeli sonradan anlaşılan fasit bir nikâhla birleşen çiftin çocuğu veled-i zinâ sayılmaz; çocuk babaya nispet edilir, mirasçı olur ve nesebi sahih kabul edilir.",
                "hanefi_hukum": "Fasit nikâhta zifaf vuku bulmuşsa nesep babaya iltihak eder, çocuk meşrudur.",
                "safii_hukum": "Şüphe akdi veya fasit akitte nesep kesinlikle sabit olur, çocuk korunur.",
                "maliki_hukum": "Hüsnüniyet ve şüphe nikâhında nesep ittifakla babaya bağlanır.",
                "hanbeli_hukum": "Akit fâsit dahi olsa nesebin ispatında aslolan korunmadır, nesep sabittir."
            }),
            (88, "Zina Eden veya Hamile Kalan Kadınla Evlenmenin Hükmü", "نكاح الزانية وحكم التزوج بها قبل الاستبراء أو التوبة", {
                "ruhsat_mezhep": "Hanefî ve Şâfiî Mezhepleri (İstibrâ ve tevbe şartının aranmaması)",
                "ruhsat_hukum": "Zina etmiş veya zinadan hamile kalmış bir kadınla nikâh akdi kıymak geçerlidir; hamile bırakan erkeğin kendisi evlenmişse zifaf derhal helal olur, başkası evlenmişse doğuma kadar zifaf ertelenir.",
                "hanefi_hukum": "Zina eden kadınla evlenmek caizdir; hâmile ise nikâh sahihtir fakat doğuma kadar cima helal olmaz.",
                "safii_hukum": "Zâniye ile evlenmek mubahtır; iddet ve istibrâ şartı yoktur, nikâh ve cima derhal caizdir.",
                "maliki_hukum": "Zina eden kadının rahmi istibrâ edilmedikçe (en az 1 hayız geçmedikçe) nikâh bâtıldır.",
                "hanbeli_hukum": "Kadın samimiyetle tevbe etmedikçe ve istibrâ süresi dolmadıkça evlilik haramdır."
            })
        ]
    },
    {
        "bolum_id": "19_kaza",
        "bolum_adi": "Kitâbü'l-Kazâ ve'ş-Şehâdât (Yargı ve İspat Hukuku)",
        "dosya": "19_kaza.md",
        "meseleler": [
            (89, "Kadının Hâkim / Yargıç Olabilmesi ve Kararlarının Geçerliliği", "تولية المرأة القضاء وحكم قضائها في المعاملات والأموال", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Hudûd dışı davalarda mutlak cevaz) ve Taberî Tahrîci",
                "ruhsat_hukum": "Kadınlar, şahitliklerinin geçerli olduğu bütün hukuk, ticaret, aile, miras ve borçlar davalarında hâkim olarak atanabilir ve verdikleri hükümler hukuken nafizdir.",
                "hanefi_hukum": "Kısas ve had cezaları hariç, şahitlik yapabildiği tüm hukukî davalarda kadının hâkimliği caizdir.",
                "safii_hukum": "Kadının hâkimiyeti mutlak surette bâtıldır; verdiği hiçbir karar hukuken geçerli olmaz.",
                "maliki_hukum": "Hâkimlikte erkeklik şarttır; kadının hükmü bozulur.",
                "hanbeli_hukum": "Yargı yetkisi velayet-i âmmedir, kadının hâkimliği sahih değildir."
            }),
            (90, "Tek Bir Şahit ve Davacının Yemini ile Hüküm Vermek", "القضاء بشاهد واحد مع يمين المدعي في الأموال", {
                "ruhsat_mezhep": "Şâfiî, Mâlikî ve Hanbelî Mezhepleri (Şahit + Yemin ile ispat ruhsatı)",
                "ruhsat_hukum": "Mali davalarda iki şahit bulunamadığı takdirde, davacının güvenilir tek bir şahit getirmesi ve kendi davasına yemin etmesiyle hâkim davacı lehine hükmedebilir; hak zayi edilmez.",
                "hanefi_hukum": "İki erkek veya bir erkek iki kadın şahit olmaksızın yeminle hüküm verilemez; tek şahitle hüküm bâtıldır.",
                "safii_hukum": "Resulullah bir şahit ve davacının yeminiyle hüküm vermiştir; mali davalarda caizdir.",
                "maliki_hukum": "Mal ve alacak davalarında şahit ile yemin birleştirilerek hak sabit olur.",
                "hanbeli_hukum": "Sünnetin açık tatbikatı gereğince tek şahit ve yeminle hüküm vermek meşrudur."
            })
        ]
    }
]

def main():
    print("=" * 80)
    print("[*] NÖRO-SEMBOLİK FAZ 7 MOTORU: MESELE 076 - 090")
    print("=" * 80)

    compiler = NeuroSymbolicFikhEngine()
    completed = load_checkpoints()
    print(f"[+] Başlangıçtaki Doğrulanmış Mesele Sayısı: {len(completed)}")

    for bolum in DUGUMLER_FAZ_7:
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
        ("16_tib_gunluk.md", "KİTÂBÜ'T-TIBB VE'L-İSTİHÂLE (SAĞLIK VE GÜNLÜK YAŞAM)"),
        ("19_kaza.md", "KİTÂBÜ'L-KAZÂ VE'Ş-ŞEHÂDÂT (YARGI VE İSPAT HUKUKU)")
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
    print(f"[+] FAZ 7 BAŞARIYLA TAMAMLANDI:")
    print(f"    Master Kitap: {MASTER_BOOK_PATH}")
    print(f"    Toplam Boyut: {size_kb:.2f} KB")
    print(f"    Toplam Mesele Sayısı: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
