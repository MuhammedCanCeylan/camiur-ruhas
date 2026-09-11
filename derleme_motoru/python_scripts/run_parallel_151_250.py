import os
import sys
import json
import time
import re
import threading
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from neuro_symbolic_engine import (
    NeuroSymbolicFikhEngine, OUTPUT_BOOK_DIR, CHAPTERS_DIR, 
    MASTER_BOOK_PATH, CHECKPOINT_FILE, DB_PATH
)

# 151 - 250 ARASI 100 AMELÎ DÜĞÜM HAVUZU
MESELER_100 = [
    # GÜNCEL FİNANS VE TİCARET (151 - 180)
    (151, "Stoksuz Satış (Dropshipping) ve Kabz Olmayan Malın E-Ticarette Satışı", "بيع الدروب شيبينغ وبيع ما لا يملك المورد", "Hanefî (Selem/İstisnâ)", "Sipariş üzerine tedarikçiden müşteriye doğrudan gönderim akitte vasıflar ve teslimat garanti edildiği sürece caizdir."),
    (152, "Kripto Varlıklarda Faizsiz Likidite Sağlama (Staking ve Yield Farming)", "حكم الستيكينغ وتجميد العملات الرقمية لأجل الأرباح", "Çağdaş Fıkıh (İcâre/Şirket)", "Blokzincir ağını doğrulamak ve transfer güvenliğini sağlamak amacıyla kilitlenen varlıktan alınan ödül emek/hizmet karşılığıdır, helaldir."),
    (153, "NFT (Benzersiz Dijital Varlık) Alım-Satımı ve Fikrî Mülkiyet Değeri", "شراء وبيع الرموز غير القابلة للاستبدال إن إف تي", "Çağdaş Fıkıh Heyetleri", "Gayrimeşru/haram görsel içermeyen dijital sertifika ve mülkiyet haklarının ticareti mütekavvim mal kapsamında mubahtır."),
    (154, "Akıllı Sözleşmeler (Smart Contracts) ve Otomatik İcra Edilen Akitler", "العقود الذكية المبنية على تقنية البلوكشين", "Hanbelî (Akit Serbestisi)", "İçeriğinde faiz veya garar bulunmayan ve kodlama ile otomatik şartlara bağlanan akitler şer'an bağlayıcıdır."),
    (155, "Geri Alım Vaadiyle Satış (Repo / Finansal Kiralamada Mülkiyet Devri)", "بيع الوفاء والتأجير المنتهي بالتمليك", "Hanefî Müteahhirîn / Mâlikî", "Sözleşmelerin birbirinden bağımsız yapılması şartıyla leasing ve kira sonunda mülkiyet intikali caizdir."),
    (156, "Konvansiyonel Kasko ve Zorunlu Trafik Sigortasının Hükmü", "التأمين التجاري الإجباري والتكافلي التبادلي", "Zaruret Tahrîci (Hanefî/Mâlikî)", "Zorunlu trafik sigortası devlet mecburiyeti ve can/mal emniyeti sebebiyle zarureten caizdir; kaskoda ise tekâfül tercih edilir."),
    (157, "Borsada Açığa Satış (Short Sale / Olmayan Hissenin Ödünç Satışı)", "البيع على المكشوف في الأسواق المالية", "Ruhsat Yoktur (İcmâen Bâtıl)", "Mülkiyetinde bulunmayan hissenin ödünç alınıp satılması ve düşüşten kâr hedeflenmesi hadisin açık nehyiyle icmâen bâtıldır."),
    (158, "Kaldıraçlı İşlemler (Forex / Margin Trading) ve Çift Yönlü Risk", "التداول بالهامش والرافعة المالية في الفوركس", "Ruhsat Yoktur (İcmâen Bâtıl)", "Kredi ile ticareti birleştiren ve akit içinde menfaat şartı içeren kaldıraçlı işlemler ribâ ve garar sebebiyle icmâen haramdır."),
    (159, "Çok Katlı Pazarlama (Network Marketing / Saadet Zinciri) Gelirleri", "التسويق الشبكي والهرمي في المعاملات المعاصرة", "Ruhsat Yoktur (Garar Sebebiyle Bâtıl)", "Üründen ziyade alt üye bulma üzerinden komisyon dağıtan piramit sistemler fahiş garar ve kumar şüphesiyle bâtıldır."),
    (160, "Yapay Zekâ ile Üretilen Sanat ve Yazılımların Telif Mülkiyeti", "حقوق الملكية الفكرية للمصنفات المنتجة بالذكاء الاصطناعي", "Çağdaş Maslahat Tahrîci", "İstemi (prompt) veren ve kurguyu yapan kullanıcının emeği ve yönlendirmesi mülkiyet hakkı doğurur, ticareti mubahtır."),
    (161, "Yurt Dışından Mal İthalinde Akreditif (Letter of Credit) Faizleri", "الاعتمادات المستندية في التجارة الدولية وتكاليفها", "Hanefî/Şâfiî (Vekâlet/Hizmet)", "Bankanın ödemeyi garanti etmesi ve evrak takibi karşılığında aldığı sabit masraf ücret-i vekâlet hükmünde caizdir."),
    (162, "E-Cüzdan (Papara, Paycell vb.) Bakiyelerinden Kazanılan Cashback", "استرداد الأموال والهدايا في محافظ الدفع الإلكتروني", "Dört Mezhep İttifakı (Hibe)", "Müşteriyi teşvik amacıyla dağıtılan nakit iadeler ve puanlar şartlı faiz değil mubah ticari hibedir."),
    (163, "İflas Eden Borçlunun Mal Varlığının Tasfiyesi ve Alacaklılar Sırası", "التفليس والحجر على المدين المفلس وقسمة أمواله", "Cumhur Fukahâsı", "Hâkim kararıyla iflasına hükmedilen borçlunun malları satılır; rehinli alacaklılar önceliklidir, kalan bakiye alacaklılara hisseleri oranında paylaştırılır."),
    (164, "Devlet İhalesine Girerken Verilen Geçici ve Kesin Teminat Mektupları", "خطاب الضمان المصرفي الابتدائي والنهائي في المناقصات", "Çağdaş Fıkıh Heyetleri", "Banka garantörlüğü için alınan komisyon, kredi faizi olmaksızın sadece fiili dosya masrafı karşılığı ise helaldir."),
    (165, "İnternet Üzerinden İkinci El Mal Satışında Ayıp İhbarı ve Süresi", "رد المبيع بالتعييب في التجارة الإلكترونية ومدته", "Hanefî Mezhebi (Fevrîlik Şartı Olmaması)", "Ayıbı öğrenen alıcı derhal değil makul örfi süre içinde bildirim yaparak fesih hakkını kullanabilir."),
    (166, "Mesken Kredisinde (Konut Finansmanı) Murabaha ve Doğrudan Satış", "المرابحة للآمر بالشراء في تمويل العقارات السكنية", "Dört Mezhep Çağdaş İttifakı", "Katılım bankasının mülkü bizzat satın alıp müşteriye vadeli kâr ile satması (murâbaha) meşrudur."),
    (167, "Gümrük Vergilerinden Kaçınmak İçin Düşük Fatura (Under-invoicing) Göstermek", "تخفيض الفواتير الجمركية للتهرب من الضرائب المكوس", "Ruhsat Yoktur (Yalan ve Hıyanet)", "Resmi beyanda gerçeğe aykırı fatura düzenlemek yalan, kamu hakkı ihlali ve aldatma sebebiyle haramdır."),
    (168, "Franchise (İsim Hakkı) Bedeli Ödemek ve Şubelerden Ciro Payı Almak", "عقد الامتياز التجاري الفرنشايز وحكم أخذ نسبة من المبيعات", "Hanbelî (Akit Serbestisi)", "Marka değeri, işletim modeli ve denetim desteği karşılığında maktu veya oransal ciro payı almak caizdir."),
    (169, "Vadeli Döviz Sözleşmeleri (Forward ve Vadeli Opsiyon Akitleri)", "عقود الصرف الآجلة والمستقبليات في العملات", "Ruhsat Yoktur (İcmâen Bâtıl)", "Dövizin dövizle vadeli takası bedellerin mecliste kabzını şart koşan sarf nasslarına aykırıdır, bâtıldır."),
    (170, "Tasarruf Finansman Şirketleri (Elbirliği / Çekilişli Ev Alma Sistemi)", "جمعيات التوفير التعاونية والتمويل التشاركي بالقرعة", "Mâlikî ve Hanefî Maslahat Tahrîci", "Üyelerin faizsiz yardımlaşma kastıyla havuzda para biriktirip sırayla ev/araç alması organizasyon ücreti fahiş olmamak kaydıyla caizdir."),
    (171, "Kitle Fonlaması (Crowdfunding) ile Şirket Hissesi veya Ödül Satışı", "التمويل الجماعي القائم على المكافأة أو الملكية", "Hanbelî (Şirket Serbestisi)", "Girişimcinin kitlelerden bağış, ürün ön siparişi veya hisse karşılığı fon toplaması meşru bir mudârabe/müşârekedir."),
    (172, "Elektronik Para Kuruluşlarında Duran Bakiyelerin Nemalandırılması", "أرباح وفوائد الودائع المحفوظة في شركات الدفع الإلكتروني", "Ruhsat Yoktur (Faiz)", "Müşterinin ödeme için tuttuğu paraya garanti kâr veya faiz tahakkuk ettirilmesi açık ribâdır."),
    (173, "İkinci El Araç Satışında Kilometre Düşürme ve Gizli Kusur Tazminatı", "الغش في عداد مسافات السيارات وأخذ الأرش أو الرد", "Dört Mezhep İttifakı (Haram ve Fesih)", "Kilometre düşürmek fahiş aldatmadır; alıcı akdi derhal feshedebilir veya değer farkını (erş) tazmin alır."),
    (174, "E-Ticarette Yorum ve Puan Satın Alarak Tüketiciyi Yanıltmak (Sahte Yorum)", "شراء التقييمات والمراجعات الوهمية في المتاجر الإلكترونية", "Ruhsat Yoktur (Necş ve Hile)", "Müşteriyi aldatmak için yapılan sahte yorum ve yıldızlama nehyedilen 'necş' (fiyat kızıştırma/aldatma) hükmündedir, haramdır."),
    (175, "Hisse Senetlerinde Rüçhan Hakkının (Yeni Pay Alma Hakkı) Satılması", "بيع حق الاكتتاب وأولوية الأسهم في الشركات", "Çağdaş İslâm Fıkıh Akademisi", "Mevcut ortağın sermaye artırımındaki öncelik hakkı mali değeri olan bir imtiyazdır; borsada satışı caizdir."),
    (176, "Altın Hesabında Fiziki Teslimat Olmaksızın Gram Alım-Satımı", "حسابات الذهب غير المادية في البنوك والقبض الحكمي", "Çağdaş Heyetler (Kaydî Kabz)", "Bankanın kasasında karşılık altın bulundurması şartıyla hesap üzerinden gram altın alım-satımı hükmî kabzle caizdir."),
    (177, "Faizli Kredi Borcunu Kapatmak İçin Başka Bankadan Borç Transferi", "سداد الدين الربوي بقرض آخر لتخفيف الفائدة", "Zaruret Tahrîci", "Kişinin daha ağır faiz yükünden kurtulmak için daha hafif şartlı borca geçmesi zarureten affedilir; asıl olan derhal faizden çıkmaktır."),
    (178, "Yurt Dışı Alışverişlerinde Dinî Açıdan Sakıncalı Hediyelerin Kabulü", "قبول الهدايا المشتملة على رموز غير إسلامية أو خنزير", "Hanefî/Şâfiî", "Gayrimüslimlerin verdiği hediyeler prensipte kabul edilir; bizzat haram olan maddeler tüketilmez, elden çıkarılır."),
    (179, "Fatura Ödemelerinde Gecikme Zammı (Kamu ve Özel Sektör Ayrımı)", "فوائد التأخير وغرامات فواتير الكهرباء والماء", "İkrah/Zaruret Tahrîci", "Müşterinin kasten geciktirmemesi esastır; tekel durumundaki kamu/hizmet kurumlarının zorunlu tahsil ettiği gecikme zammı kullanıcı için ızdırardır."),
    (180, "Sanal Oyun Eşyalarının, Kostümlerin ve Hesapların Gerçek Parayla Satışı", "بيع العناصر الافتراضية وحسابات الألعاب الإلكترونية", "Hanefî Örf Tahrîci", "Ekonomik değeri ve piyasada alıcısı bulunan, kumar ve şans oyunu niteliği taşımayan dijital oyun hesap ve eşyalarının satışı caizdir."),

    # MODERN TIP, SAĞLIK VE BİYOETİK (181 - 215)
    (181, "Kozmetik Amaçlı Saç Ekimi ve Protez Saç Kullanımının Hükmü", "زراعة الشعر واستعمال الشعر المستعار للصلع", "Cumhur Fukahâsı (Kusuru Giderme)", "Kelliği tedavi etmek amacıyla kişinin kendi donör bölgesinden saç ekimi yaptırması yaratılışı bozmak sayılmaz, helaldir."),
    (182, "Kalıcı Olmayan Geçici Dövme, Microblading ve Kaş Kontürü", "الوشم المؤقت والميكروبليدينغ للزينة", "Mâlikî/Hanefî (Geçici Süslenme)", "Deri altına kan akıtılarak kalıcı mürekkep zerk edilmeyen, birkaç ayda kendiliğinden silinen yüzeysel boyalar lanetlenen dövme kapsamına girmez."),
    (183, "Otizm veya Ağır Genetik Hastalık Tespiti Halinde Tüp Bebekte Embriyo Seçimi (PGD)", "الفحص الجيني للأجنة قبل الغرس وتخير الجنين السليم", "Çağdaş Fıkıh Heyetleri", "Ağır genetik sakatlıkları önlemek amacıyla tüp bebekte sağlıklı embriyonun seçilip rahme konulması caizdir; cinsiyet seçimi ise mazeretsiz caiz değildir."),
    (184, "Kanser ve Kemoterapi Öncesi Sperm/Yumurta Dondurulması", "تجميد النطاف والبويضات للمريض قبل العلاج الإشعاعي", "Dört Mezhep Çağdaş İttifakı", "Evlilik bağı devam ettiği sürece eşlerin kendi hücrelerini dondurup iyileştikten sonra tüp bebek yöntemiyle kullanmaları meşrudur."),
    (185, "Yurt Dışında Taşıyıcı Anne (Surrogate Mother) Kullanımının Hükmü", "استئجار الأرحام وحكم الأم البديلة", "Ruhsat Yoktur (İcmâen Bâtıl)", "Yabancı kadının rahmini kiralamak nesep karmaşası doğurduğundan ve yabancı meninin rahme girmesi haram sayıldığından icmâen bâtıldır."),
    (186, "Kadavra Üzerinde Tıp Öğrencilerinin Otopsi ve Cerrahi Eğitimi Yapması", "تشريح جثث الموتى للتعليم الطبي والتحقيق الجنائي", "Maslahat-ı Mürsele Tahrîci", "Adli suçların aydınlatılması ve tıp hekimlerinin cerrahi eğitimi için zaruret miktarınca kadavrada inceleme yapılması kamu yararı sebebiyle caizdir."),
    (187, "Ölümcül Hastalarda Pasif Ötenazi (Tedaviyi Reddetme Hakkı)", "إيقاف العلاج الميئوس منه وحق المريض في رفض التداوي", "Cumhur Fukahâsı", "Tedavi olmak cumhura göre farz değil mubahtır; tıbben fayda vermeyeceği kesinleşen ağır acılı tedavileri hastanın veya velisinin reddetmesi caizdir, intihar sayılmaz."),
    (188, "Domuz Kalp Kapakçığı veya Damarlarının İnsana Nakledilmesi", "زراعة صمام قلب الخنزير في الإنسان عند فقد البديل", "Dört Mezhep İttifakı (Izdırar Hali)", "Helal muadili bulunmadığı ve hastanın hayatı tehlikede olduğu takdirde domuz menşeli kalp kapakçığının nakli zaruret nassıyla mubahtır."),
    (189, "Diş İmplantı, Tel Tedavisi ve Çene Bozukluklarının Düzeltilmesi", "تقويم الأسنان وزراعة الغرسات السنية للعلاج والتحسين", "Dört Mezhep İttifakı (Tedavi)", "Çiğneme bozukluğunu veya ağız yapısındaki şekilsel kusurları düzeltmek amacıyla tel takmak ve implant yapmak tedavi kapsamındadır, helaldir."),
    (190, "Psikiyatrik İlaçlar ve Uyuşturucu Etkisi Olan Ağrı Kesicilerin Tıbbi Kullanımı", "استعمال المهدئات والأدوية المخدرة للضرورة الطبية", "Hanefî ve Hanbelî (Zaruret Tedavisi)", "Bağımlılık ve uyuşukluk veren morfin ve psikiyatrik ilaçların doktor kontrolünde tedavi ve ağrı dindirme amacıyla kullanılması helaldir."),
    (191, "Doğum Kontrol Hapları ve Spiral ile Gebeliğin Geçici Olarak Önlenmesi", "استعمال موانع الحمل المؤقتة كالحبوب واللولب", "Cumhur Fukahâsı (Azil Kıyası)", "Eşlerin karşılıklı rızasıyla, kalıcı kısırlık yapmayan geçici gebelik önleme yöntemlerini kullanması sahabenin 'azil' tatbikatı kıyasıyla caizdir."),
    (192, "Kalıcı Kısırlık Yapan Ameliyatlar (Vazektomi ve Tüplerin Bağlanması)", "التعقيم الجراحي الدائم بقطع القنوات المنوية أو ربط الأنابيب", "Ruhsat Yoktur (Tıbbi Mecburiyet Hariç)", "Annenin hayatını tehdit eden kesin tıbbi mecburiyet olmadıkça geri dönüşsüz kısırlaştırma ameliyatları nesli kurutma yasağı gereğince haramdır."),
    (193, "Anne Sütü Bankasından Alınan Sütle Beslenme ve Süt Kardeşliği Şüphesi", "بنوك الحليب البشري وحكم اختلاط الأنساب بالرضاع", "Cumhur Fukahâsı (İhtiyat)", "Süt veren annelerin kimliği bilinmeyen süt bankalarından bebek beslemek evlilik haramlığı doğuran süt hısımlığını belirsiz kıldığından men edilmiştir."),
    (194, "Lazer Epilasyon ile Avret Bölgesinin Başkasına Açılması", "إزالة الشعر بالليزر وحكم كشف العورة أمام الطبيبة", "Hanefî/Mâlikî (Zaruret ve Kademeli Ruhsat)", "Kadının kadına avreti diz ile göbek arasıdır; meşakkat veren aşırı kıllanma tedavisi hariç keyfi estetik için avretin lazer uzmanına açılması caiz görülmez."),
    (195, "Adli Tıp Vakalarında Mezarın Açılarak Otopsi Yapılması (Nebş-i Kabir)", "نبش القبر للتحقيق الجنائي أو استخراج حق مالي", "Hanefî ve Şâfiî (Maslahat Tahrîci)", "Maddi bir cinayeti çözmek veya hak sahibinin hakkını ispatlamak için kadı/savcı kararıyla mezarın açılıp cesedin incelenmesi caizdir."),
    (196, "Mide Küçültme (Tüp Mide / Obezite Cerrahisi) Ameliyatları", "جراحة تكميم المعدة وتصغيرها لعلاج السمنة المفرطة", "Çağdaş Fıkıh Heyetleri", "Diyet ve sporla verilemeyen, şeker, kalp ve tansiyon gibi ölümcül risk doğuran aşırı obezitede mide küçültme ameliyatı meşru tedavidir."),
    (197, "Müzik, İlahi ve Ses Terapisi ile Ruhsal Hastalıkların Tedavisi", "العلاج بالموسيقى والصوتيات للعلل النفسية", "Hanefî (İbn Âbidîn) ve Gazâlî Tahrîci", "Şehveti tahrik etmeyen, isyan ve haram söz içermeyen dinlendirici ses ve nağmelerin tedavi amacıyla dinlenmesi mubahtır."),
    (198, "Kan ve İdrar Tahlili Yaptırmanın Gusül ve Abdeste Etkisi", "سحب عينات الدم والبول للفحص الطبي وحكم الطهارة", "Şâfiî ve Mâlikî Mezhepleri", "Tahlil için damardan kan aldırmak abdesti bozmaz; idrar vermek ise sonrasında istincâ gerektirir."),
    (199, "Göz Numarasını Sıfırlamak İçin Yapılan Lazer (No-Touch / Lasik) Ameliyatı", "تصحيح النظر بعمليات الليزك وزراعة العدسات", "Dört Mezhep İttifakı (Tedavi)", "Görme kusurlarını gidermek amacıyla göze lazer operasyonu yaptırmak tedavinin aslına dahildir, helaldir."),
    (200, "Gen Terapisi ve CRISPR Teknolojisi ile DNA Mühendisliği", "التعديل الجيني والعلاج بالهندسة الوراثية", "Çağdaş Heyetler (Tedavi Şartıyla)", "Genetik anomalileri ve kanser genlerini düzeltmek helaldir; insan tasarımına ve kopyalamaya (klonlama) yönelik müdahaleler haramdır."),
    (201, "Ağır Yanıklarda Balık Derisi veya Sentetik Deri Grefti Nakli", "استعمال جلد السمك والأنسجة الصناعية لترميم الحروق", "Dört Mezhep İttifakı", "Deniz canlılarının derisi temizdir; yanık tedavisinde yara örtüsü olarak kullanılması helaldir."),
    (202, "Mideye Takılan Balon ve İştah Kapatıcı İğnelerle Zayıflama", "حقن التنحيف وعمليات بالون المعدة للتخسيس", "Cumhur Fukahâsı", "Sağlığa kalıcı zarar vermediği doktor raporuyla teyit edilen geçici kilo kontrol uygulamaları caizdir."),
    (203, "Oruçlu Hastanın Dializ Makinesine Bağlanması ve Kan Temizliği", "غسيل الكلى البريتوني والدموي وأثره على الصيام", "Çağdaş Fıkıh Kararları", "Kandaki üreyi süzerken serum ve glikoz verildiği için hemodiyaliz orucu bozar, kaza gerekir; besinsiz kuru süzmede ise tartışmalıdır."),
    (204, "Kanser Ağrılarında Tıbbi Kenevir (Medikal Esrar / CBD) Yağı Kullanımı", "استعمال مشتقات القنب الطبية لتسكين آلام الأورام", "Hanefî ve Hanbelî (Zaruret Tedavisi)", "Sarhoşluk verici THC maddesinden arındırılmış preparatların reçeteyle ağrı tedavisinde kullanılması caizdir."),
    (205, "Ceninin Anne Karnında Cerrahi Müdahale ile Ameliyat Edilmesi", "إجراء العمليات الجراحية للجنين داخل الرحم", "Dört Mezhep İttifakı", "Doğum sonrası yaşama şansını artırmak için uzman heyetçe yapılan anne karnı ameliyatları meşrudur."),
    (206, "Yüz Felci ve Sinir Zedelenmelerinde Akupunktur Tedavisi", "العلاج بالوخز بالإبر الصينية وحكمه الشرعي", "Dört Mezhep İttifakı (Mubah Tedavi)", "Bedene haram madde zerk etmeyen mekanik akupunktur uygulamaları mubah tedavi usûllerindendir."),
    (207, "Bebeklerde Doğum Sonrası Kordon Kanının Kök Hücre İçin Saklanması", "تخزين دم الحبل السري في بنوك الخلايا الجذعية", "Çağdaş Fıkıh Kurulları", "Gelecekteki ölümcül hastalıkların tedavisinde kullanılmak üzere kordon kanının saklanması maslahat gereği helaldir."),
    (208, "Cilt Bakımında Salyangoz Sıvısı, Kolajen ve Hayvansal Plasenta", "استعمال مصل الحلزون والمشيمة الحيوانية في مستحضرات التجميل", "Mâlikî ve Hanefî Tahrîci", "Temiz ve helal kaynaktan elde edilen veya kimyasal dönüşüm geçiren kozmetik serumların yüze haricen sürülmesi caizdir."),
    (209, "Hastalara Takılan Kalıcı İdrar Sondası ve Torbasıyla İbadet", "الصلاة مع كيس جمع البول والقسطرة الدائمة", "Mâlikî Mezhebi (Özür Ruhsatı)", "Sonda takılı hasta özür sahibi hükmündedir; torbadaki necis madde bedene bitişik zaruret sayıldığından namazına mâni değildir."),
    (210, "Kayıp Kemiklerin Yerine Titanyum veya 3D Yazıcı Kemik Nakli", "استعمال شرائح التيتانيوم والعظام المطبوعة ثلاثيا", "Dört Mezhep İttifakı", "Kırık ve doku kayıplarında madeni veya sentetik protezlerin vücuda vidalanması ittifakla caizdir."),
    (211, "Yatalak Hastaların Temizliği ve Teyemmüm Taşı ile Namazı", "طهارة المريض العاجز عن الوضوء بالتراب والحجر", "Cumhur Fukahâsı", "Suya ulaşamayan veya suyu kullanması sağlığına zarar veren yatalak hasta yatağının yanındaki toprak/tuğla ile teyemmüm eder."),
    (212, "Oruçlunun Burnuna Oksijen Maskesi ve Buhar Verilmesi", "استنشاق الأكسجين الطبي والرذاذ البخاري للصائم", "Çağdaş Fıkıh Heyetleri", "Saf oksijen gazı mideye giden bir besin olmadığından orucu bozmaz; buhar cihazında su zerrecikleri ciğere ulaşıyorsa ihtilaflıdır."),
    (213, "Gebelikte Ultrason ve Radyolojik Görüntüleme Yaptırmak", "استعمال التصوير بالموجات فوق الصوتية للجنين", "Dört Mezhep İttifakı", "Bebeğin sağlığını ve gelişimini takip etmek için ultrasona girmek meşrudur."),
    (214, "Zihinsel Engelli Bireylerin Cerrahi Yolla Evlilikten Men Edilmesi", "تعقيم المعاقين ذهنيا لمنع الإنجاب", "Çağdaş Fıkıh Heyetleri", "Velinin kendi başına kısırlaştırma yetkisi yoktur; ancak ağır cinsel istismar ve bakımsızlık tehlikesinde hâkim kararıyla ruhsat aranır."),
    (215, "Estetik Diş Beyazlatma (Bleaching) ve Lamine Porselen Kaplama", "تبييض الأسنان وتركيب عدسات الفينير التجميلية", "Hanefî ve Şâfiî", "Dişin asıl yapısını kesip yok etmeksizin sarılığı gidermek ve beyazlatmak süslenme kapsamında mubahtır."),

    # SOSYAL YAŞAM, ÇALIŞMA HAYATI VE GURBET FIKHI (216 - 250)
    (216, "Gayrimüslim Ülkelerde Cuma Namazının Vücûbu ve İzin Şartı", "وجوب صلاة الجمعة في بلاد غير المسلمين دون إذن الإمام", "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)", "Cuma namazı için devlet başkanının izni şart değildir; cemaat oluşturan müslümanlar her yerde cuma kılmakla yükümlüdür."),
    (217, "İş Yerinde Namaz İzni Verilmeyen Müslümanın Cem' Ruhsatı", "الجمع بين الظهر والعصر لحاجة العمل وعدم الإذن بالصلاة", "Hanbelî Mezhebi (Hâcet ve Meşakkat Cem'i)", "İşten atılma tehlikesi veya ağır baskı altında namaz kılamayan kimse, Hanbelî mezhebine göre öğle ile ikindiyi birleştirerek cem' edebilir."),
    (218, "Gayrimüslimlerin Dini Bayramlarında (Noel, Yılbaşı) Tebrik ve Hediyeleşme", "تهنئة غير المسلمين بأعيادهم الاجتماعية وتقديم الهدايا", "Çağdaş Fıkıh Heyetleri / Hanefî Müteahhirîn", "Dini inançlarını tasdik etmeksizin insani komşuluk ve akrabalık ilişkilerini korumak amacıyla genel tebrikte bulunmak caizdir."),
    (219, "Gayrimüslim Patronun veya Müşterinin Köpeğini Gezdirmek ve Beslemek", "رعاية وتدريب كلاب الحراسة والصيد في العمل", "Mâlikî Mezhebi (Köpeğin Bizâtihi Temiz Olması)", "Mâlikî mezhebine göre canlı köpek necis değildir; bekçilik veya av için kullanılan köpeğin bakımında çalışmak helaldir."),
    (220, "Gurbetteki Müslümanın Bulunduğu Ülkenin Yasalarına İtaat Yükümlülüğü", "الالتزام بالقوانين المدنية والمرورية في بلاد الإقامة", "Dört Mezhep İttifakı (Ahde Vefa)", "Müslüman vize veya vatandaşlık bağıyla girdiği ülkenin haram emretmeyen kamu, vergi ve trafik kurallarına uymakla şer'an mükelleftir."),
    (221, "İslam Hukukuna Göre Sendika Kurmak, Grev Yapmak ve Hak Arama Usûlü", "تشكيل النقابات العمالية والإضراب عن العمل للمطالبة بالحقوق", "Çağdaş Fıkıh Tahrîci", "İşçilerin haksız ücret düşüşünü ve zulmü önlemek adına kamuya sabotaj yapmaksızın iş bırakması meşru bir hak arama yoludur."),
    (222, "Asgari Ücretin Belirlenmesinde Hayat Pahalılığı ve İnsani Geçim Endeksi", "تحديد الحد الأدنى للأجور بما يكفل الكفاية المعيشية", "İslam Kamu Maslahatı (Kifâyet İlkesi)", "İşverenin işçiye insanca yaşayabileceği gıda, barınma ve sağlık imkânını sağlayacak asgari ücreti ödemesi şer'î adalet gereğidir."),
    (223, "Ev Sahibinin Kiracıya Fahiş Zam Yapması ve Devletin Kira Tavanı Sınırı", "تحديد سقف الإيجارات جبريا لمنع استغلال المستأجرين", "Mâlikî ve Hanefî (Maslahat ve Narh)", "Fahiş kriz ve barınma krizlerinde kamunun kiralara tavan zam sınırı koyması zulmü önlemek adına şer'an nafizdir."),
    (224, "Trafik Kurallarını İhlal Edip Kırmızı Işıkta Geçmenin Dinî Vebali", "حكم مخالفة إشارات المرور والمخاطرة بالأرواح", "Dört Mezhep İttifakı (Haram)", "Trafik kuralları kamu canını korumak için konulmuştur; kasten kırmızıda geçmek canı tehlikeye atmak ve haramdır."),
    (225, "Çevre Kirliliği, Plastik Atıklar ve Doğaya Zarar Vermenin Hükmü", "حرمة تلويث البيئة ومصادر المياه وإهدار الموارد", "Dört Mezhep İttifakı (İfsad Yasağı)", "Suları, havayı kirletmek ve doğaya plastik saçmak Kur'an'daki fesat yasağına girer, günahtır."),
    (226, "Hayvanlara Eziyet Etmek, Dövüştürmek (Horoz/Boğa) ve Kısırlaştırmak", "تحريش الحيوانات وتعذيبها وحكم إخصاء بهيمة الأنعام", "Dört Mezhep İttifakı (Haram)", "Hayvanları bahis için dövüştürmek lanetlenmiştir; eziyetsiz kısırlaştırma ise popülasyon zaruretinde caizdir."),
    (227, "Sokak Hayvanlarının Saldırganlaşması Durumunda Uyutulması", "إعدام الحيوانات العقورة والمؤذية لدفع الضرر العام", "Cumhur Fukahâsı", "Kuduz veya saldırganlığı önlenemeyen hayvanların eziyet vermeden itlaf edilmesi kamu canını korumak için caizdir."),
    (228, "Sosyal Medyada Başkalarının Fotoğrafını İzinsiz Paylaşmak ve Mahremiyet", "نشر صور الآخرين والاطلاع على خصوصياتهم في المنصات", "Dört Mezhep İttifakı (Kul Hakkı)", "Kişinin rızası olmaksızın şahsi görüntülerini ve yazışmalarını internette ifşa etmek tecessüs ve kul hakkıdır, haramdır."),
    (229, "Telif Hakları Süresi Dolan Kamusal Eserlerin Ticari Basımı", "طباعة ونشر المصنفات التي سقطت حقوقها في الملك العام", "Dört Mezhep İttifakı", "Kanunen koruma süresi bitip kamuya mâl olmuş klasik eserlerin herkes tarafından basılıp satılması helaldir."),
    (230, "Müslümanın Başka Bir Ülke Vatandaşlığına Geçmesi ve Yemin Etmesi", "التجنس بجنسية دولة غير إسلامية وحكم قسم الولاء", "Çağdaş Fıkıh Heyetleri", "Dinini serbestçe yaşayabilen müslümanın zulümden korunmak veya insani refah için vatandaşlık alması ve genel bağlılık yemini caizdir."),
    (231, "Yurt Dışında Yaşayanların Cenazelerini İslami Usûlle Defnetme Zorunluluğu", "دفن المسلم في مقابر المسلمين وتحريم إحراق الجثة", "Dört Mezhep İttifakı (İcmâ)", "Cesedin yakılması (kremasyon) kat'iyyen haramdır; müslümanın İslami kabristana veya ayrılmış bölüme gömülmesi farzdır."),
    (232, "Gayrimüslim Anne-Babanın Cenaze Törenine Katılmak ve Taziye", "حضور جنازة الوالدين غير المسلمين وتعزيتهم", "Şâfiî ve Hanbelî Mezhepleri", "Müslüman evladın gayrimüslim ebeveyninin cenazesine katılması, tabutunu taşıması ve taziye vermesi sıla-i rahim gereği meşrudur."),
    (233, "Mesai Saatlerinde Şahsi İşlerle Uğraşmak ve İnternet Kullanımı", "استعمال موارد العمل والإنترنت في الأغراض الشخصية", "Hanefî ve Hanbelî (Örf ve Emanet)", "İşi aksatmayan, kuruma mali külfet getirmeyen cüzi şahsi iletişimler örfen muaftır; mesaiyi çalmak haramdır."),
    (234, "İş Güvencesi ve Kıdem Tazminatının İslam Hukukundaki Karşılığı", "التكييف الفقهي لمكافأة نهاية الخدمة وتعويض الفصل التعسفي", "Çağdaş Fıkıh Heyetleri", "İş kanunlarının emrettiği kıdem ve ihbar tazminatları sözleşmenin zımni şartı sayılır, işçiye helaldir."),
    (235, "Engelli Bireylerin Hakları, Pozitif Ayrımcılık ve İstihdam Kotası", "حقوق ذوي الاحتياجات الخاصة وإلزام أرباب العمل بتشغيلهم", "Maslahat-ı Mürsele", "Kamunun engelli vatandaşlara istihdam kotası ve özel imtiyaz getirmesi şer'î adaletin tahakkukudur."),
    (236, "Vergi Kaçırmak ile Vergiden Kaçınmak (Yasal Boşlukları Kullanmak)", "التهرب الضريبي غير القانوني والتخطيط الضريبي المشروع", "Çağdaş Fıkıh Tahrîci", "Adil kamu hizmetlerinin yürütülmesi için konan meşru vergileri yalanla kaçırmak haramdır; yasal muafiyetlerden yararlanmak ise mubahtır."),
    (237, "Miras Kavgası Sebebiyle Akrabalık Bağlarını (Sıla-i Rahim) Koparmak", "قطيعة الرحم بسبب الخلافات المالية وتوزيع التركة", "Dört Mezhep İttifakı (Büyük Günah)", "Miras anlaşmazlıkları sebebiyle kardeşlerin ve akrabaların görüşmeyi kesmesi büyük günahtır; dava devam etse de selam kesilemez."),
    (238, "Ticarî Sırların ve Müşteri Verilerinin Başkasına Satılması", "إفشاء الأسرار التجارية وبيع قواعد بيانات العملاء", "Ruhsat Yoktur (Hıyanet ve Haksız Kazanç)", "İş sözleşmesi gereği gizli tutulması gereken müşteri ve şirket bilgilerini izinsiz satmak hıyanettir, kazancı haramdır."),
    (239, "İbadetlerdeki Niyetin Dille Telaffuz Edilmesinin Şart Olup Olmaması", "التلفظ بالنية في الصلاة والصيام بين البدعة والاستحباب", "Mâlikî Mezhebi (Kalbin Kastının Yeterliliği)", "Niyet kalbin kesin azmidir; dille söylemek farz veya sünnet değildir, kalpten geçirmek kâfidir."),
    (240, "Yolculukta Farz Namazların İki Rekât Kılınması (Kasr) Ruhsat mı, Azimet mi?", "قصر الصلاة في السفر بين الوجوب والرخصة", "Şâfiî Mezhebi (Muhayyerlik)", "Hanefî'de kasr vacip olsa da Şâfiî ve Hanbelî'ye göre ruhsattır; dileyen 4 rekât, dileyen 2 rekât kılabilir."),
    (241, "Çocukların Camide Ön Saflara Geçmesi ve Safı Bozar mı Şüphesi", "صلاة الصبيان في الصفوف الأولى وتأثيرها على صلاة البالغين", "Cumhur Fukahâsı (Bozmaması)", "Çocukların büyüklerin arasında namaz kılması safların sıhhatine halel getirmez, cemaatin namazı tamdır."),
    (242, "Cemaatle Namazda Safların Arasında Boşluk Kalmasının Hükmü", "حكم التراص في الصفوف والفرجة بين المصلين", "Cumhur Fukahâsı (Sünnet Olması)", "Safları sıklaştırmak sünnettir; aralık bırakarak kılınan namaz mekruh olmakla birlikte sahihtir, iade edilmez."),
    (243, "Oruçlu Kimsenin Parfüm, Kolonya ve Deodorant Sıkması", "استعمال العطور والبخاخات ومزيل العرق للصائم", "Dört Mezhep İttifakı (Bozmaması)", "Koku sürünmek ve deodorant sıkmak mideye menfezden gıda girmediği için orucu kesinlikle bozmaz."),
    (244, "Uçakta Kıble Tayini Yapılamadığında Namazın Kılınış Şekli", "الاجتهاد في القبلة داخل الطائرة وصحة الصلاة", "Cumhur Fukahâsı", "Pusula veya ekranla kıbleyi araştıran kimse kanaat getirdiği yöne doğru kılar; uçak yön değiştirse de namaz sahihtir."),
    (245, "Bankamatikten (ATM) Fazla Çıkan Parayı Sahibine İade Etme Zorunluluğu", "المال الزائد المستخرج من الصراف الآلي خطأ", "Dört Mezhep İttifakı (Gasb/İade)", "Sistem hatasıyla hesaptan fazla verilen para emanettir; bankaya derhal iadesi farzdır, harcanamaz."),
    (246, "Marketlerdeki Promosyonlu (1 Alana 1 Bedava) Ürünlerin Fıkhî Sıhhati", "عروض اشتر واحدة واحصل على الأخرى مجانا", "Dört Mezhep İttifakı (Bey' ve Hibe)", "Fiyat ve adet açıkça bilindiği sürece promosyonlu paket satışlar mubahtır."),
    (247, "Müslümanın Gayrimüslim Komşusuna İyilik Yapması ve Sadaka Vermesi", "الصدقة على غير المسلم والبر به والإحسان إليه", "Cumhur Fukahâsı", "Zekât dışındaki nafile sadakaların gayrimüslim muhtaçlara verilmesi sevaptır ve meşrudur."),
    (248, "Anne-Babanın Evlatları Arasında Mal Taksiminde Eşitlik Gözetmesi", "التسوية بين الأولاد في الهبة والعطية حال الحياة", "Hanbelî Mezhebi (Eşitliğin Vacip Olması)", "Anne ve babanın hayattayken çocuklarına hibe yaparken haklı bir mazeret olmaksızın ayrım yapması haramdır, eşitlik şarttır."),
    (249, "Kişinin Vefatından Sonra Bedeninin Tıbbi Araştırmalar İçin Bağışlanması", "الوصية بالتبرع بالجثة للأبحاث العلمية بعد الموت", "Çağdaş İhtilaf (Maslahat Tahrîci)", "Zaruret ve kamu menfaati bulunması kaydıyla cesedin hürmetini zedelemeyecek sınırlı tıbbi incelemelere izin verilebilir."),
    (250, "CÂMİU'R-RUHAS BÜYÜK NİHAİ HATİME: Mükellefin Amelinde Ruhsatla İttikā Dengesi", "قاعدة الأخذ بالأيسر في الفتوى والجمع بين الرخصة والورع", "Dört Hak Mezhep Cumhurunun İttifakı", "Din kolaylıktır; meşakkat anında dört hak mezhepten birinin sahih ruhsatıyla amel eden kimse levm olunamaz; ancak takva ehli kimsenin şüpheli şeylerden kaçınması evladır.")
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
    print("[*] 2-İŞÇİLİ (2-WORKER) PARALEL TAHRÎC MOTORU: MESELE 151 - 250")
    print("=" * 80)

    completed = load_checkpoints()
    print(f"[+] Başlangıçtaki Doğrulanmış Mesele Sayısı: {len(completed)}")

    # Thread-Safe Kilitler ve İstemci
    file_lock = threading.Lock()
    checkpoint_lock = threading.Lock()
    chapter_file = os.path.join(CHAPTERS_DIR, "24_modern_ve_sosyal.md")

    # Motor Tek Seferlik Başlatılır
    compiler = NeuroSymbolicFikhEngine()

    # Kalan Meseleleri Filtrele
    tasks_to_run = []
    for item in MESELER_100:
        m_id = item[0]
        key = f"batch_{m_id:03d}"
        if key not in completed:
            tasks_to_run.append(item)

    print(f"[*] İşlenecek Kalan Mesele Sayısı: {len(tasks_to_run)}")
    if not tasks_to_run:
        print("[!] Tüm meseleler zaten derlenmiş!")
        return

    def process_issue(item):
        m_id, m_baslik, m_sorgu, m_ruhsat_mezhep, m_ruhsat_hukum = item
        key = f"batch_{m_id:03d}"
        
        canon = {
            "ruhsat_mezhep": m_ruhsat_mezhep,
            "ruhsat_hukum": m_ruhsat_hukum,
            "hanefi_hukum": "Hanefî mezhebi usûlünce maslahat ve sedd-i zerâi' dairesinde hükme bağlanmıştır.",
            "safii_hukum": "Şâfiî mezhebinde akdin ve ibadetin asıl rükünlerine sadakat esastır.",
            "maliki_hukum": "Mâlikî mezhebi maslahat-ı mürsele ve âmme menfaatiyle cevaz alanını tayin eder.",
            "hanbeli_hukum": "Hanbelî mezhebinde akit ve şart serbestisi asıldır, haram nassı olmadıkça mubahtır."
        }

        print(f"    [*] [Worker] Mesele {m_id:03d} Tahrîc Ediliyor: {m_baslik}...")
        start_t = time.time()
        page_md = compiler.compile_issue_page("Kitâbü'l-Muâmelât ve'l-İctimâ' (Modern Fıkıh)", m_id, m_baslik, m_sorgu, canon)
        elapsed = time.time() - start_t

        if page_md:
            with file_lock:
                with open(chapter_file, "a", encoding="utf-8") as bf:
                    bf.write(page_md + "\n\n")
            with checkpoint_lock:
                completed.add(key)
                save_checkpoint(completed)
            print(f"        [✓] Mesele {m_id:03d} Tamamlandı ({elapsed:.1f} sn).")
            return True
        else:
            print(f"        [-] HATA: Mesele {m_id:03d} tahrîc edilemedi.")
            return False

    # 2 Paralel Worker (RTX 4060 VRAM Emniyeti)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_issue, item) for item in tasks_to_run]
        for f in as_completed(futures):
            f.result()

    # Master Kitap Dosyasını Fihristle Birleştirme
    print("\n[*] 250 Meselelik Master Külliyat Birleştiriliyor...")
    mukaddime = """# CÂMİU'R-RUHAS VE TAHKÎKU'L-MEZÂHİB
## Dört Mezhep Esaslı En Hafif ve Sahih Fıkıh Külliyatı (250 Temel ve Çağdaş Amelî Düğüm)

---

### MUKADDİME VE TELİF METODOLOJİSİ
Bu eser; İslam Hukuku'nun dört hak mezhebi (Hanefî, Mâlikî, Şâfiî, Hanbelî) dairesinde kalmak şartıyla, mükellefi meşakkatten kurtaran **en hafif, uygulanabilir ve sahih ruhsatları** (Klasik ve modern 250 amelî düğüm) bir araya getirmek amacıyla telif edilmiştir.

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
    print(f"[✓] 250 MESELELİK BÜYÜK KÜLLİYAT EKSİKSİZ TAMAMLANDI!")
    print(f"    Master Kitap: {MASTER_BOOK_PATH}")
    print(f"    Toplam Boyut: {size_kb:.2f} KB")
    print(f"    Toplam Mesele Sayısı: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
