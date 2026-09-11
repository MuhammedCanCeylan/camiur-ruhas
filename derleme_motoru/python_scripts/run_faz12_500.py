import os
import sys
import json
import time
from neuro_symbolic_engine import (
    NeuroSymbolicFikhEngine, OUTPUT_BOOK_DIR, CHAPTERS_DIR, 
    MASTER_BOOK_PATH, CHECKPOINT_FILE
)

# 351 - 500 ARASI SON AMELÎ VE ÇAĞDAŞ DÜĞÜM HAVUZU (150 MESELE)
MESELER_FAZ_12 = [
    # ÇAĞDAŞ FİNANS, E-TİCARET VE DİJİTAL SÖZLEŞMELER (351 - 390)
    (351, "Merkeziyetsiz Finansta (DeFi) Otomatik Likidite Havuzlarına Katılmak", "المشاركة في مجمعات السيولة اللامركزية ديفاي", "Çağdaş Fıkıh (Şirket-i İbâha)", "Faiz getirisi veya kumar protokolü içermeyen spot takas havuzlarına katkı sunarak işlem komisyonu almak mubahtır."),
    (352, "Akıllı Cihazların ve IoT Sensörlerinin Otomatik Verdiği Siparişlerin Sıhhati", "إبرام عقود البيع عبر إنترنت الأشياء والطلب الآلي", "Hanbelî (Fiilî Teâti/İcazet)", "Kullanıcının önceden parametrelerini belirleyip izin verdiği otomatik siparişler zımni irade beyanıyla geçerlidir."),
    (353, "E-Ticarette Fiyat Karşılaştırma Botları ile Fiyat Algoritması Kurmak", "استعمال خوارزميات التسعير التلقائي في المتاجر", "Cumhur Fukahâsı", "Piyasa tekelciliği (ihtikâr) ve suni şişirme yapılmadıkça arz-talebe göre dinamik fiyatlandırma caizdir."),
    (354, "Dijital Oyun Yayıncılarının Sponsorlu Kumar veya Kasa Açma Reklamı Yapması", "الترويج لألعاب المراهنات وصناديق الحظ في البث المباشر", "Ruhsat Yoktur (Harama Aracılık)", "Kumar ve şans oyunlarının reklamını yapmak ve bu yoldan sponsorluk geliri elde etmek icmâen haramdır."),
    (355, "Geri İade Edilen Bozuk/Kusurlu Ürünlerin 'Yenilenmiş' (Refurbished) Olarak Satışı", "بيع الأجهزة الإلكترونية المجددة بعد بيان العيب", "Dört Mezhep İttifakı (Beyan Şartı)", "Tamir edildiği ve yenilendiği açıkça belirtilerek satılan ikinci el veya revize cihazların satışı caizdir."),
    (356, "Freelance Platformlarının (Upwork, Fiverr) Kestiği Hizmet Komisyonu", "عمولات منصات العمل الحر الرقمية وحكم اقتطاعها", "Hanefî ve Mâlikî (Simsârlık/İcâre)", "İş bulma ve ödeme güvenliği sağlama karşılığında platformun aldığı aracılık komisyonu helaldir."),
    (357, "Banka Kredi Kartı Aidatının Müşteriden İtiraz Edilmeksizin Kesilmesi", "رسوم تجديد البطاقات الائتمانية السنوية ومصروفات الحساب", "Çağdaş Fıkıh Heyetleri", "Banka tarafından sunulan fiili operasyonel kart maliyeti ve hizmet karşılığı olan makul aidatlar caizdir."),
    (358, "E-İmza ve Biyometrik Onayla Yapılan Kredi/Alışveriş Sözleşmeleri", "حجية التوقيع الإلكتروني والبصمة الرقمية في العقود", "Dört Mezhep İttifakı (Yazılı Delil)", "Sahtecilik riski engellenmiş yasal dijital imzalar şer'an el yazısı imza gibi bağlayıcıdır."),
    (359, "Hisse Senedi Bölünmesinde (Bedelsiz Sermaye Artırımı) Pay Dağıtımı", "توزيع الأسهم المجانية في الشركات المساهمة", "Dört Mezhep İttifakı", "Şirket iç kaynaklarının sermayeye eklenmesiyle ortaklara bedelsiz hisse verilmesi mevcut mülkiyetin tescilidir, helaldir."),
    (360, "Yurt Dışı Kargo Gönderilerinde Beyan Edilen Değer Üzerinden Sigorta Bedeli", "رسوم التأمين على الشحنات الدولية ضد التلف والضياع", "Zaruret Tahrîci", "Uluslararası taşımacılıkta malın zayi olma riskine karşı zorunlu veya örfi kargo güvence bedeli caizdir."),
    (361, "İkinci El Telefon Satışında İçindeki Şahsi Verilerin Silinmesi Sorumluluğu", "مسؤولية مسح البيانات الشخصية قبل بيع الأجهزة الرقمية", "Dört Mezhep İttifakı (Mahremiyet)", "Kişinin kendi ve başkalarının mahrem verilerini kalıcı silerek satması farzdır; veriyi kötüye kullanan alıcı gaspçı sayılır."),
    (362, "E-Ticarette Yanlışlıkla Çok Düşük Girilen Sistem Hatalı Fiyatla Alışveriş", "استغلال خطأ التسعير الإلكتروني وشراء السلعة بدون ثمن المثل", "Hanefî ve Hanbelî (Fahiş Gabn/Fesih)", "Sistem hatasıyla 10.000 liralık malın 10 liraya düşmesini fırsat bilip almak batıldır; satıcının fesih hakkı vardır."),
    (363, "Borsada Temettü Dağıtmayan Büyüme Hisselerinden Al-Sat Yapmak", "المتاجرة بأسهم النمو التي لا توزع أرباحا نقدية", "Çağdaş Fıkıh Heyetleri", "Şirket faaliyetleri meşru olduğu sürece sermaye kazancı ve hisse değer artışı amacıyla hisse ticareti caizdir."),
    (364, "Yurt Dışı Eğitimi İçin Verilen Faizli Öğrenci Kredileri (Student Loan)", "قروض الطلاب الجامعية ذات الفوائد في بلاد الغرب", "Ruhsat Yoktur (Zaruret Sınırı)", "Alternatif burs veya çalışma imkânı varken faizli kredi almak haramdır; ancak hayati mezuniyet mecburiyetinde ızdırar kuralları aranır."),
    (365, "Telif Hakkı Olan Dijital Kitap ve Makalelerin İntihal (Plagiarism) Edilmesi", "الانتحال العلمي والسطو على الأبحاث والمؤلفات", "Dört Mezhep İttifakı (Haram/Hırsızlık)", "Başkasına ait ilmî eseri kaynak göstermeden kendi eseri gibi yayımlamak sahtekârlık ve hırsızlıktır."),
    (366, "Marketlerin Sadakat Kartlarında (Loyalty Card) Biriken İndirimlerin Kullanımı", "نقاط الولاء والخصومات المتراكمة في المتاجر", "Dört Mezhep İttifakı (Hibe/İskonto)", "Alışveriş hacmine göre marketin sunduğu indirim puanları ve bedava ürünler mubah bir satıcı hibesidir."),
    (367, "Şirket Ortaklarının Birbirinden Habersiz Şirket Adına Borçlanması", "استدانة أحد الشركاء على ذمة الشركة دون تفويض", "Hanefî ve Mâlikî Şirket Usûlü", "Yetki sınırlarını aşarak yapılan borçlanma diğer ortakları bağlamaz; borç bizzat işlemi yapan ortağın zimmetindedir."),
    (368, "Sosyal Medyada 'Beğeni ve Takipçi' Satın Almanın Dinî Boyutu", "شراء المتابعين والإعجابات الوهمية لترويج الحسابات", "Ruhsat Yoktur (Sahtecilik/Aldatma)", "Gerçek olmayan hesaplarla takipçi sayısını yüksek gösterip reklam veya güven devşirmek nehyedilen aldatmadır."),
    (369, "Mesken Aboneliklerinde Güvence Bedelinin (Depozito) Yıllar Sonra Değer Kaybıyla İadesi", "استرداد مبالغ التأمين والودائع العقارية بنقص القوة الشرائية", "İmam Ebû Yûsuf ve Mâlikî Tahrîci", "Ev sahibinin aldığı nakit depozitoyu enflasyona karşı altın/döviz endeksli güncellemesi veya reel zararı önlemesi adalettir."),
    (370, "Otoparklarda 'Meydana Gelen Hasarlardan İşletmemiz Sorumlu Değildir' Levhası", "اشتراط نفي الضمان في مواقف السيارات والودائع المأجورة", "Cumhur Fukahâsı (Şartın Bâtıllığı)", "Ücretli otopark ecîr-i müşterek ve vedia hükmündedir; açık kusur ve ihmalden doğan hasarlarda bu levha işletmeyi mesuliyetten kurtarmaz."),
    (371, "Yazılım Projelerinde Müşterinin İşi Kabul Etmeyip Ödemeyi Durdurması", "فسخ عقد البرمجة عند عدم مطابقة المواصفات المشروطة", "Hanefî (İstisnâ' Muhayyerliği)", "Teslim edilen yazılım şartnamedeki vasıfları taşımıyorsa müşteri fesh edebilir; taşıyorsa keyfi fesih hakkı yoktur."),
    (372, "Döviz Büfelerinde Bozuk Para Olmadığı İçin Küsüratın Sakız veya Şekerle Verilmesi", "المصارفة مع تعويض الكسور بسلع تافهة", "Hanefî ve Şâfiî İhtilafı", "Sarf akdinde karşılıklı bedellerin tam teslimi şarttır; küsüratı rızayla bağışlamak caizdir, zorunlu mal dayatması akdi bozar."),
    (373, "Kripto Paralarda Kayıp Cüzdanların İçindeki Varlıkların Sahiplik Durumu", "الأموال الرقمية في المحافظ المفقودة مفاتيحها", "Hanefî (Lukatâ/Meyus Mal)", "Şifresi kalıcı kaybolan ve ulaşılamayan kripto varlıklar madum (hükmen yok) hükmündedir; zekât matrahından düşülür."),
    (374, "Maden Suyu, Gazlı İçecek ve Enerji İçeceklerinde Boğa Spermi (Taurin) İddiası", "مادة التورين في مشروبات الطاقة ومصدرها الكيميائي", "Dört Mezhep İttifakı (Tahkik)", "Sentetik laboratuvar üretimi taurin temizdir; necis veya hayvansal haram menşe içermedikçe tüketimi mubahtır."),
    (375, "Alışveriş Merkezlerindeki Çocuk Oyun Alanlarına Saatlik Ücret Ödemek", "استئجار ألعاب الأطفال والمدن الترفيهية بالساعة", "Dört Mezhep İttifakı (İcâre)", "Süre ve kullanım alanı belli olan eğlence ve oyun hizmetlerinin kiralanması caizdir."),
    (376, "Gözlük Çerçevesi ve Saatlerde Altın Kaplama (Mikron Altın) Kullanımı", "استعمال الساعات والنظارات المطلية بالذهب للرجال", "Hanefî ve Mâlikî Mezhepleri", "Ateşe tutulduğunda eriyip ayrışmayacak derecedeki cüzi altın kaplamaları erkeklerin aksesuar olarak kullanması caizdir."),
    (377, "Yurt Dışı İthalatında Zorunlu Olan Gözetim ve Standart Uygunluk Harçları", "رسوم الفحص والمطابقة الجمركية الإلزامية", "Dört Mezhep İttifakı", "Tüketici sağlığını korumak adına kamu otoritesinin koyduğu teknik denetim bedelleri helaldir."),
    (378, "İnternet Alışverişinde Satıcının Gönderdiği Hediyenin Ürün İadesinde Geri İstenmesi", "حكم الهدايا الترويجية المشروطة عند رد السلعة المبيعة", "Hanbelî Mezhebi (Şart Kuralı)", "Hediye ana satış şartına bağlı verildiğinden, ana akit feshedildiğinde hediyenin de iadesi şart koşulabilir."),
    (379, "Kendi Ürettiği Bir Ürüne Başka Markanın Etiketini Basarak Satmak (Fason Üretim)", "التصنيع للغير ووضع علامات تجارية مرخصة", "Dört Mezhep İttifakı (Lisans Şartıyla)", "Marka sahibinin resmi izni ve lisans sözleşmesiyle fason üretim meşrudur; taklit/korsan üretim haramdır."),
    (380, "Otellerin Açık Büfelerinde Doyduktan Sonra Tabağa Alınıp Çöpe Atılan Yemekler", "الإسراف في البوفيه المفتوح وحرمة إهدار الطعام", "Dört Mezhep İttifakı (Haram/İsraf)", "Yiyebileceğinden fazlasını tabağa alıp dökmek haramdır; otel yönetiminin israfı önleyici tedbir alması haktır."),
    (381, "Mobil Bankacılık Girişlerinde Parmak İzi ve Yüz Tanıma Güvenliği", "استعمال البصمة البيومترية في العمليات المصرفية", "Dört Mezhep İttifakı", "Kişinin malını ve hesabını korumak için biyometrik şifreleme kullanması caiz ve ihtiyattır."),
    (382, "Düğün Salonu Rezervasyonunun Düğün İptalinde Cayma Bedeli Kesintisi", "فسخ حجز قاعات الأفراح واقتطاع جزء من العربون", "Hanbelî Mezhebi (Urbûn/Tazmin)", "İşletmenin uğradığı fiili rezervasyon kaybı nispetinde makul tazminat kesmesi caizdir; fahiş ceza şartı iptal edilir."),
    (383, "Borsada Temettü Gelirlerinin Otomatik Olarak Yeni Hisseye Dönüştürülmesi (DRIP)", "إعادة استثمار الأرباح الموزعة تلقائيا في أسهم الشركة", "Dört Mezhep İttifakı", "Ortağın temettü alacağını şirketten nakit çekmeyip hisseye çevirmesi caiz bir sermaye artırımıdır."),
    (384, "Kullanılmayan Telefon Hatlarının Belirli Süre Sonra Operatörce İptali", "إلغاء خطوط الهاتف غير المستخدمة بعد مهلة محددة", "Hanefî ve Mâlikî (Akit Şartı)", "Sözleşmede önceden belirtilen inaktif hat kapatma kuralları kamu iletişim altyapısı maslahatıyla meşrudur."),
    (385, "Yurt Dışında Yaşayan Müslümanın Yerel Emeklilik Sandığından Maaş Alması", "الرواتب التقاعدية في الأنظمة التأمينية الغربية", "Çağdaş Fıkıh Heyetleri", "Devlete veya fona yatırılan primlerin karşılığı olarak emeklilik maaşı almak helal bir sosyal haktır."),
    (386, "Ortak Miras Malının Satışında Mirasçılardan Birinin Şüf'a (Önalım) Hakkı", "حق الشفعة للشريك الوارث في العقار الموروث", "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)", "Bölünmemiş ortak mülkte bir mirasçı payını yabancıya satarsa, diğer ortak mirasçı aynı bedeli ödeyerek malı öncelikle alma hakkına sahiptir."),
    (387, "İkinci El Eşya Alımında Çalıntı Mal Şüphesi Varsa Ne Yapılmalıdır?", "شراء السلع مع غلبة الظن بأنها مسروقة", "Ruhsat Yoktur (Harama İştirak)", "Çalıntı olduğu kesin veya galip zanla bilinen malı satın almak harama ortaklıktır, bâtıldır; derhal polise bildirilmelidir."),
    (388, "Uçak Biletlerinde İptal Edilemez (Promosyon) Biletin Mücbir Sebeple İadesi", "استرداد قيمة تذاكر الطيران غير القابلة للإلغاء عند المرض", "Hanefî Mezhebi (Özürle Fesih)", "Ağır hastalık veya vefat gibi elde olmayan mazeretlerde bilet bedelinin iadesi veya ertelenmesi fıkhi hakkaniyet gereğidir."),
    (389, "Dijital Yayıncılıkta Reklam Engelleyici (AdBlock) Kullanmanın Dinî Hükmü", "استعمال برامج حجب الإعلانات في المواقع المجانية", "Çağdaş Maslahat İhtilafı", "Kullanıcının virüs ve müstehcen içerikten korunmak için AdBlock kullanması caizdir; ancak sitenin emeğine karşı hakkaniyet gözetilmelidir."),
    (390, "İşçinin Performans Düşüklüğü Gerekçesiyle Tazminatsız İşten Atılması", "فصل العامل لضعف الإنتاجية دون تعويض", "İslam İş Hukuku (Zulüm Yasağı)", "Açık bir hırsızlık veya sabotaj olmadıkça sadece performans düşüklüğü gerekçesiyle işçiyi birikmiş tazminatından mahrum etmek zulümdür."),

    # MODERN TIP, CERRAHİ VE BİYOETİK DERİNLEŞMESİ (391 - 430)
    (391, "Yoğun Bakımda Kalbi Duran Hastaya Elektroşok ve CPR (Canlandırma) Yapılması", "الإنعاش القلبي الرئوي واستعمال الصدمات الكهربائية للمشرف على الموت", "Dört Mezhep İttifakı (Farz-ı Kifâye)", "Geri dönme umudu bulunan hastaya elektroşok ve masaj uygulamak canı kurtarma emri gereğince vaciptir."),
    (392, "Kısırlık Tedavisinde Mikroenjeksiyon (ICSI) ile Sperm Seçimi", "التلقيح المجهري وحقن الحيوان المنوي داخل البويضة", "Dört Mezhep İttifakı", "Nikâh bağı devam eden karı-kocanın kendi hücreleri arasında yapılan mikroenjeksiyon meşru bir tedavidir."),
    (393, "Doğum Sonrası Plesantanın (Eş) Tıbbi Cilt Maskelerinde Kullanılması", "بيع واستعمال المشيمة البشرية في مستحضرات التجميل", "Ruhsat Yoktur (İnsan Hürmeti)", "İnsanın parçası sayılan plasentanın ticareti ve kozmetikte kullanımı insanın mükerrem yaratılışı gereğince haramdır; toprağa gömülür."),
    (394, "Ağır Yara ve Yanıklarda Tıbbi Sülük (Hirudoterapi) Kullanımı ve Abdest", "التداوي بالعلق الطبي لامتصاص الدم الفاسد والطهارة", "Şâfiî ve Mâlikî Mezhepleri", "Sülükle tedavi mubahtır; sülüğün emdiği ve akmayan kan Şâfiî'de abdesti bozmaz, Hanefî'de akarsa bozar."),
    (395, "Ölümcül Hastalarda Organ Bağışı Kartı Taşımak ve Vasiyet Etmek", "حمل بطاقة التبرع بالأعضاء والوصية بها بعد الموت", "Dört Mezhep Çağdaş İttifakı", "Beyin ölümü şartıyla ve karşılıksız olmak kaydıyla organlarını bağışlamak sadaka-i câriye ve hayat kurtaran bir fazilettir."),
    (396, "Kulak Zarı Delik Olanların Su Kaçmaması İçin Tıkaçla Gusletmesi", "غسل الأذن مع وجود ثقب في الطبلة واستعمال السدادات", "Dört Mezhep İttifakı (Zarar Def'i)", "Kulağa su kaçması iltihap ve sağırlık riski doğuruyorsa kulağın içine su akıtılmaz, dışı yıkanır ve üzeri mesh edilir."),
    (397, "Göz Kuruluğu İçin Kullanılan Suni Gözyaşı Damlasının Oruca Etkisi", "استعمال قطرات الدموع الاصطناعية للصائم", "Dört Mezhep İttifakı (Bozmaması)", "Gözyaşı kanallarından boğaza inen eser miktar gıda maddesi olmadığından orucu bozmaz."),
    (398, "Kanserli Memenin Alınması (Mastektomi) Sonrası Silikon Protez Taktırmak", "ترميم الثدي وزراعة السيليكون بعد استئصال الورم", "Dört Mezhep İttifakı (Kusuru Giderme)", "Hastalık sebebiyle kaybedilen uzvun yerine estetik ve psikolojik bütünlük için silikon taktırmak meşru tedavidir."),
    (399, "Oruçlu İken Aşı ve Ağrı Kesici Olmayan Kas İçi İğne Vurulması", "الحقن العضلية والجلدية غير المغذية للصائم", "Çağdaş Fıkıh Heyetleri ve Diyanet", "Besleyici ve vitamin içerikli olmayan kas içi ve deri altı tedavi iğneleri tabii menfezden girmediği için orucu bozmaz."),
    (400, "Zorunlu Histerektomi (Rahmin Alınması) Sonrası Kadının Dini Hükmü", "استئصال الرحم جراحيا وانقطاع الحيض بالكلية", "Dört Mezhep İttifakı", "Rahmi alınan kadın artık hayız görmez; operasyon sonrası gelen kanamalar yara kanı (istihâza) hükmündedir, namaza engel olmaz."),
    (401, "Ağır Yanık Hastalarında Deri Hücresi Püskürtme (Skin Gun) Tedavisi", "رش الخلايا الجلدية الذاتية لالتئام الحروق", "Dört Mezhep İttifakı", "Hastanın kendi temiz dokusundan üretilen deri hücrelerinin püskürtülmesi meşru cerrahidir."),
    (402, "Şeker Hastalarının İnsülin İğnesini Oruçlu İken Karından Yapması", "حقن الإنسولين تحت الجلد لمرضى السكر في رمضان", "Çağdaş Fıkıh Heyetleri (Bozmaması)", "İnsülin gıda ve içecek hükmünde olmayıp hormon dengeleyici olduğundan orucu bozmaz."),
    (403, "Lokal Anestezi ile Yapılan Diş Çekimi ve Kanal Tedavisinde Yutulan İlaçlı Tükürük", "ابتلاع بقايا دواء حشو الأسنان والبنج غلبة للصائم", "Hanefî ve Mâlikî Mezhepleri", "Kaçınılması güç olan uyuşukluk hissi ve ilaç tadı kasten yutulmadığı sürece orucu ifsat etmez."),
    (404, "Kanser Tedavisinde Kemik İliği (Kök Hücre) Nakli ve Kan Grubunun Değişmesi", "زراعة النخاع العظمي وتغير فصيلة الدم وحكم النسب", "Dört Mezhep İttifakı", "Kemik iliği nakli caizdir; kan grubunun veya genetik dizilimin değişmesi nesep ve süt hısımlığını değiştirmez."),
    (405, "Gebelik Zehirlenmesinde (Preeklampsi) Annenin Hayatı İçin Bebeğin Erken Alınması", "إنهاء الحمل مبكرا لإنقاذ حياة الأم من تسمم الحمل", "Dört Mezhep İttifakı (Aslolan Anne)", "Annenin hayatı tehlikeye girdiğinde bebek tıbben kurtarılabilecek haftadaysa sezaryenle alınır, anne feda edilemez."),
    (406, "Mideye Salınan İlaç Kapsüllü Kameraların (Kapsül Endoskopi) Yutulması", "ابتلاع كبسولة الكاميرا الذكية لتصوير الجهاز الهضمي", "Dört Mezhep İttifakı", "Teşhis amaçlı yutulan katı cihazlar besin sağlamadığından oruç dışı vakitte yapılmalıdır; Ramazan'da gerekirse kaza edilir."),
    (407, "Ciltteki Vitiligo (Ala) Lekelerini Kapatmak İçin Yapılan Tıbbi Kamuflaj Boyaları", "الصبغ العلاجي لإخفاء بقع البهاق والبرص", "Cumhur Fukahâsı (Tedavi/Ayıp)", "Aşırı görsel ve psikolojik travma yaratan vitiligo lekelerini deri rengine boyamak meşru tedavidir."),
    (408, "Oruçlu Kimsenin Astım İlacını (Ventolin Fısfıs) Ciğerlerine Çekmesi", "استعمال بخاخ الربو الصدري في نهار رمضان", "Çağdaş Fıkıh Heyetleri / İbn Teymiyye Tahrîci", "Akciğerlere hava ile giden ve mideye ulaşmayan mikro gaz zerrecikleri susuzluk ve gıda gidermediğinden orucu bozmaz."),
    (409, "Ağır Görme Engellilere Rehber Köpek (Guide Dog) Edinme ve Evde Bakma Ruhsatı", "اقتناء كلب الدليل لفاقدي البصر ودخوله البيت", "Mâlikî Mezhebi (Zaruret ve Tahâret)", "Görme engellinin bağımsız yaşaması için eğitilmiş rehber köpeği kullanması caizdir; Mâlikî'de canlı köpek temizdir."),
    (410, "Alzheimer Hastasının Malı Üzerinde Velisinin İlaç ve Bakımevi Harcaması", "الإنفاق من مال مريض الخرف على رعايته وعلاجه", "Dört Mezhep İttifakı (Vesayet)", "Mahkemece vasi atanan yakını hastanın kendi malından onun en iyi tıbbi bakımı alması için harcama yapmakla yetkilidir."),
    (411, "Ağır Yara Tedavisinde Kullanılan Oksijen Çadırı (Hiperbarik Oksijen) Seansları", "العلاج بالأكسجين تحت الضغط العالي للصائم", "Dört Mezhep İttifakı", "Basınçlı saf oksijen solumak beslenme sayılmaz; oruca ve abdeste engel değildir."),
    (412, "Varis Tedavisinde Bacak Damarlarına Köpük ve Lazer Uygulanması", "علاج الدوالي بالحقن الرغوي والليزر وأثره على الطهارة", "Dört Mezhep İttifakı", "Damar içi tıbbi müdahaleler caizdir; bacak sarılırsa sargı üzerine mesh edilir."),
    (413, "Oruçlu Hastanın Göz Dibine Işık Tutularak Damla ile Göz Bebeğinin Büyütülmesi", "توسيع بؤبؤ العين بالقطرات للفحص الطبي في رمضان", "Cumhur Fukahâsı", "Teşhis amaçlı göz damlası orucu bozmaz."),
    (414, "Cerrahi Dikişlerde Kendiliğinden Eriyen Hayvansal/Sentetik İplerin Kullanımı", "استعمال الخيوط الجراحية القابلة للامتصاص من أصل حيواني", "Dört Mezhep İttifakı (Zaruret)", "Yaranın kapanması için bedenin emdiği tıbbi dikiş ipleri temiz kabul edilir."),
    (415, "Yüz Felcinde Göz Kapağının Kapanması İçin Altın Ağırlık Takılması", "زراعة شريحة ذهب في جفن العين لعلاج الشلل الوجهي", "Dört Mezhep İttifakı (Tedavi)", "Gözün kuruyup kör olmasını engellemek için göz kapağına mikro altın plaka konulması ittifakla caizdir."),
    (416, "Ağır Depresyon Tedavisinde Elektrokonvülsif Terapi (EKT / Beyne Şok)", "العلاج بالصدمات الكهربائية للاكتئاب الحاد وفقد الذاكرة المؤقت", "Cumhur Fukahâsı", "Uzman hekim kontrolünde yapılan EKT mubah tedavidir; şok sonrası geçici unutkanlık döneminde namazlar mazeretle telafi edilir."),
    (417, "Kusurlu Doğan Bebeğin Tedavisinde Anne-Baba Rızasının Sınırları", "حق الوالدين في رفض العلاج الجراحي لإنقاذ حياة الرضيع", "İslam Kamu Hukuku (Çocuğun Yaşam Hakkı)", "Anne ve babanın kurtarılabilecek bebeğin ameliyatını keyfi reddetme hakkı yoktur; hekim ve hâkim bebeğin hayatını korur."),
    (418, "Oruçlu İken Dudak Dolgusu ve Yüz Mezoterapisi Yaptırmak", "حقن الميزوثيرابي والفيلر في الوجه نهار رمضان", "Cumhur Fukahâsı", "Deri altına yapılan iğneler besin ve vitamin içermediği sürece orucu bozmaz; ancak kanama ve şişlik sebebiyle iftar sonrasına bırakılması evladır."),
    (419, "Ağır Yanık Hastalarında Deri Nakli İçin Kadavradan Deri Alınması", "أخذ رقع جلدية من جثث الموتى لإنقاذ مصابي الحروق", "Dört Mezhep İttifakı (Zaruret)", "Hastanın hayatını tehdit eden yanıklarda kadavradan geçici deri grefti örtülmesi caizdir."),
    (420, "Kemik Erimesi Olan Yaşlıların Oturarak ve İma ile Namaz Kılması", "صلاة العاجز والمريض بالقعود والإيماء للركوع والسجود", "Dört Mezhep İttifakı (Meşakkat)", "Rükû ve secdeye eğilmek kemik kırığı riski doğuruyorsa sandalyede ima ile namaz kılınabilir; kaza gerekmez."),
    (421, "Cenin Anomalilerinde Amniyosentez (Karından Sıvı Alma) Testi Yaptırmak", "فحص السائل السلوي حول الجنين لتشخيص التشوهات", "Dört Mezhep İttifakı", "Bebeğin sağlığını ve tedavi imkânını araştırmak için yapılan amniyosentez mubahtır."),
    (422, "Oruçlunun Diş Taşı Temizliği (Detertraj) Yaptırması ve Kanın Durumu", "تنظيف الجير وتكلسات الأسنان للصائم والنزف اليسير", "Cumhur Fukahâsı", "Su ve kan tükürülüp yutulmadıkça diş taşı temizliği orucu bozmaz; yutulursa kaza gerekir."),
    (423, "Kanser Ağrılarında Omuriliğe Takılan Morfin Pompalarıyla İbadet", "الصلاة مع وجود مضخات المسكنات المزروعة في النخاع", "Dört Mezhep İttifakı", "Cihazın deri altında olması gusle engel değildir; akıl ve şuur yerinde olduğu sürece namaz kılınır."),
    (424, "Doğum Sonrası Depresyonda (Lohusa Sendromu) Kadının Eşine Karşı Hırçınlığı", "الأثر النفسي لاكتئاب ما بعد الولادة على الواجبات الزوجية", "İslam Aile Hukuku (Af ve Merhamet)", "Hormonal ve psikolojik rahatsızlık döneminde kadının hırçınlığı 'nüşûz' (itaatsizlik) sayılmaz; kocanın sabrı ve tedavisi farzdır."),
    (425, "Kelliği Önlemek İçin Donör Olmaksızın Sentetik Liflerle Yapay Saç Ekimi", "زراعة الألياف الصناعية البديلة للشعر الطبيعي", "Çağdaş Heyetler (Kusuru Giderme)", "Vücuda kalıcı enfeksiyon vermediği tıbben teyit edilen sentetik saç liflerinin ekimi caizdir."),
    (426, "Ağır Astım Krizinde Oksijen Tüpü Maskesi ile Namaz Kılmak", "الصلاة مع وضع قناع الأكسجين على الأنف والفم", "Dört Mezhep İttifakı (Zaruret)", "Maske secdeye engel olsa dahi hasta burnunu ve alnını imkân ölçüsünde koyar veya ima eder; namaz geçerlidir."),
    (427, "Oruçlu Kimsenin Diş Ağrısı İçin Karanfil Yağı ve Alkol İçermeyen Ağız Gargarası", "المضمضة بالغسول الطبي وزيت القرنفل دون بلعه للصائم", "Hanefî ve Şâfiî Mezhepleri", "Boğaza kaçırılmadan ağızda çalkalanıp tükürülen gargara ve karanfil yağı oruca zarar vermez."),
    (428, "Böbrek Taşı Kırdırma (ESWL / Şok Dalga) Tedavisi ve Kanlı İdrar", "تفتيت حصى الكلى بالموجات الصدمية وخروج الدم مع البول", "Dört Mezhep İttifakı", "Tedavi mubahtır; idrarla çıkan kan idrarı bozan hades hükmündedir, abdest yenilenir."),
    (429, "Yüzdeki Doğum Lekesi ve Benlerin (Nevüs) Lazerle Silinmesi", "إزالة الوحمات الجلدية والشامات بالليزر", "Cumhur Fukahâsı", "Yüzdeki anormal leke ve benleri aldırmak tedavi ve kusur izalesidir, helaldir."),
    (430, "Ağır Psikiyatrik Bipolar Hastanın Mani Döneminde Yaptığı Boşamalar", "طلاق مريض الذهان وثنائي القطب في نوبة الهوس", "Hanbelî ve Hanefî Tahrîci (Talakın Düşmemesi)", "Muhakeme yeteneğini yitirdiği mani/cinnet nöbetinde ağzından çıkan talak hükümsüzdür, nikâh devam eder."),

    # SOSYAL DOKU, KUL HAKLARI, GURBET VE GÜNLÜK MUÂMELÂT (431 - 470)
    (431, "Sosyal Medyadaki Anonim Hesaplardan İftira ve Linç Kampanyaları Yapmak", "الطعن في الأعراض بالحسابات الوهمية والتشهير الإلكتروني", "Ruhsat Yoktur (Büyük Günah ve Kazf)", "Gizli hesap arkasına sığınarak hakaret ve linç yapmak kul hakkı, iftira ve kebâirdendir."),
    (432, "Toplu Konutlarda (Sitede) Evcil Hayvan Gezdirirken Ortak Alanların Kirletilmesi", "تلويث المداخل والمصاعد المشتركة بفضلات الكلاب", "Dört Mezhep İttifakı (Zararın İzalasi)", "Ortak alanı kirletmek ve temizlememek komşuluk hakkını çiğnemektir; yönetim yaptırım uygulayabilir."),
    (433, "Mesai Saatinde Şahsi Sosyal Medya Hesabında İçerik Üretmek ve Para Kazanmak", "إدارة الحسابات الشخصية والتربح منها في أوقات الوظيفة", "Ruhsat Yoktur (Haksız Maaş)", "İşverenin zamanını çalarak şahsi sosyal medyaya içerik üretmek haram kazançtır."),
    (434, "Apartmanda Üst Kattan Alt Kata Su Sızması ve Tesisat Tamir Masrafı", "مسؤولية تسرب المياه وإصلاح الأنابيب بين الجيران", "Dört Mezhep İttifakı (Zarar Veren Öder)", "Sızıntının kaynağı olan üst kat sahibi tesisatı derhal yaptırmak ve alt katın badana zararını tazminle mükelleftir."),
    (435, "Korsan Dizi, Film ve Maç Yayını İzlemenin Dini Hükmü", "مشاهدة البث المقرصن للمباريات والأفلام المشفرة", "Cumhur Fukahâsı (Kul Hakkı/Haksız Menfaat)", "Şifreli yayınları kırarak bedelsiz izlemek yayıncı kuruluşun emeğini ve hakkını gasptır, günahtır."),
    (436, "Yolculukta Namaz Kılacak Mescit Bulamayanın Park veya Kaldırımda Namazı", "الصلاة في الحدائق العامة والأرصفة عند تعذر المسجد", "Cumhur Fukahâsı", "Temiz bir örtü veya seccade serilerek yayaların geçişini engellemeyecek bir köşede namaz kılmak caizdir."),
    (437, "İşçinin İşverenden İzinsiz İkinci Bir İşte (Moonlighting) Çalışması", "العمل الإضافي في وظيفة أخرى دون إذن صاحب العمل الأصلي", "Hanefî ve Hanbelî İcâre Usûlü", "Asıl işteki performansı düşürmediği ve şirketle çıkar çatışması yaratmadığı sürece mesai dışı çalışmak mubahtır."),
    (438, "Market Kasasında Unutulan Para Üstünün Kasiyer Tarafından Alınması", "استيلاء المحاسب على الفكة المتروكة من الزبائن", "Ruhsat Yoktur (Hıyanet/Emanet)", "Unutulan para üstü müşterinin mülküdür; marketin kayıp fonuna veya hayra aktarılmalıdır, kasiyer şahsına alamaz."),
    (439, "Apartman Girişine ve Yangın Merdivenine Ayakkabılık ve Eşya Koymak", "إشغال الممرات المشتركة وسلالم الطوارئ بالأمتعة", "Dört Mezhep İttifakı (Taddi/Haksız İşgal)", "Ortak kaçış ve geçiş alanlarını izinsiz işgal etmek komşulara zarar verir ve kul hakkıdır, kaldırılmalıdır."),
    (440, "Gurbette Yaşayan Müslümanın Yerel Mezarlığa Hristiyan Sembolü Olmadan Gömülmesi", "الدفن في مقابر الغربيين في أطراف معزولة بدون صلبان", "Zaruret Tahrîci", "İslam mezarlığı bulunamadığı ve cenazenin memlekete nakli imkânsız olduğu takdirde, haçlardan uzak izole bir bölüme İslami usûlle gömülmek caizdir."),
    (441, "Lokantada Bahşiş (Tip) Kutusunda Biriken Paraların Personel Arasında Taksimi", "قسمة صندوق البقشيش المشترك بين النوادل وعمال المطبخ", "Hanefî ve Mâlikî (Örf Şartı)", "Müşterilerin tüm personele bıraktığı bahşişler işletmedeki teamüle göre mutfak ve servis arasında adil paylaştırılır."),
    (442, "Sosyal Medyadaki Yemek ve Lüks Hayat Paylaşımlarının Kul Hakkı Boyutu", "التباهي بالأطعمة الفاخرة ونشرها في المنصات وأثره", "İslam Ahlak ve Fıkhı (Mekruh/Göz Hakkı)", "Aç ve muhtaç insanların bulunduğu ortamda lüks sofraları teşhir etmek kalpleri kırmak ve göz hakkı sebebiyle mekruhtur."),
    (443, "Taksi Şoförünün Yolu Kasten Uzatarak Fazla Ücret Yazdırması", "إطالة مسار الرحلة عمدا لزيادة أجرة العداد", "Ruhsat Yoktur (Haram ve Hırsızlık)", "Müşterinin bilgisizliğinden faydalanıp yolu uzatmak aldatma ve haksız lokmadır, farkın iadesi farzdır."),
    (444, "İş Yerinde İbadet Ederken Mesaiyi Kötüye Kullanıp İşi Aksatmak", "المبالغة في صلاة النوافل وتضييع واجبات الوظيفة", "Hanefî ve Şâfiî Usûlü", "Farz ve müekked sünnetler kılınır; ancak mesai saatinde uzun uzun nafileye dalarak şirketin acil işlerini bekletmek caiz değildir."),
    (445, "Komşunun İnternet / Wi-Fi Şifresini İzinsiz Kırarak Bağlanmak", "اختراق شبكات الواي فاي المجاورة واستعمال الإنترنت غصبا", "Ruhsat Yoktur (Gasb/Menfaat)", "İnternet kotası ve hızı mali bir haktır; izinsiz bağlanıp kullanmak menfaat gasbıdır, kul hakkıdır."),
    (446, "Marketlerde Meyve-Sebze Poşetine İyilerini Seçip Çürükleri Başkasına Bırakmak", "فرز السلع في المتاجر وترك التالف للآخرين دون إفساد", "Dört Mezhep İttifakı (Örf)", "Ezmeden ve zedelemeden seçerek almak mubahtır; ancak sağlam meyveleri tırnaklayıp bozmak haramdır."),
    (447, "Otobüste veya Metroda Yaşlı, Hamile ve Engellilere Yer Vermenin Hükmü", "إيثار الضعفاء والحوامل بالجلوس في وسائل النقل", "İslam Ahlakı ve Nebevi Sünnet", "Aciz, yaşlı ve hamile kimselere yer vermek müekked edep, merhamet ve toplumsal fazilettir."),
    (448, "Miras Kalan Gayrimenkulün İntikalini Kasten Geciktirip Diğerlerini Mağdur Etmek", "تعطيل حصر الإرث والإضرار بالورثة لحرمانهم من حقوقهم", "Ruhsat Yoktur (Zulüm/İzrar)", "Miras taksimini inatla kilitleyip muhtaç kardeşleri perişan etmek Kur'an'daki 'Zarar vermeksizin' emrine aykırıdır, büyük günahtır."),
    (449, "Cenazeden Sonra Yedinci, Kırkıncı ve Elli İkinci Gün Merasimleri Yapmak", "إقامة مآتم الأربعين والخميس والبدع المرتبطة بالأموات", "Cumhur Fukahâsı (Bid'at)", "Dinde 7, 40 veya 52. gün diye bir ibadet yoktur; bunlar sonradan uydurulan bid'atlerdir; dua ve hayır her zaman yapılır."),
    (450, "İşçinin Şirket Araçlarıyla Aşırı Hız Yapıp Trafik Cezası Yemesi", "تحمل العامل لغرامات المرور الناتجة عن إهماله الشخصي", "Dört Mezhep İttifakı (Kusurlu Öder)", "Şirket işini görürken dahi olsa kural ihlali şahsi kusurdan kaynaklanıyorsa ceza işçinin kendi cebinden ödenir."),
    (451, "Gurbette Yaşayan Müslümanın Helal Kesim Et Bulamadığında Ehl-i Kitap Eti Yemesi", "أكل لحوم أهل الكتاب في بلاد الغرب والتثبت من الذبح", "Dört Mezhep İttifakı (Şartlı Cevaz)", "Boğulmadan veya şokta ölmeden, besmeleyle veya ehl-i kitap usûlüyle boğazlandığı bilinen hayvanlar helaldir; mekanik boğmaca leştir."),
    (452, "Apartmanda Çöp Torbalarını Saatinden Önce Kapı Önüne Koyup Koku Yapmak", "وضع القمامة في الممرات وإيذاء الجيران بالرائحة", "Dört Mezhep İttifakı (Eziyet Yasağı)", "Apartman kurallarına aykırı saatte çöp çıkarıp kokutmak komşuya eziyettir, haramdır."),
    (453, "Öğrenci Yurdunda 또는 Odada Başkaları Uyurken Işığı Açıp Ses Yapmak", "إزعاج الزملاء في السكن المشترك وإيقاظهم لغير حاجة", "İslam Ahlakı (Kul Hakkı)", "Ortak odada kalanların dinlenme hakkına saygı duymak farzdır; gürültü yapmak kul hakkıdır."),
    (454, "Lokantada Yan Masada Kuran Okunurken veya Ezan Okunurken Alkol Servisi", "المطاعم التي تقدم المأكولات الحلال مع الخمور", "Hanefî ve Şâfiî (Mekruh/Kaçınma)", "Alkol satılan masada oturmak haramdır; ancak helal yemek yapılan temiz lokantanın helal menüsü yenir, alkollü ortamdan uzak durulur."),
    (455, "Sosyal Medyadaki Dini Tartışmalarda Karşı Tarafı Tekfir Etmek", "التسرع في تكفير المسلمين في المناظرات الرقمية", "Dört Hak Mezhep (Büyük Günah)", "Ehl-i kıble olan ve küfrü açık nassla sabit olmayan müslümanı tekfir etmek hadisin tehdidiyle tekfir edenin aleyhine döner."),
    (456, "Taksiye Müşteri Olarak Binen Kadının Yalnız Başına Şehir İçi Yolculuğu", "ركوب المرأة بمفردها مع سائق الأجرة داخل المدينة", "Hanefî ve Cumhur (Hılvet-i Sahîha Sayılmaması)", "Pencereleri açık, caddede seyreden ticari takside şehir içi yolculuk kapalı halvet sayılmaz, meşrudur; tenha ıssız yollarda kaçınılır."),
    (457, "İşçinin İşverenin Bilgisi Dışında Bahşiş Almasının Yasak Olduğu Kurumlar", "تحريم أخذ الإكراميات المشروطة بنظام المؤسسة الداخلي", "Hanefî ve Hanbelî (Şart Bağlayıcılığı)", "Kurum sözleşmesinde bahşiş almak yasaklanmışsa bu şarta uymak gerekir; gizlice almak ahde vefasızlıktır."),
    (458, "Cenazede Ağıt Yakmak, Saçını Başını Yolmak ve Feryat Etmek (Niyâha)", "النياحة ولطم الخدود وشق الجيوب على الميت", "Dört Mezhep İttifakı (Haram)", "Gözyaşı dökmek ve hüzünlenmek rahmettir; feryat koparmak, elbiseyi yırtmak ve isyan sözleri nassla lanetlenmiştir."),
    (459, "Komşunun Arabasının Çıkışını Engelleyecek Şekilde Park Etmek", "إغلاق مداخل سيارات الآخرين والتضييق عليهم في الطريق", "Dört Mezhep İttifakı (Zulüm/İzrar)", "İletişim numarası bırakmaksızın başkasının aracını kilitlemek ve vaktini çalmak kul hakkıdır."),
    (460, "Müslümanın Gayrimüslim Bir Hayır Kurumuna (Kızılhaç vb.) Bağışta Bulunması", "التبرع للجمعيات الإنسانية غير الإسلامية لإغاثة المنكوبين", "Cumhur Fukahâsı (İyilik ve Takva)", "Açlık ve doğal afet krizlerinde din ayrımı gözetmeksizin küresel yardım kuruluşlarına nafile bağış yapmak meşrudur."),
    (461, "İş Güvenliği Bareti ve Yeleğini Takmayarak Hayatını Tehlikeye Atmak", "إهمال وسائل السلامة المهنية ومخالفة لوائح الأمان", "Dört Mezhep İttifakı (Kendi Canını Korumak)", "İşverenin sunduğu koruyucu donanımı takmamak kendi canını tehlikeye atmaktır, günahtır."),
    (462, "Eski Kocasından Nafaka Almaya Devam Etmek İçin Resmi Evlilik Yapmamak", "الزواج العرفي للاحتفاظ براتب الزوج المتوفى أو نفقته", "Ruhsat Yoktur (Hile ve Haram Kazanç)", "Hakkı olmadığı halde yetim veya dul maaşını almak için dini nikâhla yaşayıp resmiyeti gizlemek devleti aldatmaktır, para haramdır."),
    (463, "Apartmanda Çift Asansörden Birini Eşya Taşıyarak Bozmak ve Korumamak", "استعمال مصاعد الركاب في نقل الأثاث الثقيل وإتلافها", "Dört Mezhep İttifakı (Tazmin)", "Kurala aykırı yük taşıyarak asansöre zarar veren kimse tamir masrafını şahsen ödemekle yükümlüdür."),
    (464, "Mirasçılardan Mal Kaçırmak İçin Bütün Mülkü Tek Bir Evladın Üzerine Satış Göstermek", "البيع الصوري لأحد الورثة لحرمان الباقين من التركة", "Dört Mezhep İttifakı (Bâtıl Hile)", "Miras payını düşürmek kastıyla yapılan muvazaalı (danışıklı) satışlar bâtıldır; vefattan sonra terekeye iade edilir."),
    (465, "İş Yerinde Kalan Yemeklerin Dökülmeyip Sokak Hayvanlarına Verilmesi", "إطعام بقايا الأطعمة الصالحة لحيوانات الشوارع", "Dört Mezhep İttifakı (Sadaka)", "İsrafı önleyip hayvanları doyurmak sevaptır; ancak çevreye koku ve pislik yaymayacak şekilde yapılmalıdır."),
    (466, "Gurbette Yaşayan Müslümanın Çocuğuna İslami İsim Koyma Mecburiyeti", "تسمية الأولاد بأسماء غير إسلامية للاندماج في المجتمعات الغربية", "Cumhur Fukahâsı", "Anlamı güzel ve İslam inancına zıt olmayan her isim caizdir; küfür sembolü veya çirkin isimler haramdır."),
    (467, "Trafik Polisinin Yazdığı Haksız Cezaya Karşı İtiraz Etmek ve Hukuki Hak", "التظلم القضائي من المخالفات المرورية الجائرة", "Dört Mezhep İttifakı", "Kişinin haksız kesildiğini düşündüğü cezayı iptal ettirmek için mahkemeye delil sunması meşru hakkıdır."),
    (468, "Öğretmenin Öğrenciler Arasında Başarı veya Sevgi Ayrımcılığı Yapması", "التمييز الجائر بين الطلاب في الدرجات والمعاملة", "İslam Eğitim Hukuku (Adalet)", "Öğretmen adaletle mükelleftir; şahsi sempati sebebiyle hak etmeyene yüksek not vermek kul hakkıdır."),
    (469, "Komşunun Ağacının Meyvelerinin Kendi Bahçesine Taşması ve Dalın Durumu", "أغصان أشجار الجار المتدلية في الفناء الخاص", "Hanefî ve Şâfiî Mezhepleri", "Komşudan dalı budaması istenir; budamazsa kendi mülkünü gölgeleyen kısmı mülk sahibi budayabilir; meyve ise komşunundur."),
    (470, "Ev Sahibinin Kiracının Evi Başkasına Alt Kiraya (Sublease) Vermesini Yasaklaması", "اشتراط منع المستأجر من التأجير من الباطن", "Hanbelî Mezhebi (Şart Serbestisi)", "Ev sahibinin 'evi başkasına devredemezsin' şartı bağlayıcıdır; kiracı bu şarta uymak zorundadır."),

    # KÜLLİYATIN SON İNCE FÜRÛAT DÜĞÜMLERİ (471 - 500)
    (471, "Namazda İftitah Tekbiri Alırken Elleri Kulak Memesine Değdirmek Şart mıdır?", "لمس شحمة الأذنين في تكبيرة الإحرام بين الاستحباب والبدعة", "Cumhur Fukahâsı (Şâfiî ve Mâlikî - Omuz Hizası)", "Elleri kulak memesine fiilen değdirmek şart değildir; Hanefî'de başparmakların kulak hizasına, cumhurda ise omuz hizasına kaldırılması sünnettir."),
    (472, "Namazda Rükûdan Doğrulurken 'Semiallahu Limen Hamideh' Sözünün İmama ve Cemaate Hükmü", "الجمع بين التسميع والتحميد للإمام والمأموم والمنفرد", "Hanefî Mezhebi (Cemaatin Sadece Tahmid Demesi)", "İmama uyan cemaat sadece 'Rabbenâ leke'l-hamd' der; 'Semiallah' sözünü imam söyler (Şâfiî'de ise her ikisi de söylenir)."),
    (473, "Secdede Ayak Parmaklarının Kıbleye Dönük Olması Farz mıdır?", "استقبال القبلة بأطراف أصابع القدمين في السجود", "Cumhur Fukahâsı (Sünnet Olması)", "Secdede ayakların kıbleye dönük tutulması sünnettir; ayağın bir parmağının yere değmesi Hanefî'de kâfidir, dönmemesi namazı bozmaz."),
    (474, "Oruçlu İken Dudak Kanamasının Yutulması Halinde Orucun Durumu", "بلع دم الشفة اليسير مع الريق للصائم", "Hanefî Mezhebi (Tükürükten Az Olma Kuralı)", "Dudaktan sızan kan tükürükten az veya eşitse orucu bozmaz; tükürükten çok olup tadı boğaza inerse kaza gerekir."),
    (475, "Abdest Alırken Konuşmanın ve Gereksiz Söz Söylemenin Hükmü", "الكلام أثناء الوضوء بغير حاجة هل يبطل الطهارة", "Dört Mezhep İttifakı (Mekruh/Hilaf-ı Evlâ)", "Abdest esnasında dünya kelamı konuşmak abdesti bozmaz; ancak edebe aykırı ve hilâf-ı evlâdır."),
    (476, "Cemaatle Namazda Ön Safta Boşluk Görünce Namaz İçinde Bir İki Adım İlerlemek", "المشي اليسير لملء الفرجة في الصف أثناء الصلاة", "Dört Mezhep İttifakı (Amel-i Kalîl)", "Saftaki boşluğu kapatmak için göğsü kıbleden çevirmeksizin 1-2 adım yürümek namazı bozmaz, safları sıklaştırmak sünnettir."),
    (477, "Secde Edilen Yerin Sert Olması Şart mıdır? (Aşırı Yumuşak Sünger Üzerinde Namaz)", "السجود على الإسفنج والفرش اللينة جدا واستقرار الجبهة", "Hanefî ve Şâfiî (Alnın Bastırılması)", "Secdede alnın yerin sertliğini hissetmesi gerekir; aşırı süngerimsi ve başın gömüldüğü yumuşak zeminde secde tam sayılmaz."),
    (478, "Oruçlu Kimsenin Kan Vermesi (Kan Bağışı) Orucu Bozar mı?", "التبرع بالدم في نهار رمضان وأثره على صحة الصوم", "Cumhur Fukahâsı (Hanefî, Mâlikî, Şâfiî)", "Kan aldırmak veya kan bağışlamak vücuttan madde çıktığı için orucu bozmaz; halsizlik sebebiyle mekruhtur."),
    (479, "Kadının Çorapsız Olarak Namaz Kılmasının Sıhhati (Ayak Avret midir?)", "عورة قدم المرأة في الصلاة وجواز كشف القدمين", "Hanefî Mezhebi (İmam Ebû Hanîfe - Ayakların Avret Olmaması)", "Hanefî mezhebine göre kadının ayakları namazda avret değildir; çorapsız kılınan namaz sahihtir (Cumhurda ise örtmek farzdır)."),
    (480, "Namazda Gözleri Yummanın (Kapatmanın) Dini Hükmü", "تغميض العينين في الصلاة للخشوع ودفع الشواغل", "Hanefî ve Hanbelî (Huşû İçin Cevaz)", "Gözü kapatmak mekruh olmakla birlikte, etraftaki dikkat dağıtıcı şeylerden kurtulup huşûyu artırmak amacıyla gözleri yummak caizdir."),
    (481, "Teyemmüm Ederken Yüzük ve Saatin Altına Toprak Tozunun Ulaşması", "نزع الخاتم والساعة عند التيمم ومسح اليدين", "Hanefî ve Şâfiî (Çıkarma Şartı)", "Teyemmümde el mesh edilirken yüzüğün çıkarılması veya oynatılması farzdır; altına mesh değmezse teyemmüm tamam olmaz."),
    (482, "İmamın Namazı Çok Fazla Uzatması Halinde Cemaatin Niyetini Ayırıp Çıkması", "مفارقة المأموم للإمام وإتمام الصلاة منفردا لتطويل الإمام", "Şâfiî ve Hanbelî Mezhepleri (İnfirâd Ruhsatı)", "İmam cemaati bıktıracak derecede namazı uzatırsa veya bir özür belirdiğinde cemaat niyetini infirâda çevirip selam verip çıkabilir."),
    (483, "Oruçlu Kimsenin Banyoda Başına Su Dökerek Serinlemesi", "الاغتسال وصب الماء على الرأس للتبرد في الصوم", "Dört Mezhep İttifakı (Sünnet/Mubah)", "Ağız ve burundan içeri su kaçırmamak kaydıyla yıkanmak ve soğuk suyla serinlemek caizdir; Resulullah sıcaktan başına su dökmüştür."),
    (484, "Kaza Namazlarında Ezân ve Kâmet Getirmenin Hükmü", "الأذان والإقامة لقضاء الصلوات الفائتة", "Hanefî Mezhebi (Kâmetin Sünnet Olması)", "Birden fazla kaza namazı kılınırken tek bir ezan okunup her farz için ayrı kâmet getirilmesi sünnettir."),
    (485, "Camiye Girildiğinde Cemaat Farza Başlamışsa Tahiyyetü'l-Mescid Kılınır mı?", "صلاة تحية المسجد بعد إقامة الفريضة", "Dört Mezhep İttifakı (Terk Edilmesi)", "Farza kâmet getirildiğinde hiçbir nafile kılınmaz; doğrudan imama uyulur, tahiyyetü'l-mescid farzla eda edilmiş sayılır."),
    (486, "Abdest Alırken Ayakları Sol El ile Yıkamanın Sünnet Olması", "غسل الرجلين باليد اليسرى وتخليل الأصابع بالخنصر", "Dört Mezhep İttifakı (Edep)", "Ayakları yıkarken sol eli kullanmak ve parmak aralarını hilallemek nebevi bir edeptir."),
    (487, "Namaz Kılarken Önünden İnsan Geçmesini Engelleyen Sütre Koymanın Hükmü", "اتخاذ السترة في الصلاة وحكم المرور بين يدي المصلي", "Cumhur Fukahâsı (Sünnet/Müstehap)", "Sütre koymak sünnettir; sütre olmasa dahi namaz bozulmaz, ancak geçen günahkâr olur."),
    (488, "Oruçlu İken Dudakları Yalamak ve Tükürükle Islatmak", "لحس الشفاه الجافة وابتلاع رطوبتها للصائم", "Dört Mezhep İttifakı (Bozmaması)", "Dudaktaki tabii ıslaklığı yutmak orucu bozmaz; dışarıdan su sürülüp yutulmadıkça zarar vermez."),
    (489, "Seferde İken Cuma Namazı Kılan Seferînin Öğle Namazı Kılması Gerekir mi?", "صلاة المسافر للجمعة وإجزاؤها عن فرض الظهر", "Dört Mezhep İttifakı (Kâfi Olması)", "Seferîye cuma farz değildir; ancak cuma namazını cemaatle kılarsa öğle namazının yerine geçer, tekrar öğle kılmaz."),
    (490, "Secdede Alın ile Birlikte Burnun da Yere Değmesi Farz mıdır?", "السجود على الأنف مع الجبهة وحكم الاقتصار على الجبهة", "Hanefî Mezhebi (İmam Ebû Hanîfe - Alnın Yeterliliği)", "Ebû Hanîfe'ye göre sadece alınla secde geçerlidir; ancak İmam Ebû Yûsuf ve cumhura göre özürsüz burnu yere koymamak namazı tahrîmen bozar."),
    (491, "Cünüp Olan Kimsenin Yemek Yemeden Önce Elini ve Ağzını Yıkaması", "وضوء الجنب قبل النوم والأكل والشرب", "Cumhur Fukahâsı (Sünnet Olması)", "Guslü geciktiren cünübün yemek yemeden veya uyumadan önce abdest alması veya en azından elini-ağzını yıkaması sünnettir."),
    (492, "Namazda İkinci Rekâta Kalkarken Yere Dayanarak Doğrulmak (İstirâhat Secdesi)", "جلسة الاستراحة والاعتماد على اليدين للقيام", "Şâfiî Mezhebi (Sünnet Olması)", "İkinci secde sonrası hafif oturup yere dayanarak kalkmak Şâfiî'de sünnettir; Hanefî'de doğrudan kalkılır, iki tatbikat da sahihtir."),
    (493, "Oruçlunun Yüzünü Soğuk Islak Havlu ile Silmesi ve Kompres Yapması", "وضع الكمادات الباردة والمنشفة الرطبة على الجسد للصائم", "Dört Mezhep İttifakı (Mubah)", "Harareti gidermek için ıslak havlu koymak ibadete zarar vermez."),
    (494, "Namazda Esneme Geldiğinde Ağzı Elin Tersiyle Kapatmanın Edebi", "كظم التثاؤب في الصلاة ووضع اليد على الفم", "Dört Mezhep İttifakı (Sünnet)", "Namazda esnemeyi gücü yettiğince tutmak, tutamazsa elin sırtıyla ağzı kapatmak nebevi sünnettir."),
    (495, "Abdest Sırasında Baş Mesh Edilirken Kulakların da Aynı Suyla Mesh Edilmesi", "مسح الأذنين بماء الرأس أو بماء جديد", "Hanefî Mezhebi (Aynı Suyla Mesh)", "Hanefî'de başı mesh eden ıslaklıkla kulaklar da mesh edilir; Şâfiî'de yeni su almak sünnettir, iki yol da meşrudur."),
    (496, "İkindi ve Sabah Namazlarından Sonra Nafile Namaz Kılmanın Hükmü", "الصلاة بعد العصر والصبح وحكم ذوات الأسباب", "Şâfiî Mezhebi (Sebepli Namaz Ruhsatı)", "Hanefî'de bu vakitlerde hiçbir nafile kılınmaz; Şâfiî'de ise kaza namazı, tavaf namazı ve tahiyyetü'l-mescid gibi sebepli namazlar kılınabilir."),
    (497, "Oruçlu İken Dişlerin Arasında Kalan Nohut Tanesinden Küçük Kırıntının Yutulması", "بلع ما بين الأسنان وهو دون الحمصة للصائم", "Hanefî Mezhebi (Bozmaması)", "Diş arasına sıkışmış nohuttan küçük yemek kırıntısını gayriihtiyari yutmak Hanefî'de orucu bozmaz; nohuttan büyükse kaza gerekir."),
    (498, "Rükûda ve Secdede Tesbihleri 3'ten Fazla (5 veya 7 Kez) Söylemek", "الزيادة في تسبيح الركوع والسجود وترا للمنفرد", "Dört Mezhep İttifakı (Müstehap)", "Yalnız kılan kimsenin rükû ve secdede tesbihleri 5, 7, 9 gibi tekli sayılarda artırması müstehaptır; imam ise cemaati usandırmaz."),
    (499, "Abdestten Sonra Kalan Su Damlalarını Temiz Bir Havlu ile Kurulamak", "تنشيف أعضاء الوضوء بالمنديل والمنشفة", "Dört Mezhep İttifakı (Mubah/Cevaz)", "Abdestten sonra havlu ile kurulanmak mubahtır; aşırı soğukta kurulanmak evladır."),
    (500, "CÂMİU'R-RUHAS BÜYÜK HİLÂFİYÂT HATİMESİ: 500 Düğümün Şer'î Mührü", "خاتمة كتاب الرخص وتكامل الأقوال الفقهية مع النصوص الشرعية", "Dört Hak Mezhep Cumhurunun İttifakı", "Bu külliyatta yer alan 500 mesele, mükellefin dinini bâtıl etmeden en ehven yolla amel etmesi için fukahânın sahih ictihadlarından tahrîc edilmiştir; ruhsat heva için değil zaruret ve meşakkat için alınır.")
]

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
    print("[*] FAZ 12: 500 MESELE HEDEFİNE ULAŞMA MOTORU (MESELE 351 - 500)")
    print("=" * 80)

    compiler = NeuroSymbolicFikhEngine()
    completed = load_checkpoints()
    chapter_file = os.path.join(CHAPTERS_DIR, "24_modern_ve_sosyal.md")

    tasks = [item for item in MESELER_FAZ_12 if f"batch_{item[0]:03d}" not in completed]
    print(f"[+] Mevcut Doğrulanmış Mesele: {len(completed)} | Kalan: {len(tasks)}")

    if not tasks:
        print("[!] 500 meselenin tamamı zaten derlenmiş!")
        return

    # Tek iş parçacığında kesintisiz ve hatasız işleme
    for idx, (m_id, m_baslik, m_sorgu, m_ruhsat_mezhep, m_ruhsat_hukum) in enumerate(tasks, 1):
        key = f"batch_{m_id:03d}"
        canon = {
            "ruhsat_mezhep": m_ruhsat_mezhep,
            "ruhsat_hukum": m_ruhsat_hukum,
            "hanefi_hukum": "Hanefî mezhebi usûlünce maslahat ve sedd-i zerâi' dairesinde hükme bağlanmıştır.",
            "safii_hukum": "Şâfiî mezhebinde akdin ve ibadetin asıl rükünlerine sadakat esastır.",
            "maliki_hukum": "Mâlikî mezhebi maslahat-ı mürsele ve âmme menfaatiyle cevaz alanını tayin eder.",
            "hanbeli_hukum": "Hanbelî mezhebinde akit ve şart serbestisi asıldır, haram nassı olmadıkça mubahtır."
        }
        print(f"[{idx:03d}/{len(tasks):03d}] Mesele {m_id:03d} Tahrîc Ediliyor: {m_baslik}...")
        start_t = time.time()
        try:
            page_md = compiler.compile_issue_page("Kitâbü'l-Muâmelât ve'l-İctimâ' (Modern Fıkıh)", m_id, m_baslik, m_sorgu, canon)
            elapsed = time.time() - start_t
            if page_md:
                with open(chapter_file, "a", encoding="utf-8") as bf:
                    bf.write(page_md + "\n\n")
                completed.add(key)
                save_checkpoint(completed)
                print(f"       [✓] Tamamlandı ({elapsed:.1f} sn).")
        except Exception as e:
            print(f"       [-] Hata (Atlandı): {e}")

    # 500 Meselelik Master Kitap Birleştiriliyor
    print("\n[*] 500 Meselelik Master Kitap Ciltleniyor...")
    mukaddime = """# CÂMİU'R-RUHAS VE TAHKÎKU'L-MEZÂHİB
## Dört Mezhep Esaslı En Hafif ve Sahih Fıkıh Külliyatı (500 Amelî Düğüm ve Ruhsatlar)

---

### MUKADDİME VE TELİF METODOLOJİSİ
Bu eser; İslam Hukuku'nun dört hak mezhebi (Hanefî, Mâlikî, Şâfiî, Hanbelî) dairesinde kalmak şartıyla, mükellefi meşakkatten kurtaran **en hafif, uygulanabilir ve sahih ruhsatları** (500 temel ve çağdaş amelî düğüm) bir araya getirmek amacıyla telif edilmiştir.

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
    print(f"[✓] 500 MESELELİK HİLÂFİYÂT BÖLÜMÜ TAMAMLANDI! Boyut: {size_kb:.2f} KB")
    print("=" * 80)

if __name__ == "__main__":
    main()
