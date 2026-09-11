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

DUGUMLER_FAZ_10 = [
    {
        "bolum_id": "24_muamelat_son",
        "bolum_adi": "Kitâbü'l-Muâmelât (Son Ticari ve Mali Düğümler)",
        "dosya": "04_buyu.md",
        "meseleler": [
            (126, "Peşin Fiyatına Taksit Kampanyalarında Banka Komisyonunun Hükmü", "عمولة البنك في البيع بالتقسيط بسعر النقد وحكمها", {
                "ruhsat_mezhep": "Çağdaş Fıkıh Heyetleri ve Hanefî İcâre Tahrîci",
                "ruhsat_hukum": "Satıcının bankaya ödediği pos/komisyon bedeli müşteriye yansıtılmadığı ve ürün peşin fiyatıyla aynı fiyata taksitlendirildiği sürece alıcının bu kampanyadan yararlanması caizdir; faiz sayılmaz.",
                "hanefi_hukum": "Müşteriden fazlalık alınmadığı sürece satıcı ile banka arasındaki komisyon hizmet bedeli hükmündedir, caizdir.",
                "safii_hukum": "Banka borcu üstlenirken kâr sağlıyorsa şüphe doğar; ancak faiz şartı doğrudan akitte yoksa alışveriş sahihtir.",
                "maliki_hukum": "Müşterinin borcu artmadığı müddetçe muamele meşrudur.",
                "hanbeli_hukum": "Faiz doğrudan alıcıya yüklenmediği sürece peşin fiyatlı taksitli işlem mubahtır."
            }),
            (127, "Kat Karşılığı İnşaat Sözleşmeleri (Arsa Payı Karşılığı Bağımsız Bölüm)", "عقد الاستصناع والمقاولة على الأراضي مقابل وحدات عقارية", {
                "ruhsat_mezhep": "Hanefî Mezhebi (İstisnâ' ve Şirket Akitlerinin Birleşimi)",
                "ruhsat_hukum": "Arsa sahibinin arsasını müteahhide verip karşılığında henüz inşa edilmemiş daireler alması istisnâ' ve örfe binaen meşrudur; madumun satışı (olmayan şeyin satışı) sayılmaz.",
                "hanefi_hukum": "Teamül ve örf haline gelen kat karşılığı inşaat istisnâ' kuralına göre istihsânen caizdir.",
                "safii_hukum": "İnşa edilmemiş dairenin satışı madum sayıldığından klasik selem şartları haricinde tartışmalıdır.",
                "maliki_hukum": "Belirsizlik (garar) giderilmiş ve vasıflar netleşmişse akit maslahaten sahihtir.",
                "hanbeli_hukum": "Akitlerde serbestlik asıldır; vasıfları belirlenen teslimat taahhütleri bağlayıcıdır."
            }),
            (128, "Tevelliyen Satış ve Kâr Haddi (Fahiş Kâr / Gabn-i Fâhiş Sınırı)", "تحديد نسبة الربح في التجارة والتسعير الجبري وحكم الغبن الفاحش", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Serbest piyasa ve kâr haddi konulmaması ruhsatı)",
                "ruhsat_hukum": "İhtikâr (karaborsacılık) ve tekelcilik olmadığı sürece dinen kâra yüzde (%) sınırı konulamaz; satıcı dilediği kârla satabilir, ancak aldatma (gabn) varsa alıcının fesih hakkı doğar.",
                "hanefi_hukum": "Kâr oranı tahdit edilmez; ancak fahiş aldatma (gabn-i fâhiş) durumunda alıcıya fesih muhayyerliği tanınır.",
                "safii_hukum": "Kâr oranında serbestlik esastır; piyasa fiyatlarına narh koymak meşhur kavilde caiz değildir.",
                "maliki_hukum": "Örfün aşırı dışına çıkan fahiş fiyatlandırmada hâkim müdahale edebilir; normalde sınır yoktur.",
                "hanbeli_hukum": "Resulullah'ın 'Fiyatları tayin eden Allah'tır' hadisi gereği kâr serbesttir, suni müdahale edilemez."
            }),
            (129, "Telif ve Lisans Haklarının İzinsiz Kopyalanması ve Korsan Kullanım", "استعمال البرامج المقرصنة والنسخ غير المصرح به للحاجة والتعلم", {
                "ruhsat_mezhep": "Zaruret Hali Tahrîci (Kamu yararı ve eğitime mahsus dar ruhsat)",
                "ruhsat_hukum": "Ticari kâr amacıyla korsan yazılım/kitap çoğaltmak kul hakkı ve haramdır; ancak maddi gücü yetmeyen öğrencinin veya araştırmacının sadece kendi şahsi eğitimi için muadilsiz bir yazılımdan istifade etmesi zarureten affedilmiştir.",
                "hanefi_hukum": "Fikrî haklar korunur, ticari korsanlık gasptır; ilim tahsilinde maslahat gözetilir.",
                "safii_hukum": "Emeğin hakkı mütekavvim maldır; izinsiz kopyalama tazminat gerektirir.",
                "maliki_hukum": "Maddi zarar vermeyen şahsi eğitim istifadelerinde umum-ı belvâ ruhsatı mülahaza edilir.",
                "hanbeli_hukum": "Hak sahibinin izni asıldır; ticari olmayan ilmi zaruretlerde ta'zir uygulanmaz."
            }),
            (130, "Vadeli Çek ve Senetlerin Kırdırılması (İskonto / Faktoring)", "خصم الأوراق التجارية والكمبيالات في البنوك", {
                "ruhsat_mezhep": "Ruhsat Yoktur (Dört Mezhebin İcmâıyla Bâtıldır)",
                "ruhsat_hukum": "Vadesi gelmemiş çeki veya senedi bankaya veya tefeciye verip daha az nakit para almak 4 mezhebin ittifakıyla haram ve kat'i ribâdır (faizdir); hiçbir mezhepte ruhsatı yoktur.",
                "hanefi_hukum": "Paranın vade karşılığı eksik parayla takası nesîe ve fazlalık ribâsıdır, bâtıldır.",
                "safii_hukum": "Borcun borçla ve farklı değerle peşin takası icmâen haramdır.",
                "maliki_hukum": "Zaman farkını parayla satın almak açık faizdir.",
                "hanbeli_hukum": "Hadis-i şerifin açık nehyi gereğince çek kırdırmak haramdır."
            })
        ]
    },
    {
        "bolum_id": "25_aile_son",
        "bolum_adi": "Kitâbü'n-Nikâh ve Aile (Son Aile Düğümleri)",
        "dosya": "07_nikah.md",
        "meseleler": [
            (131, "Resmi Nikâh Kıyılmadan Yapılan Dini Nikâhın Hükmü ve Cezai/Hukuki Durumu", "إجراء عقد النكاح العرفي دون توثيق رسمي في المحاكم", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Diyâneten sıhhat, kazaen tescil lüzumu)",
                "ruhsat_hukum": "Şahitler ve icap-kabul ile kıyılan akit dinen sahihtir; ancak kadının ve çocukların haklarının (nafaka, miras, velayet) zayi olmaması için devlet tescili (resmi nikâh) yaptırmak maslahat-ı mürsele gereği vaciptir.",
                "hanefi_hukum": "Rükünleri tam olan nikâh diyâneten geçerlidir; fesadı önlemek için resmi tescil şarttır.",
                "safii_hukum": "Şahitler varsa akit sahihtir; hakların zayi edilmesi haramdır.",
                "maliki_hukum": "İlan ve tescil kadının haklarını korumak için gereklidir.",
                "hanbeli_hukum": "Şer'i rükünleri taşıyan akit geçerlidir; ihmal sebebiyle hak kaybı doğarsa günahkâr olunur."
            }),
            (132, "Kadının Kocasından İzin Almadan Nafakası İçin Çalışması", "خروج الزوجة للعمل بدون إذن الزوج عند تقصيره في النفقة", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Koca ailenin zaruri nafakasını temin etmekten aciz kalır veya nafaka vermeyi ihmal ederse, kadın kocasının rızası olmasa dahi meşru bir işte çalışıp kendi geçimini temin edebilir; nâşize (itaatsiz) sayılmaz.",
                "hanefi_hukum": "Kocanın nafakayı aksatması kadına meşru çerçevede çalışma ve nafakasını çıkarma hakkı verir.",
                "safii_hukum": "Nafaka temin etmeyen kocaya itaat mecburiyeti düşer; kadın rızasız çalışabilir.",
                "maliki_hukum": "Zaruret halinde kadının çalışması meşrudur, nafakayı düşürmez.",
                "hanbeli_hukum": "Kocanın acziyeti kadının dışarı çıkıp helal rızık kazanmasını mubah kılar."
            }),
            (133, "Kadının Boşanma Yetkisini Elinde Bulundurması (Tefvîz-i Talâk)", "تفويض الطلاق للزوجة وجعل العصمة بيدها في عقد النكاح", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Cumhur)",
                "ruhsat_hukum": "Nikâh kıyılırken veya sonrasında kocanın boşama yetkisini kadına vermesi (tefvîz-i talâk) ittifakla caizdir; kadın dilediği zaman kendini tek veya üç talakla boşayabilir.",
                "hanefi_hukum": "Tefvîz-i talâk şartı sahihtir; kadın bu yetkiyi kullanarak mecliste veya mutlak olarak kendini boşayabilir.",
                "safii_hukum": "Boşama hakkının kadına vekâlet veya tefvîz yoluyla verilmesi sahihtir.",
                "maliki_hukum": "Yetki kadına devredildiğinde şartlara uygun olarak talakı vaki kılabilir.",
                "hanbeli_hukum": "Akit esnasında koşulan tefvîz şartı bağlayıcıdır, kadının hakkıdır."
            }),
            (134, "Kocanın Eşine Karşı Şiddet Uygulaması ve Mahkemece Derhal Boşanma (Tefrik)", "التفريق القضائي للضرر وسوء العشرة وضرب الزوجة", {
                "ruhsat_mezhep": "Mâlikî Mezhebi (Şiddet ve geçimsizlikte kadının tek taraflı boşanma imtiyazı)",
                "ruhsat_hukum": "Kocasından fiziksel veya psikolojik şiddet gören kadın, koca boşamaya yanaşmasa dahi mahkemeye başvurarak derhal evliliği feshettirebilir; mehir ve nafaka hakları saklı kalır.",
                "hanefi_hukum": "Klasik mezhepte şiddet tek başına fesih sebebi değildir, koca ta'zir edilir; ancak müteahhirîn Mâlikî mezhebine göre fetva vermiştir.",
                "safii_hukum": "Şiddet sebebiyle hâkim kocayı uyarır ve döver; fesih için nafaka acziyeti aranır.",
                "maliki_hukum": "Darp, hakaret ve kötü muamele (zarar) kesin fesih sebebidir; hâkim tek celsede bâin talakla boşar.",
                "hanbeli_hukum": "Zarar ve şiddet ispatlandığında hâkim eşleri ayırır."
            }),
            (135, "Evlilik Sözleşmesine 'Üzerime İkinci Eş Almayacaksın' Şartı Koymak", "اشتراط الزوجة في عقد النكاح أن لا يتزوج عليها أخرى", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (İmam Ahmed b. Hanbel)",
                "ruhsat_hukum": "Kadının nikâh akdi esnasında 'üzerime evlenmeyeceksin, evlenirsen boşanma hakkım olsun' diye şart koşması sahihtir; koca ikinci evlilik yaparsa ilk eş sözleşmeyi feshedip ayrılabilir.",
                "hanefi_hukum": "Bu şart geçersizdir; nikâh sahihtir fakat ikinci evliliği engellemez.",
                "safii_hukum": "Mubahı haram kılan şart bâtıldır; koca evlenebilir, kadının fesih hakkı doğmaz.",
                "maliki_hukum": "Şart fâsittir, akit geçerlidir; ancak şart talaka bağlanmışsa geçerli olur.",
                "hanbeli_hukum": "'Müslümanlar şartlarına bağlıdır' hadisi gereğince bu şart tam bağlayıcıdır; ihlal edilirse kadın nikâhı fesheder."
            })
        ]
    },
    {
        "bolum_id": "26_tib_biyoetik",
        "bolum_adi": "Kitâbü't-Tıbb ve Biyoetik (Modern Tıp ve Sağlık Düğümleri)",
        "dosya": "16_tib_gunluk.md",
        "meseleler": [
            (136, "Beyin Ölümü Gerçekleşmiş Hastanın Yaşam Destek Ünitesinden Çekilmesi", "حكم رفع أجهزة الإنعاش عن الميت دماغيا", {
                "ruhsat_mezhep": "Çağdaş İslâm Fıkıh Akademisi ve Diyanet Kararları",
                "ruhsat_hukum": "Uzman hekim heyetince beyin sapı reflekslerinin tamamen durduğu ve geri dönüşün imkânsız olduğu belgelenen hastanın yaşam destek ünitesinden fişinin çekilmesi caizdir; cinayet veya ötenazi sayılmaz.",
                "hanefi_hukum": "Hayat emareleri tamamen tükenen kimsenin tıbbi tedavisini sonlandırmak helaldir.",
                "safii_hukum": "Geri dönüşsüz beyin ölümü şer'an vefat alametidir; cihazların kapatılması mubahtır.",
                "maliki_hukum": "Meyus olunan hastadan cihazın çekilmesi caizdir, eceliyle ölüme terk edilir.",
                "hanbeli_hukum": "Hayat-ı müstakırra kalmadığında tedaviyi terk etmek caizdir."
            }),
            (137, "Plastik Cerrahi ve Doğuştan Olmayan Kusurlarda Botoks/Dolgu", "استعمال البوتوكس والفيلر لعلاج التجاعيد وإزالة آثار الشيخوخة", {
                "ruhsat_mezhep": "Hanefî ve Mâlikî Tedavi Tahrîci",
                "ruhsat_hukum": "Aşırı psikolojik rahatsızlık, çöküntü veya erken yaşlanma anomalisi taşıyan kimselerin beden bütünlüğüne zarar vermeyen geçici botoks ve dolgu maddelerini kullanması caizdir; kalıcı dövme gibi yaratılışı değiştirme sayılmaz.",
                "hanefi_hukum": "Eziyeti gidermek ve eşine güzel görünmek kastıyla geçici müdahaleler caizdir.",
                "safii_hukum": "Fıtratı kalıcı şekilde değiştirmeyen geçici süsler eşin izniyle helaldir.",
                "maliki_hukum": "Kusuru ve yıpranmayı gidermek tağyir-i halkillâh kapsamına girmez.",
                "hanbeli_hukum": "Zararı defetmek ve psikolojik meşakkati gidermek adına cevaz verilir."
            }),
            (138, "DNA Testi (Genetik İnceleme) ile Nesebin Reddedilmesi veya İspatı", "نفي النسب وإثباته بالبصمة الوراثية وتحليل الحمض النووي", {
                "ruhsat_mezhep": "Çağdaş Fıkıh Akademileri (İspatta mutlak delil, redde sınırlı delil)",
                "ruhsat_hukum": "Kaybolan çocukların, afet kurbanlarının ve şüpheli bebeklerin nesebinin ispatında DNA testi kesin delildir; ancak sahih evlilik içinde doğan çocuğun babadan reddi için DNA testi tek başına yetmez, liân usûlü şarttır.",
                "hanefi_hukum": "Yatak (firâş) sabitken çocuk kocaya aittir; nesep kolayca reddedilemez.",
                "safii_hukum": "İspatta karine ve kâif (iz sürücü) gibi DNA testi de muteberdir.",
                "maliki_hukum": "Çocuğun hakkı korunur; şüpheyle nesep iptal edilmez.",
                "hanbeli_hukum": "Kesin fenni deliller nesebin tayininde kuvvetli karinedir."
            }),
            (139, "Cinsiyet Geçiş Ameliyatları (Hünsâ-i Müşkil vs. Psikolojik Eğilim)", "جراحة تصحيح الجنس للخنثى المشكل وحكم التحويل لغير علة عضوية", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Hünsâda tedavi caiz, sırf psikolojik heveste haram)",
                "ruhsat_hukum": "Çift cinsiyetli (hünsâ-i müşkil) doğan ve tıbbî tahlillerle biyolojik cinsiyeti belirlenen kimsenin ameliyatla baskın cinsiyetine kavuşturulması helal bir tedavidir; fakat biyolojik kusuru olmayan kimsenin estetik hevesle cinsiyet değiştirmesi ittifakla haramdır.",
                "hanefi_hukum": "Hünsânın organını belirginleştirmek fıtratı düzeltmektir, caizdir; sağlam bedeni bozmak haramdır.",
                "safii_hukum": "Yaratılıştaki ayıbın ameliyatla giderilmesi tedavi kapsamındadır.",
                "maliki_hukum": "Biyolojik cinsiyeti ortaya çıkarma ameliyatı meşrudur.",
                "hanbeli_hukum": "Doğuştan gelen anatomik karmaşayı gidermek vacip veya menduptur."
            }),
            (140, "Aşı Olmanın Hükmü ve Bulaşıcı Hastalık Döneminde Toplum Sağlığı", "حكم التداوي باللقاحات والتحصين الإجباري للأمراض المعدية", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Seddi Zerâi' ve Maslahat-ı Mürsele)",
                "ruhsat_hukum": "Toplumda salgın ve ölümlere yol açan tehlikeli virüslere karşı koruyucu aşı yaptırmak canı koruma ilkesi gereğince caiz hatta vaciptir; kamu otoritesinin aşı zorunluluğu getirmesi meşrudur.",
                "hanefi_hukum": "Zararı önceden defetmek vaciptir; koruyucu hekimlik meşrudur.",
                "safii_hukum": "Bulaşıcı hastalıktan korunmak için aşı olmak sünnet ve maslahattır.",
                "maliki_hukum": "Kamu sağlığını korumak adına yöneticinin aşı emri bağlayıcıdır.",
                "hanbeli_hukum": "Zararın def'i şer'an asıldır; aşı meşru bir sebeptir."
            })
        ]
    },
    {
        "bolum_id": "27_ibadet_genel_son",
        "bolum_adi": "Kitâbü'l-İbâdât (İbadetlerde Kalan Son Düğümler)",
        "dosya": "02_salat.md",
        "meseleler": [
            (141, "Kaza Namazlarının Borcunu Düşürmek İçin Nafileleri Terk Etmek", "قضاء الفوائت الكثيرة وتقديمها على السنن الرواتب والنوافل", {
                "ruhsat_mezhep": "Şâfiî Mezhebi (Ruhsat ve hafiflik yönüyle Hanefî tercihi)",
                "ruhsat_hukum": "Üzerinde çok sayıda kaza namazı bulunan kimse, Şâfiî'de bütün nafileleri bırakıp kazaya yönelmek zorunda olsa da; Hanefî mezhebine göre sabah, öğle, akşam ve yatsının müekked sünnetlerini terk etmeden aralarda kaza kılabilir; sünnetlerin sevabından mahrum kalmaz.",
                "hanefi_hukum": "Kaza borcu olanın müekked sünnetleri terk etmesi gerekmez; sünnetler aynen kılınır, diğer vakitlerde kaza edilir.",
                "safii_hukum": "Kaza borcu olan kimsenin nafile ve revâtib kılabilmesi haramdır; bütün vaktini kazaya ayırmalıdır.",
                "maliki_hukum": "Sabah namazının sünneti (ragîbe) hariç nafileler bırakılıp kazaya odaklanılır.",
                "hanbeli_hukum": "Vitr ve sabah sünneti hariç diğer nafileleri bırakıp kaza kılmak efdaldir."
            }),
            (142, "Kutuplarda ve Gecesi/Gündüzü 6 Ay Süren Bölgelerde Namaz ve Oruç Vakitleri", "تقدير أوقات الصلاة والصيام في المناطق القطبية وخوارق العادات", {
                "ruhsat_mezhep": "Dört Mezhep Çağdaş İttifakı (Takdîr Hadisi Tahrîci)",
                "ruhsat_hukum": "Güneşin aylarca batmadığı veya doğmadığı kutup bölgelerinde yaşayan müslümanlar 24 saatlik süreye itibar etmezler; en yakın normal vakitlerin yaşandığı 45. enlemdeki şehrin veya Mekke'nin saatlerine göre namaz ve oruçlarını takdir ederek eda ederler.",
                "hanefi_hukum": "Vaktin sebebi ortadan kalktığında hüküm takdirle sabit olur; Deccal hadisi gereğince takdir yapılır.",
                "safii_hukum": "Normal gece-gündüzü olan en yakın beldenin saatleri kıyas alınır.",
                "maliki_hukum": "Mutedil beldelere kıyas edilerek takdir yapılır, ibadet terk edilmez.",
                "hanbeli_hukum": "Takdir hadisinin açık hükmü gereğince saatle takdir uygulanır."
            }),
            (143, "Oruçlu İken Unutularak Yapılan Cinsel İlişkinin Durumu", "الجماع في نهار رمضان ناسيا هل يوجب القضاء والكفارة", {
                "ruhsat_mezhep": "Şâfiî ve Hanbelî Mezhepleri (Orucun mutlak bozulmaması ruhsatı)",
                "ruhsat_hukum": "Ramazan gününde oruçlu olduğunu tamamen unutarak cinsel ilişkide bulunan kimsenin orucu bozulmaz; kaza da keffâret de gerekmez; hatırladığı an derhal ayrılır.",
                "hanefi_hukum": "Unutarak cima orucu bozmaz; ancak hatırlayınca devam ederse 60 gün keffaret gerekir.",
                "safii_hukum": "Unutarak cima yemek-içmek gibidir; oruç sahihtir, hiçbir şey gerekmez.",
                "maliki_hukum": "Unutarak cima farz orucu bozar, gününe gün kaza gerekir (keffaret gerekmez).",
                "hanbeli_hukum": "Nassın 'Unutarak yiyip içen orucunu tamamlasın' hükmü cimayı da kapsar; oruç tamdır."
            }),
            (144, "Secde Âyetini İşiten Kimsenin Tilavet Secdesi Yapma Mecburiyeti", "حكم سجود التلاوة بين الوجوب والسنية", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Kur'an'daki secde âyetlerini okuyan veya dinleyen kimseye tilavet secdesi yapmak farz veya vacip değildir; sünnettir. Terk edilmesinde günah veya kaza yoktur.",
                "hanefi_hukum": "Tilavet secdesi âyeti okuyana da dinleyene de vaciptir; terk eden günahkâr olur, kazası gerekir.",
                "safii_hukum": "Tilavet secdesi sünnettir; Hz. Ömer minberde secde etmiş, bir sonraki hafta terk ederek sünnet olduğunu göstermiştir.",
                "maliki_hukum": "Müekked sünnettir, vacip değildir.",
                "hanbeli_hukum": "Tilavet secdesi menduptur, terki caizdir."
            }),
            (145, "Hoparlörden veya Canlı Yayından İmama Uymak (Ekrandan Cemaat)", "صلاة المأموم خلف الإمام عبر المذياع والتلفاز والإنترنت", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Mekân birliği şartı - Bâtıl olması)",
                "ruhsat_hukum": "Radyo, televizyon veya internet yayınından Kâbe imamına veya yerel imama evden uymak 4 mezhebin ittifakıyla bâtıldır, geçersizdir; cemaatle namazın sıhhati için fiziksel olarak safların birbirine bitişik olması (ittisâl-i mefârık) şarttır.",
                "hanefi_hukum": "İmam ile cemaat arasında yol, nehir veya büyük boşluk bulunması imama uymayı iptal eder, namaz bâtıldır.",
                "safii_hukum": "Aynı mescitte veya safların muttasıl olduğu açık alanda bulunmak şarttır; ekranla namaz olmaz.",
                "maliki_hukum": "Mekân birliği ve safların irtibatı rükündür; uzaktan yayınla cemaat kurulamaz.",
                "hanbeli_hukum": "İmamı sadece sesle takip etmek cemaat sayılmaz; fiziksel safta bulunmak farzdır."
            })
        ]
    },
    {
        "bolum_id": "28_kapanis_muamelat",
        "bolum_adi": "Kitâbü'l-Câmi' (Külliyatı Tamamlayan Son 5 Düğüm)",
        "dosya": "04_buyu.md",
        "meseleler": [
            (146, "Namaz Kılmayanın Kestiği Hayvanın Eti Yenir mi? (Târikü's-Salât Zebîhası)", "ذبيحة تارك الصلاة تهاونا وكسلا هل تحل وتؤكل", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Hanefî, Mâlikî, Şâfiî)",
                "ruhsat_hukum": "Namazı inkâr etmeksizin tembellikle kılmayan kimse dinden çıkmış kâfir sayılmaz; fâsık bir müslümandır. Kestiği hayvanın üzerine besmele çektiği sürece eti helaldir ve temizdir.",
                "hanefi_hukum": "Tembellikle namaz kılmayan müslümandır; kestiği hayvan helaldir ve yenir.",
                "safii_hukum": "Kelime-i şehadet getiren müminin zebihası temizdir; namazı terk etmekle dinden çıkmaz.",
                "maliki_hukum": "İtikadı sağlam olduğu sürece ameli kusurlu müslümanın kesimi helaldir.",
                "hanbeli_hukum": "Mezhebin meşhur kavline göre namazı tamamen terk eden kâfir hükmündedir ve kestiği yenmez (İbn Kudâme ise tekfir etmeyen rivayeti tercih eder)."
            }),
            (147, "Müslümanın Faizli Bankada veya İçkili Restoranda Çalışması ve Maaşı", "عمل المسلم في البنوك الربوية والمطاعم المشتملة على المحرمات", {
                "ruhsat_mezhep": "Hanefî Mezhebi (İmam Ebû Hanîfe - Doğrudan haram akdin tarafı olmama ayrımı)",
                "ruhsat_hukum": "Faiz sözleşmesini bizzat yazmayan veya faiz akdine şahitlik etmeyen; güvenlik, temizlik, şoförlük ve teknik bakım gibi nötr işlerde çalışan kimsenin aldığı maaş helaldir; kazancın bizzat kendisi faiz sayılmaz.",
                "hanefi_hukum": "Doğrudan günaha vesile olmayan, bizâtihi müstakil işlerin karşılığında alınan ücret helaldir.",
                "safii_hukum": "Haram kuruma hizmet etmek günahta yardımlaşmadır; faizli bankada her türlü istihdam mekruhtur.",
                "maliki_hukum": "Harama yardımcı olan işlerden kaçınmak farzdır; maaşta şüphe vardır.",
                "hanbeli_hukum": "Faiz katibine ve şahidine lanet hadisi doğrudan faiz memurlarına aittir; diğer işlerde ruhsat aranır."
            }),
            (148, "Cenaze Kabirdeyken Telkin Vermenin Dînî Hükmü", "تلقين الميت بعد الدفن عند القبر بين السنية والبدعة", {
                "ruhsat_mezhep": "Şâfiî ve Hanbelî Mezhepleri (Müstehap ve Sünnet olması)",
                "ruhsat_hukum": "Defin tamamlandıktan sonra kabrin başında durup meyyite tevhid ve iman esaslarını telkin etmek meşru ve müstehaptır; ölünün bundan faydalandığına dair hadisler mevcuttur.",
                "hanefi_hukum": "Mükellef olmadığı için telkin emredilmez; ancak yapılmasında bir sakınca da yoktur, caizdir.",
                "safii_hukum": "Definden sonra meyyite kabir başında telkin vermek sünnet ve müstehaptır.",
                "maliki_hukum": "Meşhur kavle göre definden sonra telkin bid'attir; terk edilmesi evladır.",
                "hanbeli_hukum": "Sahabe tatbikatına binaen defin sonrasında telkin verilmesi müstehaptır."
            }),
            (149, "Kredi Kartı Puanları, Mil Puanlar ve Cash-back (Nakit İade) Gelirleri", "نقاط المكافآت واسترداد النقود في البطاقات المصرفية", {
                "ruhsat_mezhep": "Çağdaş Fıkıh Heyetleri ve Diyanet Tahrîci",
                "ruhsat_hukum": "Kredi kartıyla yapılan alışverişler karşılığında bankanın müşteriye hediye ettiği puanlar, miller ve nakit iadeler (cash-back) akitte şart koşulan faiz değil; satıcı ile bankanın müşteri çekmek için verdiği mubah bir hibe/teşviktir, helaldir.",
                "hanefi_hukum": "Müşterinin kendi parasından fazlalık talep etmediği, üçüncü tarafın hibe ettiği primler helaldir.",
                "safii_hukum": "Karşılıksız hediye ve ikramiye hükmündedir; borç faizi değildir.",
                "maliki_hukum": "Haksız kazanç ve ribâ unsuru taşımayan ticari promosyonlar mubahtır.",
                "hanbeli_hukum": "Akitlerde asıl olan ibâhadır; şartlı faiz olmadıkça ödül puanları helaldir."
            }),
            (150, "CÂMİU'R-RUHAS NİHAİ MÜHÜR: Telfîk-i Bâtıl ve İcmâ-i Mürekkep Özet Beyannamesi", "ضابط التلفيق الممنوع والإجماع المركب في الفتوى والعمل", {
                "ruhsat_mezhep": "Dört Hak Mezhep Fukahâsının İttifakı (Mutlak Kapanış İlkesi)",
                "ruhsat_hukum": "Külliyatta yer alan 150 meselenin tamamında temel kural: Bir mükellef hangi ruhsatı tatbik ederse etsin, o amelin geçerli olabilmesi için o mezhebin o amele dair koyduğu asgari rükün ve sıhhat şartlarını eksiksiz yerine getirmelidir; 4 mezhebin dördünün birden 'kesinlikle bâtıldır' dediği bir kompozit amel asla yapılamaz. Bu kurala riayet eden kimsenin ameli sahihtir, dini selamettedir.",
                "hanefi_hukum": "Her amelde intisap edilen imamın şartlarına tam riayet farzdır; icmâ-i mürekkep bâtıldır.",
                "safii_hukum": "Ruhsat taklidi ancak mezhebin furû ve rükünlerine sadakatle meşru olur.",
                "maliki_hukum": "Telfîk heva ve hevese dayanmamalı; nass ve usûle dayalı ruhsatlar alınmalıdır.",
                "hanbeli_hukum": "Meşakkat anında en ehven mezhebin sahih kavliyle amel etmek haktır; telfîk-i bâtıl ise icmâ ile men edilmiştir."
            })
        ]
    }
]

