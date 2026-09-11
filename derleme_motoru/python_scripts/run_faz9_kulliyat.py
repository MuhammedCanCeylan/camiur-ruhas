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

DUGUMLER_FAZ_9 = [
    {
        "bolum_id": "22_siyer_diyet",
        "bolum_adi": "Kitâbü'l-Cinâyât, Diyet ve Siyer (Can Güvenliği ve Kamu Hukuku)",
        "dosya": "22_siyer_diyet.md",
        "meseleler": [
            (106, "Meşru Müdafaa Sırasında Saldırganın Öldürülmesi ve Cezai Sorumluluk", "الدفاع الشرعي عن النفس والعرض والمال ودفع الصائل", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Saldırganın kanının heder olması)",
                "ruhsat_hukum": "Canına, ırzına veya malına kasteden saldırganı (sâil) defetmek için başka çare kalmadığında öldürmek meşrudur; öldüren kimseye kısas, diyet veya keffâret terettüp etmez, saldırgan hederdir.",
                "hanefi_hukum": "Defi imkânsız olan saldırganı öldürmek caizdir; katile kısas veya diyet gerekmez.",
                "safii_hukum": "Nefsi ve malı müdafaa haktır; kademeli def esastır, ölüm gerçekleşirse kanı hederdir.",
                "maliki_hukum": "Saldırganın tecavüzünü savuştururken öldürülmesi durumunda hiçbir mali ve cezai mesuliyet doğmaz.",
                "hanbeli_hukum": "Nassın açık hükmü gereğince müdafaa esnasında ölen saldırgan için tazminat ve kısas yoktur."
            }),
            (107, "Trafik Kazasında Kusurlu Olarak Adam Öldürmede Keffâret ve Diyetin Âkıleye Yüklenmesi", "القتل الخطأ في حوادث السير المعاصرة وتحمل العاقلة للدية", {
                "ruhsat_mezhep": "Hanefî Mezhebi ve Çağdaş Kaza Sigortası Tahrîci",
                "ruhsat_hukum": "Trafik kazasında kasıtsız ölüme sebebiyet veren sürücünün ödeyeceği hataen katil diyeti sigorta fonu veya âkıle (akraba dayanışması) tarafından karşılanır; sürücü bizzat iflas ettirilmez, oruç keffâreti ise gücü yetene aittir.",
                "hanefi_hukum": "Hataen katilde diyet şahsa değil âkıleye terettüp eder; sigorta havuzu modern âkıle hükmündedir.",
                "safii_hukum": "Diyet üç yıla yayılarak âkıleden tahsil edilir; katil ayrıca 2 ay peş peşe oruç tutar.",
                "maliki_hukum": "Hataen öldürmede diyet âkıleye aittir, katil bizzat ödemez.",
                "hanbeli_hukum": "Âkılenin diyeti üstlenmesi nassla sabittir; sigorta tazminatı bu borcu düşürür."
            }),
            (108, "Savaş Hukukunda Sivillerin, Kadınların, Çocukların ve Çevrenin Dokunulmazlığı", "حرمة قتل النساء والأطفال والرهبان وتخريب البنيان والشجر في الحرب", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Fiilen çatışmaya girmeyen kadınlar, çocuklar, din adamları, yaşlılar, hastalar ve çiftçilerin öldürülmesi kesinlikle haramdır; ağaçların kesilmesi, su kaynaklarının ve sivil binaların tahrip edilmesi icmâen men edilmiştir.",
                "hanefi_hukum": "Savaşmayan kadın, çocuk ve acizlerin öldürülmesi caiz değildir; askeri zaruret olmadıkça tahribat yapılmaz.",
                "safii_hukum": "Masum canların öldürülmesi kat'iyyen haramdır; savaşa katılmayan sivil hedef alınamaz.",
                "maliki_hukum": "Kadın, çocuk, ruhban ve mabetlerin tahrip edilmesi nehyedilmiştir.",
                "hanbeli_hukum": "Resulullah'ın açık yasakları gereğince siviller ve çevre unsurları dokunulmazdır."
            }),
            (109, "Gayrimüslimlerle Yapılan Barış, Vize ve Güvenlik Anlaşmalarına Riayet (Eman)", "عقد الأمان والهدنة وحرمة الغدر بالمعاهد والمستأمن", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Cumhur)",
                "ruhsat_hukum": "Vize, pasaport veya uluslararası anlaşma ile bir İslam ülkesine giren gayrimüslimin (müstemen) canı, malı ve ırzı tam koruma altındadır; ona hıyanet etmek, malını çalmak veya zarar vermek büyük günahtır ve haramdır.",
                "hanefi_hukum": "Eman verilen kimsenin malı ve canı dârülislâmda dokunulmazdır; ona tecavüz eden tazminatla yükümlüdür.",
                "safii_hukum": "Eman akdi bağlayıcıdır; müstemene zarar vermek ahdi bozmak ve haramdır.",
                "maliki_hukum": "Ahde vefa farzdır; vize sahibi gayrimüslimin hakları korunur.",
                "hanbeli_hukum": "Hadis-i şerifin 'Kim bir muâhide zulmederse kıyamet günü hasmı benim' uyarısı gereği eman mutlaktır."
            })
        ]
    },
    {
        "bolum_id": "08_etime_derin",
        "bolum_adi": "Kitâbü'l-Et'ime, Eşribe ve Sayd (İleri Gıdalar ve Kesim Düğümleri)",
        "dosya": "08_etime.md",
        "meseleler": [
            (110, "Eğitilmiş Av Köpeğinin veya Av Kuşunun Öldürdüğü Hayvanın Yenmesi", "صيد الكلب المعلم والجوارح إذا قتل الصيد ولم يدرك حيا", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Köpeğin avdan yememesi şartıyla)",
                "ruhsat_hukum": "Besmele ile salınmış eğitimli av köpeğinin veya şahinin yakalayıp öldürdüğü av hayvanı, avcı yetiştiğinde ölmüş olsa dahi boğazlanmış sayılır; eti helaldir ve temizdir.",
                "hanefi_hukum": "Eğitilmiş köpek avı öldürse dahi besmeleyle gönderilmişse eti helaldir; köpek avdan yerse haram olur.",
                "safii_hukum": "Avcı canlı yetiştiremezse köpeğin öldürdüğü av tezkiye edilmiş kabul edilir, yenir.",
                "maliki_hukum": "Eğitilmiş hayvanın yakalayıp öldürdüğü av helaldir.",
                "hanbeli_hukum": "Nassın açık izniyle eğitilmiş av hayvanının öldürdüğü av tezkiye hükmündedir."
            }),
            (111, "Elektrik Şoku veya Karbondioksit Gazı ile Sersemletilerek Kesilen Hayvanlar", "تدويخ الحيوان بالصدمة الكهربائية قبل الذبح", {
                "ruhsat_mezhep": "Çağdaş Fıkıh Kurulları ve Diyanet Tahrîci",
                "ruhsat_hukum": "Hayvan kesilmeden önce şok verildiğinde henüz canlılığını yitirmemiş (kalbi atar) vaziyetteyken besmele ile boğazlanırsa kesim meşrudur ve eti helaldir; şok esnasında ölen hayvan ise leştir, yenmez.",
                "hanefi_hukum": "Boğazlama anında hayatta olduğu kesin olan hayvanın şoklanması mekruh olmakla birlikte eti helaldir.",
                "safii_hukum": "Hayat emâresi mevcutken boğazlanan hayvan helaldir.",
                "maliki_hukum": "Hayat-ı müstakırra varken yapılan kesim geçerlidir.",
                "hanbeli_hukum": "Kesim esnasında hareket eden veya kanı fışkıran hayvan tezkiye edilmiş sayılır."
            }),
            (112, "İlaç Kapsüllerinde ve Gıda Katkılarında Kullanılan Jelatin ve Enzimler", "استعمال الجيلاتين والإنزيمات الحيوانية في الأدوية والأغذية", {
                "ruhsat_mezhep": "Hanefî ve Mâlikî Mezhepleri (İstihâle ve Umum-ı Belvâ Tahrîci)",
                "ruhsat_hukum": "İlaç kapsülleri, aşılar veya gıdalarda kullanılan domuz/leş menşeli jelatin ve peynir mayası enzimleri, kimyasal süreçte yapısal değişime (istihâle) uğradığı ve alternatif bulunmadığı hallerde tedavi ve gıda için caizdir.",
                "hanefi_hukum": "İstihâleye uğrayan veya peynir mayası gibi cansız dokulardan alınan enzimler temizdir.",
                "safii_hukum": "Domuz menşeli maddeler haramdır; ancak hayati zaruret ve muadilsiz ilaç halinde ruhsat vardır.",
                "maliki_hukum": "Zâtı başkalaşan maddeler necis olmaktan çıkar, ilaca karışması affedilir.",
                "hanbeli_hukum": "Zaruret halinde helal olmayan nesnelerle tedavi caizdir; istihale tartışmalıdır."
            }),
            (113, "Alkolsüz Bira, Boza ve Fermantasyon Sonucu Eser Miktarda Oluşan Alkolün Hükmü", "المشروبات المخمرة التي تحتوي على نسبة ضئيلة غير مسكرة من الكحول", {
                "ruhsat_mezhep": "Hanefî Mezhebi (İmam Ebû Hanîfe ve Ebû Yûsuf)",
                "ruhsat_hukum": "Üzüm ve hurma şarabı dışındaki içeceklerde, fermantasyon veya aroma çözücü sebebiyle ortaya çıkan ve sarhoşluk vermeyecek derecedeki eser miktardaki (binde birkaç) alkol necâset sayılmaz; içilmesi helaldir.",
                "hanefi_hukum": "Hamr dışındaki mayalanmış içeceklerde sarhoş etmeyen az miktarı tüketmek haram ve necis değildir.",
                "safii_hukum": "Çoğu sarhoş edenin damlası da haram ve necistir; bilerek alkol katılmışsa içilmez.",
                "maliki_hukum": "Sarhoş edici vasfı olmayan tabii fermantasyon kalıntıları umum-ı belvâ sebebiyle bağışlanır.",
                "hanbeli_hukum": "Kasıtlı alkol ilavesi haramdır; fakat kendiliğinden oluşan eser miktar sarhoş etmedikçe caizdir."
            }),
            (114, "Laboratuvar Ortamında Kök Hücreden Üretilen Kültür (Yapay) Etin Hükmü", "حكم اللحوم المستنبتة مخبريا من الخلايا الجذعية", {
                "ruhsat_mezhep": "Çağdaş Fıkıh Akademileri (İslâm Fıkıh Akademisi Kararları)",
                "ruhsat_hukum": "Canlı bir hayvandan koparılmayıp usûlüne uygun kesilmiş helal bir hayvanın kök hücresinden temiz besi ortamında üretilen yapay et helaldir ve temizdir; 'meyte' (leş) sayılmaz.",
                "hanefi_hukum": "Temiz ve helal asıldan türeyen gıdalar bizzat zararlı olmadıkça helaldir.",
                "safii_hukum": "Hücrenin alındığı kaynak helal kesim ise elde edilen et de helaldir.",
                "maliki_hukum": "Necis madde katılmadan üretilen yeni besinler eşyada asıl olan ibâhadır kuralına tâbidir.",
                "hanbeli_hukum": "Haram kılınan bir nassa girmeyen ve zararı bulunmayan gıdalar helaldir."
            })
        ]
    },
    {
        "bolum_id": "10_eyman_derin",
        "bolum_adi": "Kitâbü'l-Eymân ve'n-Nüzûr (İleri Yemin ve Adak Düğümleri)",
        "dosya": "10_eyman.md",
        "meseleler": [
            (115, "Yemin Ederken Tevriye (Çift Anlamlı Söz) Kullanmanın Caiziyeti", "استعمال التورية والتعريض في اليمين للمظلوم والمعذور", {
                "ruhsat_mezhep": "Şâfiî ve Hanbelî Mezhepleri (Mazlum için tevriye ruhsatı)",
                "ruhsat_hukum": "Zulümden, haksız gasptan veya canını kurtarmaktan başka çaresi olmayan kimsenin yemin ederken karşı tarafın anladığı anlamın dışında kalbinden meşru bir manayı kastetmesi (tevriye) caizdir; yalan sayılmaz, keffâret gerekmez.",
                "hanefi_hukum": "Yeminde yemin ettirenin niyeti esastır; zalime karşı tevriye caiz olmakla birlikte hak davada bâtıldır.",
                "safii_hukum": "Zulüm ve meşakkat anında tevriye caizdir; yemin bozulmuş sayılmaz.",
                "maliki_hukum": "Mazlum için tevriyeli yemin caizdir; zalimin yemini ise niyetine göredir.",
                "hanbeli_hukum": "Haksızlığa uğrayanın kalbindeki niyete göre yemin etmesi sahihtir, günah ve keffaret yoktur."
            }),
            (116, "Zorla, Baskı veya Tehdit Altında Ettirilen Yeminin Hükmü", "يمين المكره وحكم انعقادها ولزوم الكفارة فيها", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Ölüm, işkence veya hapis tehdidiyle zorla ettirilen yeminler dinde kesinlikle mün'akit olmaz (bağlayıcı değildir); kişi bu yemine aykırı davransa dahi hiçbir keffâret ödemez.",
                "hanefi_hukum": "İkrah altında edilen yemin geçerlidir; yemin bozulursa keffaret verilmelidir.",
                "safii_hukum": "İkrah altındaki yemin lağvdır; hiçbir hüküm ve keffaret doğurmaz.",
                "maliki_hukum": "Baskı altındaki yemin geçersizdir, keffaret gerekmez.",
                "hanbeli_hukum": "İradesiz yemin hükümsüzdür; nassın açık affına dahildir."
            }),
            (117, "Yemin Keffâretinde 10 Fakiri Doyurmak Yerine Nakit Bedelini Ödemek", "إخراج القيمة بالنقود في كفارة اليمين بدلا من الطعام", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Kıymet intikali ruhsatı)",
                "ruhsat_hukum": "Yeminini bozan kimse 10 fakire buğday/arpa dağıtmak veya onları doyurmak yerine, 10 fakirin bir günlük doyma bedelini doğrudan nakit para olarak tek veya ayrı fakirlere verebilir; sahihtir.",
                "hanefi_hukum": "Keffâretlerde kıymet ödemek caizdir; nakit para fakir için daha faydalıdır.",
                "safii_hukum": "Aynen nassda zikredilen yiyecek maddesinin verilmesi farzdır; nakit ödeme bâtıldır.",
                "maliki_hukum": "Aynî yiyecek verilmesi esastır, nakit caiz görülmez.",
                "hanbeli_hukum": "Yiyeceğin bizzat kendisi verilmelidir; para ödemek keffareti düşürmez."
            })
        ]
    },
    {
        "bolum_id": "23_lukata_icare",
        "bolum_adi": "Kitâbü'l-Lukata, İcâre ve Çağdaş Mülkiyet (Kira, Tazminat ve Haklar)",
        "dosya": "23_lukata_icare.md",
        "meseleler": [
            (118, "Kayıp ve Sahipsiz Eşyayı (Lukata) Bulan Kimsenin Sahiplenme Şartları", "التقاط اللقطة وتملكها بعد التعريف واللقطة التافهة اليسيرة", {
                "ruhsat_mezhep": "Hanbelî ve Mâlikî Mezhepleri (Değersiz/hafif eşyada derhal temellük ruhsatı)",
                "ruhsat_hukum": "Yolda bulunan cüzi, değersiz veya sahibinin aramayacağı küçük eşyalar (kalem, bozuk para, mendil vb.) için 1 yıl ilân şartı yoktur; bulan kimse derhal sahiplenip kullanabilir.",
                "hanefi_hukum": "Hafif eşya bir müddet bekletilir; sahibi çıkmazsa fakire tasadduk edilir veya fakirse kendisi kullanır.",
                "safii_hukum": "Kıymetsiz eşyada zann-ı galip kadar beklenir; 1 yıl şartı büyük mallara mahsustur.",
                "maliki_hukum": "Önemsiz eşyayı bulan kimsenin ilân etmeksizin istifade etmesi helaldir.",
                "hanbeli_hukum": "Kıymeti az olan şeylerde ilân gerekmez; bulan doğrudan temellük edebilir."
            }),
            (119, "Gasbedilen veya Çalınan Paranın Enflasyon Değer Kaybıyla Birlikte Tazmini", "تضمين الغاصب نقص القوة الشرائية للنقود المغصوبة", {
                "ruhsat_mezhep": "İmam Ebû Yûsuf Tahrîci ve Mâlikî Maslahat Kuralı",
                "ruhsat_hukum": "Haksız yere gasp edilen veya borcu geciktirilen paranın enflasyon sebebiyle değer kaybetmesi halinde, mağdurun reel zararını önlemek amacıyla paranın gasp edildiği gündeki alım gücü üzerinden tazmin ettirilmesi caizdir.",
                "hanefi_hukum": "İmam Ebû Hanîfe'ye göre misli ödenir; Ebû Yûsuf'a göre fahiş değer kaybı varsa kıymeti ödenir.",
                "safii_hukum": "Parada nominal misil esastır; enflasyon farkı faiz şüphesi sayılır.",
                "maliki_hukum": "Haksız fiilde zararın tam tazmini (zarar izale edilir) esastır.",
                "hanbeli_hukum": "Gasbda aynın veya mislin tazmini kuraldır; ancak sulh yoluyla telafi mubahtır."
            }),
            (120, "Kiralanan Mülkün Mücbir Sebeple (Afet, Salgın, İflas) Vaktinden Önce Feshi", "فسخ عقد الإجارة بالأعذار الطارئة والجائحة", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Özür sebebiyle kira feshi imtiyazı)",
                "ruhsat_hukum": "Kiracının iflas etmesi, tayininin çıkması, dükkânın kapatılması gibi öngörülemeyen bir mazeret (özür) ortaya çıktığında kiracı sözleşmeyi tek taraflı feshedebilir; oturmadığı ayların kirası talep edilemez.",
                "hanefi_hukum": "İcâre akdinde mazeret fesih sebebidir; zararı önlemek için sözleşme feshedilir.",
                "safii_hukum": "Kira akdi bağlayıcıdır (lâzım); kiracının şahsi özrü sebebiyle akit tek taraflı bozulamaz.",
                "maliki_hukum": "Genel afet (câiha) durumunda kira bedeli tenzil edilir veya feshedilir.",
                "hanbeli_hukum": "Aynın menfaati tamamen yok olmadıkça şahsi özürle fesih caiz görülmez."
            }),
            (121, "İşçinin Geçici Hastalık Sebebiyle Çalışamadığı Günlerin Ücret Hakkı", "أجر العامل عند المرض الطارئ والتعطيل الخارج عن إرادته", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Hâs ecîr tahrîci) ve Çağdaş İş Hukuku",
                "ruhsat_hukum": "Belirli süreli çalışan işçi (ecîr-i hâs) kendi kusuru olmaksızın hastalandığında veya işverenin iş verememesi durumunda mesaisini tahsis etmiş sayıldığından ücreti tam ödenir; kesinti yapılmaz.",
                "hanefi_hukum": "Kendini işe hazır tutan ecîr-i hâs işveren iş vermese veya hastalık arız olsa da ücrete hak kazanır.",
                "safii_hukum": "Ücret fiili menfaatin karşılığıdır; çalışılmayan günlerin ücreti düşer.",
                "maliki_hukum": "Kısa süreli hastalıklar örfen affedilir ve ücretten kesilmez.",
                "hanbeli_hukum": "Amel gerçekleşmedikçe ücret hak edilmez; ancak sözleşme şartları bağlayıcıdır."
            }),
            (122, "Ayıplı/Kusurlu Çıkan Malda Malı İade Etmeyip Değer Farkını (Erş) Talep Etmek", "أخذ أرش العيب دون رد المبيع بالتراضي أو تعذر الرد", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (İmam Ahmed b. Hanbel)",
                "ruhsat_hukum": "Satın aldığı malda gizli bir kusur (ayıp) gören alıcı, malı tamamen iade etmek zorunda değildir; dilerse malı elinde tutup ayıbın sebep olduğu değer kaybını (erş) satıcıdan nakit olarak tazmin alabilir.",
                "hanefi_hukum": "Satıcı razı olmadıkça sadece değer farkı alınamaz; ya tam kabul edilir ya da tamamen iade edilir.",
                "safii_hukum": "Mal mevcutsa ya aynen iade edilir ya da olduğu gibi kabul edilir; tek taraflı erş alınamaz.",
                "maliki_hukum": "Kusur malın esasına aitse iade edilir; cüzi ise değer düşümü yapılır.",
                "hanbeli_hukum": "Alıcı muhayyirdir; dilerse malı geri verir, dilerse elinde tutup değer farkını (erş) satıcıdan alır."
            }),
            (123, "Fikrî Mülkiyet, Yazılım, Marka ve Telif Haklarının Satışı ve Mirası", "بيع البرمجيات وحقوق الابتكار والتأليف والعلامات التجارية", {
                "ruhsat_mezhep": "Çağdaş İslâm Fıkıh Akademisi ve Mâlikî Maslahat Tahrîci",
                "ruhsat_hukum": "Yazılım, telif hakkı, ticari marka ve patentler şer'an mütekavvim ve meşru birer maldır; satışı, kiralanması, şirket sermayesi yapılması ve mirasçılara intikali ittifakla caizdir.",
                "hanefi_hukum": "Örf ve teamülde kıymeti olan mücerret haklar semen ve mal hükmünde kabul edilir.",
                "safii_hukum": "Menfaati meşru ve ekonomik değeri olan her hak akde konu olabilir.",
                "maliki_hukum": "İnsanların mülk edindiği ve ziyanında tazmin ettirdiği fikrî değerler maldır.",
                "hanbeli_hukum": "Mubah menfaati bulunan her nesne ve hak satış akdine konu teşkil eder."
            }),
            (124, "Döviz ve Altın Alım-Satımında Banka Hesabına Geçişin Hükmî Kabz Sayılması", "القبض الحسابي في صرف العملات والذهب عبر الحسابات البنكية", {
                "ruhsat_mezhep": "Çağdaş Fıkıh Heyetleri (AAOIFI ve Diyanet Kararları)",
                "ruhsat_hukum": "İnternet bankacılığında veya borsada yapılan döviz ve altın alımlarında paranın ve altının anında hesaba yansıması (kaydî teslimat) şer'an elden ele kabz hükmündedir; vadeli ribâ sayılmaz, caizdir.",
                "hanefi_hukum": "Hükmî kabz fiili kabz gibidir; hesap bakiyesinin bloke edilmesi kabz sayılır.",
                "safii_hukum": "Mecliste bedellerin karşılıklı teslimi kaydî olarak gerçekleştiğinde sarf akdi tamamdır.",
                "maliki_hukum": "Örfen kabz sayılan her tasarruf imkânı akdi ribâdan kurtarır.",
                "hanbeli_hukum": "Mülkiyetin anında hesaba intikal etmesi şer'î kabzın şartını yerine getirir."
            }),
            (125, "Şarta Bağlı Hibe ve Geri Dönüşlü İntifa Sözleşmeleri (Umrâ ve Rukbâ)", "عقد العمرى والرقبى وحكم عودة العين إلى الواهب بعد الوفاة", {
                "ruhsat_mezhep": "Mâlikî Mezhebi ve Hanbelî Rivayeti (Şartın geçerliliği)",
                "ruhsat_hukum": "Bir kimsenin 'Bu evde yaşadığın sürece otur, ölünce ev bana veya vârislerime geri dönsün' şartıyla evini birine tahsis etmesi (umrâ/rukbâ) geçerlidir; ev bağışlanana miras kalmaz, asıl sahibine döner.",
                "hanefi_hukum": "Umrâ akdi mülkiyet hibesidir; geri dönüş şartı fâsittir, ev bağışlananın vârislerine kalır.",
                "safii_hukum": "Hibe geçerli, geri dönme şartı bâtıldır; mülk bağışlanana temlik edilmiş olur.",
                "maliki_hukum": "Vâkıfın şartı geçerlidir; intifa süresi dolunca mülk asıl sahibine geri döner.",
                "hanbeli_hukum": "İki rivayetten birine göre şart sahihtir; mülk şart koşulan kişiye iade edilir."
            })
        ]
    }
]

def main():
    print("=" * 80)
    print("[*] NÖRO-SEMBOLİK FAZ 9 MOTORU: MESELE 106 - 125")
    print("=" * 80)

    compiler = NeuroSymbolicFikhEngine()
    completed = load_checkpoints()
    print(f"[+] Başlangıçtaki Doğrulanmış Mesele Sayısı: {len(completed)}")

    for bolum in DUGUMLER_FAZ_9:
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
    print(f"[+] FAZ 9 BAŞARIYLA TAMAMLANDI:")
    print(f"    Master Kitap: {MASTER_BOOK_PATH}")
    print(f"    Toplam Boyut: {size_kb:.2f} KB")
    print(f"    Toplam Mesele Sayısı: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
