import os
import sys
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from neuro_symbolic_engine import (
    NeuroSymbolicFikhEngine, OUTPUT_BOOK_DIR, CHAPTERS_DIR, 
    MASTER_BOOK_PATH, CHECKPOINT_FILE
)

# 251 - 350 ARASI MİKRO ÇAĞDAŞ VE AMELÎ DÜĞÜMLER
MESELER_FAZ_11 = [
    # ÇAĞDAŞ FİNANS, DİJİTAL GELİRLER VE TİCARET (251 - 280)
    (251, "Kripto Paralarda Vadeli İşlemler (Futures / Perpetual Contracts)", "عقود المشتقات والمستقبليات في العملات المشفرة", "Ruhsat Yoktur (İcmâen Bâtıl)", "Teslimatsız ve sırf fiyat farkı üzerinden nakit mahsuplaşmaya dayanan kripto vadeli işlemleri kumar ve garar sebebiyle haramdır."),
    (252, "E-Ticarette Ön Sipariş (Pre-Order) ile Üretim Öncesi Satış", "بيع المنتجات بالطلب المسبق وتكييفه على عقد الاستصناع", "Hanefî Mezhebi (İstisnâ')", "Vasıfları, teslim tarihi ve iade şartları belirlenen malların ön siparişle peşin veya vadeli satışı istisnâ' ve selem kurallarınca caizdir."),
    (253, "Dijital Oyun İçi Sandık (Loot Box / Gacha) Açma Sistemleri", "صناديق الحظ العشوائية في الألعاب الإلكترونية وحكمها", "Ruhsat Yoktur (Kumar/Meysir)", "Gerçek parayla satın alınıp içinden rastgele değerde eşya çıkan mekanikler kumara (meysir) dahil olup haramdır; garantili doğrudan alımlar caizdir."),
    (254, "Influencer ve Yayıncıların Aldığı Bağışlar (Donation) ve Abonelik Gelirleri", "أموال التبرعات والاشتراكات في منصات البث الرقمي", "Dört Mezhep İttifakı (Hibe/İcâre)", "İçerik meşru ve helal olduğu sürece izleyicilerin gönüllü bağışları hibe, ayrıcalıklı abonelikler ise caiz bir hizmet akdidir."),
    (255, "Banka Promosyon Paralarının Muhtaç Akrabaya veya Hayra Verilmesi", "صرف الفوائد والجوائز الترويجية البنكية في وجوه البر", "Cumhur Fukahâsı (Tathîr Tahrîci)", "Faizli kurumdan gelen promosyon parası bizzat tüketilmez; sevap beklenmeksizin kamu yararına, borçlulara veya fakirlere arındırma amacıyla verilir."),
    (256, "Freelance Çalışanların Yabancı Para Cinsinden Anlaşıp Yerel Para ile Tahsilatı", "الاتفاق على الأجرة بعملة أجنبية وقبضها بسعر يوم السداد", "Hanefî ve Hanbelî Mezhepleri", "Hizmet bedelinin döviz olarak belirlenip tahsilat günündeki serbest piyasa rayici üzerinden yerel parayla ödenmesi ribâ sayılmaz, meşrudur."),
    (257, "POS Cihazından Nakit Para Çekimi Yaparak Komisyon Ödemek (POS Tefeciliği)", "سحب السيولة النقدية عبر بطاقات الائتمان ونقاط البيع بعمولة", "Ruhsat Yoktur (Kat'i Faiz)", "Karttan alışveriş yapılmış gibi gösterip komisyon kesilerek nakit para alınması hileli borç faizidir (ribâ), icmâen haramdır."),
    (258, "Yapay Zekâ ve Algoritmik Botlarla Otomatik Spot Hisse/Kripto Alım-Satımı", "التداول الآلي عبر روبوتات الذكاء الاصطناعي في الأسواق المالية", "Hanbelî (Vekâlet Serbestisi)", "İşlemler spot piyasada yapıldığı, açığa satış ve kaldıraç içermediği sürece algoritmik yazılımlara alım-satım yetkisi vermek caizdir."),
    (259, "Hisse Senedi Alınan Şirketin Gelirinde %5'ten Az Faiz veya Gayrimeşru Gelir Olması", "نسبة تطهير الأسهم المختلطة والتخلص من الإيرادات المحرمة", "Çağdaş Fıkıh Heyetleri (AAOIFI)", "Ana faaliyeti helal olan şirketin küçük faiz/meşru olmayan gelirleri temettü dağıtımında oransal olarak hesaplanıp hayra bağışlanarak hisse caiz hale gelir."),
    (260, "İnternet Sitelerine Reklam Alarak Tıklama Başına Gelir (AdSense) Elde Etmek", "التربح من إعلانات المواقع الإلكترونية والشبكات الإعلانية", "Hanefî ve Mâlikî Maslahat Tahrîci", "Site sahibinin filtreleme yaparak kumar, alkol ve müstehcen reklamları engellemesi şartıyla reklam alanı kiralamak ve gelir elde etmek helaldir."),
    (261, "İkinci El Alışverişte Güvenli Ödeme Havuzlarının (Escrow) Kullanımı", "خدمات الحساب الوسيط في التجارة الإلكترونية لحفظ الثمن", "Dört Mezhep İttifakı (Vekâlet/Rehin)", "Paranın mal teslim edilip alıcı onaylayana kadar tarafsız emanetçi/aracı şirkette bloke tutulması akdin ifasını garanti eden caiz bir vekâlettir."),
    (262, "E-Ticarette Kargo Ücretinin Alıcıya veya Satıcıya Yükletilmesi Şartı", "اشتراط نفقات الشحن والتوصيل على المشتري أو البائع", "Hanbelî Mezhebi (Şart Serbestisi)", "Kargo bedelinin açıkça belirtilerek taraflardan birine yüklenmesi akit şartı olarak sahihtir."),
    (263, "Yazılım Geliştiricilerin Lisanslı Kodlarını Açık Kaynak (Open-Source) Olarak Vakfetmesi", "وقف البرمجيات والملكية الفكرية للنفع العام", "Hanefî (İmam Züfer - Menfaat Vakfı)", "Maddi değeri olan bir yazılımın kamu istifadesine bedelsiz tahsis edilmesi meşru bir menfaat vakfı ve sadaka-i câriyedir."),
    (264, "Kira Sözleşmelerinde Dolar/Euro Cinsinden Kira Bedeli Belirlenmesi", "تحديد الأجرة بالعملات الأجنبية في الإجارات المحلية", "Dört Mezhep İttifakı (Cevaz)", "Enflasyondan korunmak amacıyla kiranın döviz cinsinden tayin edilmesi ve o günkü kurla veya döviz olarak ödenmesi akden geçerlidir."),
    (265, "Kripto Cüzdan Şifrelerinin (Private Key) ve Varlıkların Mirasçılara İntikali", "توريث الأصول الرقمية والمحافظ المشفرة للورثة", "Dört Mezhep İttifakı (Terekede Hak)", "Maddi kıymeti olan dijital varlıklar terekeye dâhildir; şifrelerin veya erişim haklarının mirasçılara intikali şer'î mirastır."),
    (266, "Mesai Saatinde Şirket Bilgisayarında Kripto veya Borsa Takibi Yapmak", "المتاجرة بالأسهم أثناء ساعات العمل الرسمي", "Ruhsat Yoktur (Emanet İhlali)", "İşverenin izni olmaksızın mesaiyi şahsi ticarete ayırmak alınan maaşın o kısmını şüpheli ve haksız kılar."),
    (267, "Geciken Borçlarda Alacaklının Uğradığı Ticari Kâr Mahrumiyeti Tazminatı", "التعويض المالي عن فوات الربح بسبب مماطلة المدين الموسر", "Çağdaş Fıkıh İhtilafı / Mâlikî Tahrîci", "Borcunu kasten geciktiren zengin borçludan, alacaklının reel ticaret zararını telafi için mahkeme kararıyla tazminat alınmasını caiz gören tahrîcler vardır."),
    (268, "Evden Çalışan (Remote) İşçinin Elektrik, İnternet ve Donanım Masrafları", "تحمل صاحب العمل لنفقات العمل عن بعد وأدواته", "Hanefî İcâre Usûlü", "İşin görülmesi için zorunlu olan altyapı ve araç gereç masraflarının işverene ait olması veya ücrete dâhil edilmesi akdin adaletindendir."),
    (269, "Dijital Oyun Hilesi (Cheat / Bot) Satışı ve Bu Yoldan Gelir Elde Etmek", "بيع برمجيات الغش في الألعاب الإلكترونية وحكم كسبها", "Ruhsat Yoktur (Hile ve İfsad)", "Sistemi manipüle eden, kullanıcıların emeğini gasbeden hile yazılımlarının ticareti ve kazancı bâtıldır, haramdır."),
    (270, "Taksitle Alınan Bir Malın Borcu Bitmeden Başkasına Satılması", "بيع السلعة المشتراة بالتقسيط قبل سداد كامل الثمن", "Cumhur Fukahâsı", "Mal teslim alınmış (kabzedilmiş) ve mülkiyet geçmişse, henüz taksitleri bitmemiş olsa dahi başkasına peşin veya vadeli satılabilir; borç alıcının zimmetinde kalır."),
    (271, "Yurt Dışında Yaşayan Müslümanın Vergi İadesi (Tax-Free) Alması", "استرداد الضرائب السياحية في الأسواق الخارجية", "Dört Mezhep İttifakı", "Yabancı devletin yasal mevzuatla izin verdiği vergi iadesini almak mubahtır, helal haktır."),
    (272, "Otomatik Aboneliklerin (Netflix, Spotify vb.) Unutularak Karttan Çekilmesi", "تجديد الاشتراكات الرقمية تلقائيا وحكم المبالغ المخصومة", "Hanefî Mezhebi (Rıza ve İcâre)", "Kullanıcı sözleşmede otomatik yenilemeyi onayladığı için çekilen ücretler hukuken geçerlidir; fesih hakkı sözleşme şartlarına tâbidir."),
    (273, "Borsada Birleşme ve Devralma (M&A) Süreçlerinde İçeriden Bilgi Ticareti (Insider Trading)", "التداول بناء على معلومات داخلية سرية قبل إعلانها", "Ruhsat Yoktur (Haksız Rekabet/Hile)", "Kamuya açıklanmamış gizli bilgilerle hisse alıp haksız kâr sağlamak fahiş aldatma ve piyasa hıyanetidir, kazancı gayrimeşrudur."),
    (274, "Kargo Kayıplarında Taşıyıcı Şirketin Tazminat Sorumluluğu (Ecîr-i Müşterek)", "تضمين شركات الشحن للبضائع التالفة والمفقودة", "Hanefî (İmâmeyn) ve Cumhur", "Kargo firmaları ecîr-i müşterek hükmündedir; mücbir afet hariç kargodaki her türlü ziyan ve hasarı tam değerinden tazmin etmekle mükelleftir."),
    (275, "İnternet Bankacılığında Yanlış IBAN'a Gönderilen Paranın İadesi", "تحويل المال لحساب خاطئ وحكم احتفاظ المستلم به", "Dört Mezhep İttifakı (Gasb/İade)", "Hataen hesabına para gelen kimsenin bu parayı harcaması haramdır; derhal bankaya veya sahibine iadesi farzdır."),
    (276, "Altın ve Gümüş Takıların Değiştirilmesinde İşçilik Farkı Ödenmesi", "مبادلة الذهب القديم بالجديد مع دفع فرق الصنعة", "İbn Teymiyye ve İbnü'l-Kayyim Tahrîci", "Klasik cumhura göre altın altınla gramı gramına satılmalı, işçilik ayrı ödenmelidir; İbn Teymiyye'ye göre ise işlenmiş takı artık eşya vasfı kazandığından makul işçilik farkıyla takası caizdir."),
    (277, "Mobil Uygulama Geliştiricilerinin Reklamsız Sürüm İçin Ücret Alması", "بيع النسخ الخالية من الإعلانات للتطبيقات والخدمات", "Dört Mezhep İttifakı (İcâre)", "Yazılım hizmetinde reklamdan arındırılmış konfor sunarak abonelik/satış bedeli almak meşru bir hak satışıdır."),
    (278, "Ortaklık Paylarının Noterden ve Ticaret Sicilinden Tescil Mecburiyeti", "توثيق حصص الشركاء رسميا لمنع جحود الحقوق", "Maslahat-ı Mürsele", "Hakların inkârını ve mirasçıların mağduriyetini önlemek adına şirket ortaklıklarını resmi tescil ettirmek vacip derecesinde gereklidir."),
    (279, "Kira Bedelinin Altın veya Gram Altın Olarak Belirlenmesi", "تحديد أجرة العقار بجرامات الذهب وسدادها عينا أو قيمة", "Hanefî ve Mâlikî Mezhepleri", "Kira bedelinin enflasyondan korunmak için gram altın olarak akdedilmesi ve vadesinde altın veya cari TL değeriyle ödenmesi caizdir."),
    (280, "Şirket Kredi Kartının Şahsi Harcamalarda Kullanılıp Sonradan Kapatılması", "استعمال بطاقة الشركة في المصاريف الخاصة وتسديدها لاحقا", "Hanefî ve Hanbelî (Vekâlet/İzin)", "Şirket yönetiminin açık izni ve suiistimal olmaması şartıyla cari hesaba borç kaydedilip derhal kapatılması caizdir; izinsiz kullanım emanete hıyanettir."),

    # MODERN TIP, BİYOETİK VE KADIN HALLERİ (281 - 315)
    (281, "Menopoz Döneminde Gelen Düzensiz Kanamaların Hayız mı İstihâza mı Olduğu", "دم اليأس والاضطرابات الهرمونية هل هو حيض أم استحاضة", "Hanefî Mezhebi (55 Yaş Sınırı)", "55 yaşından sonra gelen kanamalar aksi kesinleşmedikçe istihâza (özür) sayılır; kadın abdestini alıp namazını kılar, orucunu tutar."),
    (282, "Doğum Sonrası Kanamada (Nifas) 40 Günden Sonra Gelen Kan", "تجاوز دم النفاس أكثر من أربعين يوما وحكم الطهارة", "Hanefî ve Hanbelî Mezhepleri", "Nifasın azami süresi 40 gündür; 40 günü aşan kanama istihâza sayılır, kadın gusledip ibadetine başlar."),
    (283, "Düşük (Abortus) Yapan Kadının Kanamasının Nifas Sayılma Sınırı", "حكم الدم النازل بعد الإجهاض وسقوط السقط", "Hanefî ve Şâfiî Mezhepleri", "Düşen ceninde el, parmak veya yüz gibi organ belirmişse (genellikle 80-90 günden sonra) gelen kan nifastır; organ belirmemişse hayız veya istihâza hükmündedir."),
    (284, "Kanser Hastalarının Kemoterapide Saç, Kaş ve Kirpiklerinin Dökülmesinde Protez", "استعمال الباروكة والرموش الصناعية لمريضة السرطان", "Dört Mezhep İttifakı (Tedavi/Zaruret)", "Hastalık sebebiyle bedeninde belirgin kusur oluşan kimsenin psikolojik yıkımı önlemek için protez saç/kirpik kullanması caizdir, lanetlenen süs sayılmaz."),
    (285, "Yapay Zekâ ile Çalışan Cerrahi Robotların Ameliyat Yapması ve Hekim Sorumluluğu", "المسؤولية الطبية عن أخطاء الروبوتات الجراحية الذكية", "İslam Ceza Hukuku (Mübaşir/Mütesebbib)", "Robotu yöneten ve ameliyatı denetleyen cerrah hekim mesuliyet taşır; kusur ihmalden kaynaklanıyorsa diyet ve tazminat hekim veya hastaneye aittir."),
    (286, "Kornea Nakli ile Görme Engellinin Tedavisi ve Donörün Rızası", "زراعة قرنية العين من الموتى لفاقدي البصر", "Dört Mezhep Çağdaş İttifakı", "Gözün tamamı değil sadece saydam kornea tabakasının nakledilmesi cesede eziyet sayılmaz, görmeyi sağladığı için helal bir bağıştır."),
    (287, "Yatalak Hastaya Bakım Veren Yakınının veya Hemşirenin Avret Mahalline Bakması", "كشف عورة المريض العاجز للممرض والطبيب للضرورة", "Dört Mezhep İttifakı (Zaruret Miktarı)", "Kendi temizliğini yapamayan yatalak hastanın altını temizlemek ve tedavisini yapmak zaruret gereği caizdir; avrete ihtiyaç kadar bakılır."),
    (288, "Oruçlu İken Endoskopi ve Kolonoskopi Yaptırmak", "دخول المنظار الطبي إلى المعدة والأمعاء وأثره على الصيام", "Hanefî ve Şâfiî İhtilafı (İlaçsız Kuru Giriş)", "Cihazın üzerine kaydırıcı sıvı/ilaç sürülmüşse veya içeriye su/gaz verilmişse mideye ulaştığı için oruç bozulur; kuru girişte ise ihtilaf vardır, kaza ihtiyattır."),
    (289, "Ağır Yanık ve Yara Sebebiyle Başına Mesh Edemeyen Kimsenin Ameli", "سقوط مسح الرأس عند وجود الجروح والضمادات والجبائر", "Cumhur Fukahâsı", "Başında sargı olan sargının üzerine mesh eder; sargıyı açmak veya mesh etmek zarar veriyorsa o uzvun hükmü tamamen düşer, abdest tamamdır."),
    (290, "İdrar Kaçırma Pedi ve Yetişkin Hasta Bezinin Namaza Engeli", "الصلاة مع الحفاضات الطبية لمرضى السلس", "Mâlikî Mezhebi (Özür Ruhsatı)", "Pedde biriken necis madde gayriihtiyari çıktığı ve sürekli yenilenmesi fahiş meşakkat doğurduğu sürece vakit içinde kılınan namaza engel olmaz."),
    (291, "Estetik Amaçlı Burun Ameliyatı (Rinoplasti) ve Nefes Darlığı Birlikteliği", "جراحة تجميل الأنف لعلاج انحراف الوتيرة وتحسين المظهر", "Cumhur Fukahâsı (Kusuru Düzeltme)", "Nefes alma güçlüğü, kaza sonrası eğrilik veya belirgin bir anatomik çöküntüyü düzeltmek amacıyla yapılan burun ameliyatları caizdir."),
    (292, "Hacamat Yaptırmanın Orucu Bozup Bozmayacağı (Hâcim ve Mahcûm)", "احتجام الصائم وحكم حديث أفطر الحاجم والمحجوم", "Cumhur Fukahâsı (Hanefî, Mâlikî, Şâfiî)", "Hacamat orucu bozmaz; nassın nehyi kan kaybı sebebiyle halsiz düşüp orucu açma tehlikesine matuftur (Hanbelî'de ise bozar kavli vardır)."),
    (293, "Doğum Sancılarını Dindirmek İçin Yapılan Epidural (Prenses Doğum) İğnesi", "التخدير النصفي الإبيدورال أثناء الولادة الطبيعية", "Dört Mezhep İttifakı (Mubah Tedavi)", "Annenin dayanılmaz sancılarını hafifletmek için omuriliğe yapılan epidural anestezi mubah bir tedavidir."),
    (294, "Kanser Taramasında Kullanılan Radyoaktif İlaçlar ve Vücuttan Yayılımı", "المواد المشعة المستخدمة في الفحوصات الطبية وأثرها على الطهارة", "Dört Mezhep İttifakı", "Damardan verilen radyoaktif kontrast maddeler necis sayılmaz; idrar yoluyla atılmadıkça abdesti bozmaz."),
    (295, "Akıl Sağlığını Yitirmiş Bireylerin İbadet ve Mali Mükellefiyeti", "سقوط التكليف عن فاقد العقل والوعي وأداء الزكاة من ماله", "Dört Mezhep İttifakı", "Delilik ve koma halinde namaz ve oruç teklifi düşer; zekât ise cumhura göre malın hakkı olduğundan velisi tarafından ödenir."),
    (296, "Kulak Çöpü Kullanırken Kulağa İlaç Kaçması veya Pamuğun Islanması", "إدخال القطن والمنظفات في الأذن وأثره على الصيام", "Hanefî Sahih Kavli", "Kulağa sokulan kuru kulak çöpü veya dış kulak yolu temizliği orucu bozmaz; zardan dimağa sıvı inmediği sürece oruç tamdır."),
    (297, "Göz Lenslerinin Gusül ve Abdeste Engeli Olup Olmadığı", "العدسات اللاصقة وحكم وصول الماء إلى العين في الغسل", "Dört Mezhep İttifakı", "Gözün içini yıkamak ne abdestte ne gusülde farzdır; kontakt lensler abdeste ve gusle asla engel değildir."),
    (298, "Epilepsi (Sara) Nöbeti Geçiren Kimsenin Namazı ve Abdesti", "فقدان الوعي المؤقت بنوبات الصرع وأثره على الوضوء", "Dört Mezhep İttifakı", "Nöbet esnasında bilinç tamamen kapandığı için his kaybı sebebiyle abdest bozulur; nöbet geçince yeniden abdest alınır."),
    (299, "Ağız Kokusu İçin Kullanılan Spreyler ve Nane Aromalı Bantlar", "استعمال بخاخات الفم ومعطرات النفس للصائم", "Hanefî ve Şâfiî İhtilafı", "Mideye zerre gitmemek şartıyla koku spreyi orucu bozmaz; ancak boğaza kaçma riski yüksek olduğundan mekruhtur, kaçınmak esastır."),
    (300, "Gebeliğin İlk Haftalarında Alınan Ertesi Gün Hapının Hükmü", "استعمال حبوب منع الحمل الطارئة بعد الجماع", "Hanefî ve Şâfiî Tahrîci", "Döllenmiş yumurta henüz rahme tutunmadan önce alınan acil doğum kontrol ilaçları kürtaj sayılmaz; ancak keyfi alışkanlık haline getirilmemelidir."),
    (301, "Ceninin Cinsiyetini Öğrenmek İçin Yapılan Testlerin Caiziyeti", "الكشف عن جنس الجنين بالأشعة والتحاليل الطبية", "Dört Mezhep İttifakı", "Anne karnında cinsiyet oluştuktan sonra fenni aletlerle bunu öğrenmek gaybı bilmek sayılmaz; caizdir."),
    (302, "Şeker Hastalarının Parmaktan Kan Şekeri Ölçtürmesi", "وخز الإصبع لتحليل السكر للصائم وحكم الطهارة", "Şâfiî ve Mâlikî Mezhepleri", "Şeker ölçümü için çıkan damla kan abdesti bozmaz (Hanefî'de akarsa bozar); oruca ise hiçbir zararı yoktur."),
    (303, "Oruçlu Kimsenin Makattan Fitil (Süpozituvar) Kullanması", "استعمال التحاميل الشرجية للصائم وحكم القضاء", "Mâlikî Mezhebi (Besleyici Olmama Ruhsatı)", "Fitil doğrudan gıda ve su sağlamadığından Mâlikî mezhebine göre orucu bozmaz; Hanefî ve Şâfiî'de ise menfezden girdiği için kaza gerekir."),
    (304, "Ağır Demans (Alzheimer) Hastalarının Namaz ve Oruç Yükümlülüğü", "تكليف مريض الخرف والزهايمر بالصلاة والصيام", "Dört Mezhep İttifakı (Sâkıt Olması)", "Vakitleri, rekâtları ve idraki hatırlayamayan ileri evre demans hastalarından namaz ve oruç mükellefiyeti tamamen kalkar; kaza veya fidye gerekmez."),
    (305, "Vücuda Takılan Sürekli Şeker Takip Sensörlerinin Gusle Engeli", "أجهزة استشعار السكر اللاصقة على الجلد والغسل", "Hanefî ve Mâlikî (Zaruret ve Sargı Kıyası)", "Çıkarılması tıbbi ve mali külfet getiren deri altı glikoz sensörlerinin üzerinden su akıtılması veya mesh edilmesi gusül ve abdest için kâfidir."),
    (306, "Cilt Kanseri Tedavisinde Kullanılan Ağır Kimyasal Soyucular", "التقشير الكيميائي الطبي وتأثيره على وصول ماء الوضوء", "Cumhur Fukahâsı", "Tedavi sonrası yüzde oluşan kabuklanma ve su temas yasağında o bölgeye mesh edilir veya teyemmüm yapılır; ibadet aksatılmaz."),
    (307, "Bebek Emziren Annenin Göğüs Ucu Çatlağı İçin Sürdüğü Merhemlerin Yutulması", "دهن حلمة الثدي لعلاج التشققات ورضاع الطفل منه", "Dört Mezhep İttifakı", "Merhemin temiz ve helal içerikten olması kaydıyla bebeğin süt emerken ilacı yutması caizdir; anneye günah yoktur."),
    (308, "Oruçlu İken Burnuna Damla Damlatılması", "تقطير الدواء في الأنف ونزوله إلى الحلق للصائم", "Dört Mezhep İttifakı", "Burun ile boğaz arasında açık kanal olduğundan ilacın boğaza inmesi orucu bozar; Ramazan sonrası gününe gün kaza edilir."),
    (309, "Kadının Kaşlarının Ortasındaki ve Yüzündeki Fazla Kılları Aldırması", "إزالة شعر ما بين الحاجبين والوجه للمرأة", "Cumhur Fukahâsı", "Kadının yüzünde ve kaş ortasında çıkan sakal/bıyık benzeri fıtrata aykırı kılları alması lanetlenen 'nams' (kaş inceltme) kapsamında değildir; caizdir."),
    (310, "Kanda Pıhtılaşmayı Önleyen İlaç Kullananların Kanama Hallerinde Abdesti", "طهارة مستعملي مسيلات الدم عند بطء انقطاع النزف", "Mâlikî Mezhebi (Özür Ruhsatı)", "Kan sulandırıcı sebebiyle kesiklerin uzun süre kanaması durumunda kişi yaranın üzerini kapatıp Mâlikî mezhebini takliden namazını kılar."),
    (311, "Yoğun Bakımda Yatan Bilinçsiz Hastanın Kılınamayan Namazları", "قضاء الصلوات الفائتة عن المريض المغشى عليه في العناية المركزة", "Hanefî Mezhebi (1 Günü Aşan Baygınlıkta Kazanın Düşmesi)", "Bilinç kaybı 24 saati (5 vakti) aştığında Hanefî mezhebine göre geçmiş namazların kazası tamamen düşer; hasta sorumlu tutulmaz."),
    (312, "Tırnak Batması Tedavisinde Takılan Tel ve Koruyucuların Gusle Etkisi", "تركيب أسلاك تقويم الأظافر المنغرزة والطهارة", "Dört Mezhep İttifakı (Cebire Kıyası)", "Tırnak batmasını tedavi eden tıbbi bant ve tellerin altını yıkamak zorunlu değildir; üzerinden su akıtılması yeterlidir."),
    (313, "Akne Tedavisinde Kullanılan Ağır A Vitamini İlaçlarının Dudak Kuruluğu", "استعمال مرطبات الشفاه العلاجية للصائم", "Dört Mezhep İttifakı", "Aşırı kuruyan dudaklara sürülen nemlendirici krem mideye yutulmadığı sürece oruca ve abdeste zarar vermez."),
    (314, "Oruçlu Kimsenin Ağız Dolusu Kusması ve Kusmuğu İstem dışı Yutması", "القيء في نهار رمضان غلبة أو عمدا وأثره على الصوم", "Cumhur Fukahâsı (Hanefî ve Şâfiî)", "Kişi kendi isteğiyle kasten kusmadıkça, gelen kusmuk ağız dolusu olsa ve gayriihtiyari geri kaçsa dahi oruç kesinlikle bozulmaz."),
    (315, "Yapay Kalp Pili (Pacemaker) Taktıran Hastanın İbadet Durumu", "الصلاة مع وجود أجهزة تنظيم ضربات القلب المزروعة", "Dört Mezhep İttifakı", "Deri altına yerleştirilen elektronik kalp pilleri vücudun parçası sayılır; abdeste, gusle ve secdeye hiçbir mâni teşkil etmez."),

    # SOSYAL YAŞAM, ÇALIŞMA HAYATI VE KAMU HUKUKU (316 - 350)
    (316, "Gayrimüslim Ülkelerde Miras Paylaşımında Yerel Medeni Kanun Hükümleri", "توزيع التركة وفق القوانين الغربية ومخالفتها للفرائض", "Şer'î Taksim Farziyeti", "Müslüman mirasçılar yerel mahkeme kararıyla malları eşit alsalar dahi, kendi aralarında toplanıp terekeyi Kur'an'daki şer'î paylara göre rızayla yeniden taksim etmekle mükelleftir."),
    (317, "İş Yerinde Namaz Kılmasına İzin Verilmeyen İşçinin Tazminatlı Fesih Hakkı", "حق العامل في فسخ العقد للمنع من إقامة الصلاة المفروضة", "İslam İş Hukuku", "İşverenin farz namazı kıldırmamakta ısrar etmesi din özgürlüğü ihlalidir; işçi sözleşmeyi haklı feshedip tüm kıdem ve haklarını talep edebilir."),
    (318, "Toplu Taşımada veya Sokakta Bulunan Kayıp Şemsiye, Mont Gibi Eşyalar", "اللقطة في وسائل النقل العامة والمترو", "Cumhur Fukahâsı", "Toplu taşımada unutulan eşyalar kurumun kayıp eşya bürosuna teslim edilir; bulan kişi doğrudan sahiplenemez."),
    (319, "Gayrimüslim Komşuya Pişirilen Yemekten veya Kurban Etinden İkram Etmek", "إهداء لحم الأضحية وطعام المسلم للجيران غير المسلمين", "Dört Mezhep İttifakı (Müstehap)", "Savaş halinde olmayan gayrimüslim komşulara kurban etinden ve yemekten ikram etmek sıla-i ihsan ve sünnettir."),
    (320, "Apartman ve Site Aidatlarını Kasten Ödemeyen Komşunun Hukuki Durumu", "الامتناع عن سداد الرسوم المشتركة في العمارات السكنية", "Hanefî ve Mâlikî (Şart ve Maslahat)", "Ortak giderler zımni sözleşme hükmündedir; aidatı ödememek kul hakkı ve zulümdür; yönetim yasal yolla icraya başvurabilir."),
    (321, "Otel Odasında Unutulan veya Bilerek Bırakılan Eşyaların Tasarrufu", "حكم الأمتعة المتروكة في غرف الفنادق", "Hanefî Mezhebi (Terk Edilen Mal)", "Müşterinin değersiz görerek bilerek bıraktığı eşya mubahtır; unutulan kıymetli eşyalar ise otel emanetinde saklanır."),
    (322, "Sosyal Medya Hesaplarının Hacklenmesi ve Şantaj Yoluyla Para İstenmesi", "قرصنة الحسابات والابتزاز الرقمي للحصول على فدية", "Ruhsat Yoktur (Haram ve Terör)", "Başkalarının verisini çalıp şantaj yapmak gasp ve haramdır; şantajcıya para ödememek ve siber suçlara şikâyet etmek esastır."),
    (323, "Devlet Memurunun Görevi Sebebiyle Vatandaştan Aldığı Hediye ve Bahşiş", "هدايا العمال والمسؤولين وحكم حديث هدايا العمال غلول", "Dört Mezhep İttifakı (Haram/Gullûl)", "Kamu memurunun vatandaştan gördüğü iş karşılığı aldığı her türlü hediye ve rüşvet hadisin açık nassıyla haramdır ve kamuya aittir."),
    (324, "Cuma Günü Ezan Okunurken Alışveriş Yapmanın Hükmü", "البيع والشراء بعد أذان الجمعة الثاني", "Hanefî ve Şâfiî İhtilafı", "Cuma ezanı okunduğunda çarşıda alışveriş yapmak Hanefî'de tahrîmen mekruh, Şâfiî ve Hanbelî'de bâtıldır; namazla mükellef olmayanların (kadınlar/hastalar) alışverişi ise caizdir."),
    (325, "Gurbetteki Müslümanın Yerel Mahkemede Boşanması ve Dini Nikâha Etkisi", "أثر الطلاق المدني في المحاكم الغربية على العصمة الشرعية", "Çağdaş Fıkıh Heyetleri Kararı", "Kocanın mahkemede boşanma protokolünü bizzat imzalaması talak iradesi sayılır ve dini nikâh da hukuken son bulur (bâin talak)."),
    (326, "İşçinin İş Yerindeki Artık Malzeme ve Hurdayı Şahsi İşinde Kullanması", "استعمال الفضلات ومخلفات الورش دون إذن صاحب العمل", "Dört Mezhep İttifakı (İzin Şartı)", "Değersiz dahi olsa işverenin izni olmaksızın şirket hurdasını şahsi menfaate almak caiz değildir; açık izin şarttır."),
    (327, "Yol Kenarındaki Ağaçlardan Dökülen Meyveleri Yemenin Caiziyeti", "أكل الثمار المتساقطة من بساتين الآخرين على الطريق", "Hanbelî Mezhebi (Döküleni Yeme Ruhsatı)", "Duvar dışına taşan ve yola dökülüp çürüyecek olan sahipsiz meyvelerden yoldan geçenin toplayıp yemesi Hanbelî ve Mâlikî'de mubahtır; torbaya doldurmak caiz değildir."),
    (328, "Trafik Kazası Sonrası Karşı Tarafın Sigortasından Değer Kaybı Tazminatı Almak", "الحصول على تعويض هبوط القيمة السوقية للسيارة بعد الحادث", "Dört Mezhep İttifakı (Zararın Tazmini)", "Kusurlu aracın verdiği hasar sebebiyle arabada oluşan reel piyasa değer kaybını sigortadan tahsil etmek meşru haktır."),
    (329, "Gayrimüslim Bir Ülkede Seçimlerde Oy Kullanmanın Dini Hükmü", "المشاركة في الانتخابات السياسية في الدول غير الإسلامية", "Maslahat-ı Mürsele ve Ehven-i Şerreyn", "Müslüman azınlığın haklarını korumak, zulmü azaltmak ve daha adil olan adayı desteklemek amacıyla oy kullanmak caiz hatta maslahattır."),
    (330, "Miras Kalan Gayrimenkulü Kardeşlerden Birinin İzinsiz Tek Başına Kullanması", "استغلال أحد الورثة للعقار المشترك دون إذن الباقين", "Dört Mezhep İttifakı (Ecrimisil)", "Miras kalan mülkte diğer kardeşlerin de hissesi vardır; izinsiz tek başına oturan veya kiralayan kardeş diğer vârislere ecrimisil (kira payı) ödemekle yükümlüdür."),
    (331, "İşçinin Rapor Alarak İşe Gitmemesi ve Gerçeğe Aykırı Sağlık Raporu", "التمارض وأخذ التقارير الطبية الكاذبة للتغيب عن العمل", "Ruhsat Yoktur (Yalan ve Haksız Kazanç)", "Hasta olmadığı halde sahte rapor alıp işe gitmemek ve o günün maaşını almak yalan, sahtecilik ve haksız kazançtır; haramdır."),
    (332, "Kiralık Evin Duvarına Çivi Çakmak veya Boyasını Değiştirmek", "إحداث التغييرات اليسيرة في العين المستأجرة", "Hanefî ve Mâlikî (Örf Şartı)", "Tablo asmak gibi örfe uygun ufak çiviler caizdir; ancak mülke kalıcı zarar veren veya değer düşüren büyük tadilatlar ev sahibinin iznine bağlıdır."),
    (333, "Marketlerde Poşet Ücreti Alınmasının Dinî Açıdan Sıhhati", "فرض رسوم على أكياس التسوق لحماية البيئة", "Dört Mezhep İttifakı", "Plastik israfını ve çevre kirliliğini önlemek adına devletin poşete ücret koyması kamu maslahatına uygundur, helaldir."),
    (334, "Çocuğunu Dövmenin Sınırı ve İslam Hukukunda Terbiye Disiplini", "ضرب الأولاد والطلاب وحكم التعذيب البدني في التأديب", "Cumhur Fukahâsı (Ağır Şiddetin Haramlığı)", "Yüze vurmak, iz bırakacak veya kemik kıracak derecede şiddet uygulamak haramdır; terbiye nasihat ve mahrumiyetle yapılır."),
    (335, "Komşunun Balkonundan veya Bahçesinden Rahatsız Eden Dumana Müdahale", "دفع ضرر الدخان والشواء المفرط عن الجيران", "Dört Mezhep İttifakı (Zararın İzalasi)", "Aşırı duman ve koku komşuya açık zarar (zarar-ı fahiş) veriyorsa hâkim veya zabıta yoluyla engellenmesi haktır."),
    (336, "İbadet Yerlerine (Camilere) Girişte Güvenlik Araması Yapılması", "التفتيش الأمني على أبواب المساجد لحفظ الأمن", "Maslahat-ı Mürsele", "Cemaatin can güvenliğini korumak ve terör saldırılarını önlemek amacıyla cami kapılarında üst ve çanta araması yapılması meşrudur."),
    (337, "Sosyal Medyadaki Çekilişlere (Giveaway) Katılmanın Hükmü", "المسابقات الرقمية والسحب على الجوائز بدون رسوم اشتراك", "Dört Mezhep İttifakı (Hibe)", "Katılımcıdan hiçbir ücret veya bilet parası alınmayan, sırf takip ve beğeni karşılığı yapılan çekilişler kumar sayılmaz; hediye hibedir."),
    (338, "Yalan Şahitlik Yaparak Mahkemeyi Yanıltmanın Cezai ve Uhrevi Boyutu", "شهادة الزور في القضاء وحكم الرجوع عنها", "Dört Mezhep İttifakı (Büyük Günah ve Tazmin)", "Yalan şahitlik kebâirdendir; şahit yalanı sebebiyle verilen zararları şahsi malından tazmin etmekle mükelleftir."),
    (339, "Kamu Kurumundaki Resmi Aracı Şahsi Tatilde veya İhtiyaçta Kullanmak", "استعمال سيارات المصلحة الحكومية في الأغراض الخاصة", "Ruhsat Yoktur (Beytülmâl Hıyaneti)", "Kamunun aracı milletin ortak malıdır; yetkisiz şahsi gezilerde kullanmak kul hakkıdır ve haramdır."),
    (340, "Ev Sahibinin Kiracıyı Sözleşme Bitmeden Sebepsiz Yere Tahliye Etmesi", "طرد المستأجر تعسفيا قبل انتهاء مدة العقد", "Cumhur Fukahâsı (Akit Bağlayıcılığı)", "Kira akdi süresi dolmadan haklı ve yasal bir gerekçe olmaksızın kiracıyı zorla evden çıkarmak akdi bozmaktır, caiz değildir."),
    (341, "Lokantada Yenen Yemekten Sonra Masada Kalan Fazla Artıkların Tasarrufu", "التعامل مع بقايا الأطعمة في المطاعم وتفادي الإسراف", "Dört Mezhep İttifakı", "Artan temiz yemeklerin çöpe atılması israftır ve haramdır; paketlenip müşteriye verilmesi veya sokak hayvanlarına ayrılması farzdır."),
    (342, "Cenazelerde Çelenk Göndermek ve Aşırı Gösterişli Törenler Düzenlemek", "إرسال أكاليل الزهور والإسراف في مراسم العزاء", "Cumhur Fukahâsı (Mekruh/İsraf)", "Çelenk gibi faydasız mali harcamalar israftır; cenaze sahibine yük getirecek şatafatlı taziye sofraları bid'attir."),
    (343, "Taksiye Binip Taksimetrenin Yazdığı Ücretten Fazlasını Talep Etmek", "طلب سائق الأجرة زيادة على التسعيرة الرسمية المحددة", "Ruhsat Yoktur (Haksız Kazanç)", "Belirlenen resmi taksimetre rayicinin üzerinde keyfi fazlalık istemek haksız kazançtır; rızasız alınamaz."),
    (344, "Bebek Bakıcısının Çocuğun Güvenliğindeki Hukuki Sorumluluğu", "مسؤولية جليسة الأطفال عن الحوادث المنزلية", "Hanefî ve Cumhur (Emanetçi/Taddi)", "Bakıcı emanetçidir; açık kusuru ve ihmali (taddî) olmadıkça çocuğun kazaen yaralanmasından tazminatla sorumlu tutulmaz."),
    (345, "Öğrencinin Sınavda Kopya Çekerek Başarı Elde Etmesi ve Diploması", "الغش في الامتحانات الدراسية وأثره على شرعية الشهادة", "Dört Mezhep İttifakı (Haram/Hile)", "Kopya çekmek haramdır; ancak hileyle mezun olan kimse işe girdikten sonra mesleğini fiilen layıkıyla ve hakkıyla icra ediyorsa maaşı emeğin karşılığıdır."),
    (346, "Apartmanda Güvercin, Kedi veya Köpek Beslemenin Komşuluk Hukuku", "تربية الحيوانات الأليفة في الشقق المشتركة وإيذاء الجيران", "Hanefî ve Mâlikî (Zararın İzalasi)", "Hayvan beslemek mubahtır; fakat komşuya koku, pislik ve dayanılmaz sesle zarar veriyorsa zararın derhal giderilmesi şarttır."),
    (347, "İşverenin Çalışanlarına Dinlenme, Tuvalet ve İbadet Molası Vermesi", "إلزام صاحب العمل بفترات الراحة وقضاء الحاجة للعمال", "İslam Kamu Maslahatı", "İşçiye insani ihtiyaçları ve farz namazı eda etmesi için makul mola vermek işverenin şer'î adalet borcudur."),
    (348, "Sokak Çalgıcılarına veya Dilencilere Verilen Paranın Hükmü", "إعطاء المال للمتسولين وامتهان السؤال في الطرقات", "Hanefî ve Şâfiî", "Gerçek muhtaç olup olmadığı bilinmeyen dilenciye verilen para sadaka sevabı taşır; ancak profesyonel dilenciliği meslek edinenleri teşvik etmemek evladır."),
    (349, "Kişinin Kendi Malını Hayattayken İstediği Vakfa veya Kuruma Bağışlaması", "تبرع الإنسان بجميع ماله في وجوه البر حال حياته وصحته", "Hanefî (Ebû Yûsuf) ve Şâfiî", "Sağlığı yerinde olan kimsenin malını hayattayken dilediği hayır kurumuna hibe etmesi geçerlidir; vasiyet gibi üçte birle sınırlı değildir (fakat çocukları muhtaç bırakmak mekruhtur)."),
    (350, "CÂMİU'R-RUHAS ORTA MÜHÜR: Modern Hayatta Şüphelerden Sakınma (Verâ') İlkesi", "قاعدة الورع والشبهات في فقه المعاملات والطب المعاصر", "Dört Hak Mezhep Cumhurunun İttifakı", "251-350 arasındaki mikro düğümlerde verilen ruhsatlar meşakkat anında amel içindir; imkânı olanın 'Helal bellidir, haram bellidir; ikisi arasındaki şüphelilerden kaçının' nassına riayet etmesi dinin kemâlidir.")
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
    print("[*] 2-WORKER PARALEL İŞÇİ HAVUZU: MESELE 251 - 350 (FAZ 11)")
    print("=" * 80)

    completed = load_checkpoints()
    print(f"[+] Başlangıçtaki Doğrulanmış Mesele Sayısı: {len(completed)}")

    file_lock = threading.Lock()
    checkpoint_lock = threading.Lock()
    chapter_file = os.path.join(CHAPTERS_DIR, "24_modern_ve_sosyal.md")

    compiler = NeuroSymbolicFikhEngine()

    tasks_to_run = []
    for item in MESELER_FAZ_11:
        m_id = item[0]
        key = f"batch_{m_id:03d}"
        if key not in completed:
            tasks_to_run.append(item)

    print(f"[*] İşlenecek Kalan Mesele Sayısı: {len(tasks_to_run)}")
    if not tasks_to_run:
        print("[!] Bu fazdaki tüm meseleler zaten derlenmiş!")
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

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_issue, item) for item in tasks_to_run]
        for f in as_completed(futures):
            f.result()

    print("\n" + "=" * 80)
    print(f"[✓] FAZ 11 BAŞARIYLA TAMAMLANDI! Toplam Doğrulanan Mesele: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