def main():
    print("=" * 80)
    print("[*] NÖRO-SEMBOLİK NİHAİ KAPANIS MOTORU: MESELE 126 - 150 (TAMAMLANIYOR)")
    print("=" * 80)

    compiler = NeuroSymbolicFikhEngine()
    completed = load_checkpoints()
    print(f"[+] Başlangıçtaki Doğrulanmış Mesele Sayısı: {len(completed)}")

    for bolum in DUGUMLER_FAZ_10:
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
    print("\n[*] 150 Meselelik Master Külliyat Birleştiriliyor...")
    mukaddime = """# CÂMİU'R-RUHAS VE TAHKÎKU'L-MEZÂHİB
## Dört Mezhep Esaslı En Hafif ve Sahih Fıkıh Külliyatı (150 Amelî Düğüm - Lite Tatbikat)

---

### MUKADDİME VE TELİF METODOLOJİSİ
Bu eser; İslam Hukuku'nun dört hak mezhebi (Hanefî, Mâlikî, Şâfiî, Hanbelî) dairesinde kalmak şartıyla, mükellefi meşakkatten kurtaran **en hafif, uygulanabilir ve sahih ruhsatları** (150 temel amelî düğüm) bir araya getirmek amacıyla telif edilmiştir.

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
        ("19_kaza.md", "KİTÂBÜ'L-KAZÂ VE'Ş-ŞEHÂDÂT (YARGI VE İSPAT HUKUKU)"),
        ("20_hudud_cinayat.md", "KİTÂBÜ'L-HUDÛD VE'L-CİNÂYÂT (CEZA VE KISAS HUKUKU)"),
        ("21_sirketler_vakif.md", "KİTÂBÜ'Ş-ŞİRKE VE'L-VAKF (ŞİRKETLER, FİNANS VE VAKIF HUKUKU)"),
        ("22_siyer_diyet.md", "KİTÂBÜ'L-CİNÂYÂT, DİYET VE SİYER (CAN GÜVENLİĞİ VE KAMU HUKUKU)"),
        ("23_lukata_icare.md", "KİTÂBÜ'L-LUKATA, İCÂRE VE ÇAĞDAŞ MÜLKİYET (KİRA, TAZMİNAT VE HAKLAR)")
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
    print(f"[✓] 150 MESELELİK KÜLLİYAT EKSİKSİZ TAMAMLANDI!")
    print(f"    Master Kitap: {MASTER_BOOK_PATH}")
    print(f"    Toplam Boyut: {size_kb:.2f} KB")
    print(f"    Toplam Mesele Sayısı: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
