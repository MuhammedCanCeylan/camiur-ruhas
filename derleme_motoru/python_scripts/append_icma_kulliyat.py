import os
import sys
import re

MASTER_BOOK_PATH = r"D:\fikh_kitap\Camiur_Ruhas_Nihai_Kulliyat.md"

ICMA_METNI = """

# İKİNCİ KISIM: DÖRT MEZHEBİN ÇAĞDAŞ VE KLASİK İTTİFAK KANUNNAMESİ
## (EL-MÜTTEFEK ALEYH VE'L-İCMÂ'İ'L-FUKAHÂ)

> **BAĞLAYICILIK BEYANNAMESİ:**  
> Bu kısımda yer alan hükümler, İslam Hukuku'nun dört hak mezhebi (Hanefî, Mâlikî, Şâfiî, Hanbelî) tarafından **ittifakla ve icmâen** kabul edilmiş kesin kurallardır. Bu meselelerde mezhepler arası hiçbir ihtilaf, alternatif kavil veya "lite ruhsat" bulunmaz. Bir amelin sıhhati ancak bu asılların eksiksiz tatbiki ile mümkündür.

---

### BÖLÜM I: TAHÂRET VE BEDENSEL ARINMADA KESİN İTTİFAKLAR
1. **Dört Uzvun Yıkanması (Mâide 6):** Abdestte yüzün, dirseklerle beraber kolların ve topuk kemikleriyle (ka'beyn) beraber ayakların yıkanması; başın ise en az bir kısmının ıslak elle mesh edilmesi dört mezhebin kat'i icmâıdır. Çıplak ayağa sadece mesh çekmek Ehl-i Sünnet dairesinde bâtıldır.
2. **Tabii Menfezlerden Çıkan Maddeler:** Ön ve arka yoldan (bevlü ve gāit mahalli) çıkan idrar, dışkı, yel (gaz), meni, mezi ve vedi istisnasız dört mezhepte de abdesti bozar.
3. **Meni İntikali ve Cünüplük:** Uykuda veya uyanıkken şehvetle meninin dışarı atılması durumunda bütün bedeni iğne ucu kadar kuru yer bırakmaksızın yıkamak (gusül) farz-ı ayndır.
4. **Cinsel Birleşme (İltikā-i Hıtâneyn):** Meni gelmese dahi sünnet mahallinin kavuşmasıyla hem erkeğe hem kadına gusül farz olur.
5. **Hayız ve Nifasın Bitimi:** Kadınların ay hali ve lohusalık kanaması sona erdiğinde gusletmeleri namaz ve orucun sıhhati için ittifakla farzdır.
6. **Suyun Mutlaklığı:** Hadesin (hükmî kirlilik) izalesi yalnızca yağmur, kuyu, deniz, nehir ve kar gibi yaratılış vasfını koruyan mutlak sularla mümkündür; meyve suyu, çorba veya kimyasal sıvılarla hades kalkmaz.
7. **Ağır Necasetler (Necâset-i Galîza):** İnsan idrarı, dışkısı, yaradan fışkıran kan, irin, şarap, domuzun bütün cüzleri ve usûlüne göre kesilmemiş leş hayvanın eti icmâen necistir; temas ettiği yer yıkanmadan namaz kılınamaz.
8. **Mest Üzerine Meshin Caiziyeti:** Abdestli olarak giyilen ve topukları örten deri veya dayanıklı mestler üzerine mukimin 1 gün 1 gece (24 saat), yolcunun (seferî) 3 gün 3 gece (72 saat) mesh etmesi tevatür derecesinde sünnetle sabittir.
9. **Teyemmümün Meşruiyeti:** Su bulunamadığında veya suyu kullanmak ağır hastalık/ölüm tehlikesi doğurduğunda temiz toprak cinsinden bir maddeyle teyemmüm etmek abdest ve gusül yerine geçer.
10. **İstincâ ve Temizlik:** Necaset mahallinin su veya temizleyici taş/peçete ile temizlenmesi, idrar kalıntısından (istibrâ) sakınmak kabir azabından korunmak adına dört mezhepte de emredilmiştir.

---

### BÖLÜM II: SALÂTTA (NAMAZDA) DÖRT MEZHEBİN İTTİFAK ETTİĞİ ASLÎ HÜKÜMLER
11. **Beş Vakit Farziyeti:** Sabah (2), Öğle (4), İkindi (4), Akşam (3) ve Yatsı (4) rekât farz namazları büluğa ermiş akıllı her müslümana farz-ı ayndır; inkârı küfürdür.
12. **Hadesten ve Necasetten Taharet:** Abdestsiz veya cünüp olarak ya da üzerinde namaza mâni miktarda necaset varken bilerek kılınan namaz icmâen bâtıldır.
13. **Setr-i Avret Farziyeti:** Erkeğin en az göbek ile diz kapağı arasını; kadının ise el, yüz (ve Hanefî'de ayak) hariç bütün bedenini namazda örtmesi sıhhat şartıdır.
14. **Vaktin Girmesi:** Bir namaz vakti girmeden önce eda niyetiyle kılınan namaz ittifakla geçersizdir.
15. **Kıbleye Yönelmek:** Gücü yetenin Mekke'deki Kâbe-i Muazzama cihetine yönelmesi namazın olmazsa olmaz şartıdır.
16. **İftitah Tekbiri ve Kıyam:** Namaza tekbir lafzıyla başlamak ve farzlarda gücü yetenin ayakta durması (kıyam) ittifakla rükündür.
17. **Kıraat, Rükû ve Secde:** Namazda Kur'an'dan bir miktar okumak, rükûya eğilmek ve her rekâtta alnı yere koyarak iki secde yapmak namazın sıhhat rükünleridir.
18. **Son Oturuş (Ka'de-i Ahîre):** Teşehhüd miktarı oturmak namazın tamamlanması için dört mezhepte de farzdır.
19. **Namazda Konuşma Yasağı:** Namaz esnasında kasten veya meram anlatmak kastıyla insan kelamı konuşmak ittifakla namazı bozar.
20. **Yeme-İçme ve Amel-i Kesîr:** Namaz içinde bir şey çiğneyip yutmak ve dışarıdan bakanın namazda olmadığını zannedeceği ölçüde sürekli bedenî hareketler namazı iptal eder.

---

### BÖLÜM III: SIYÂM (ORUÇ) VE RAMAZAN İTTİFAKLARI
21. **Fecr-i Sâdıktan Gurûba İmsak:** Oruç; tan yerinin ağarmasından (imsak) güneşin batışına (akşam) kadar ibadet niyetiyle yeme, içme ve cinsel ilişkiden uzak durmaktır.
22. **Kasten Yeme ve İçme:** Oruçlu olduğunu bilerek ağızdan mideye besin veya sıvı indirmek dört mezhebin icmâıyla orucu bozar ve kazayı farz kılar.
23. **Ramazan Günü Cinsel İlişki:** Oruçlu iken bilerek cinsel birleşmede bulunmak orucu bozar; hem kazayı hem de 60 gün peş peşe kefareti gerektirir.
24. **Unutarak Yiyip İçenin Orucu:** Oruçlu olduğunu tamamen unutup yiyen veya içen kimsenin orucu bozulmaz; hatırladığı anda ağzındakini çıkarıp orucuna devam eder.
25. **Niyetin Lüzumu:** Niyetsiz aç kalmak oruç sayılmaz; her gün için zihnen oruca niyetlenmek şarttır.
26. **Hayız ve Nifas Halinde Oruç Yasağı:** Âdet ve lohusalık halindeki kadının oruç tutması haram ve bâtıldır; tutamadığı günleri Ramazan'dan sonra gününe gün kaza eder.
27. **Hastalık ve Sefer Ruhsatı:** Sağlığına ciddi zarar gelecek hastanın ve meşru yolculuğa çıkan seferînin oruç tutmayıp sonradan kaza etmesi Kur'an nassıyla haktır.
28. **Kasten Kusmak:** Kendi isteğiyle parmak atarak veya zorlayarak ağız dolusu kusan kimsenin orucu bozulur.
29. **Yaşlılık ve Tedavisi Olmayan Hastalıkta Fidye:** Oruç tutmaya bedenen hiçbir zaman güç yetiremeyecek yaşlıların ve kronik hastaların her gün için bir fakiri doyuracak fidye vermesi ittifakla meşrudur.
30. **İtikâfın Meşruiyeti:** Ramazan'ın son on gününde ibadet kastıyla mescide kapanmak Peygamber Efendimiz'in müekked sünnetidir.

---

### BÖLÜM IV: ZEKÂT VE MALİ FARZLARDA KESİN İTTİFAKLAR
31. **Farziyet ve İnkârı:** Zekât İslam'ın beş temel şartından biridir; farziyetini inkâr eden dinden çıkar, vermeyen günahkâr ve gasptadır.
32. **Nisab Miktarı:** Zekâtın farz olması için temel ihtiyaçlar ve borçlar haricinde 80.18 gram altın (veya buna denk nakit para/ticaret malı) asgari zenginlik ölçüsüdür.
33. **Yıllık Zekât Oranı:** Nakit para, altın, gümüş ve ticari mallarda zekât oranı net %2.5'tir (kırkta bir).
34. **Havalân-ı Havl:** Zekâta tâbi paranın üzerinden bir kamerî yılın (354 gün) geçmesi şarttır; yıl içinde eksilip nisab altına düşmeyen mal zekâtlandırılır.
35. **Tevbe 60 Âyeti (Sarfiye Sınırı):** Zekât yalnızca Kur'an'da sayılan sınıflara (fakirler, miskinler, borçlular vb.) verilebilir; zengine veya cami/köprü/yol inşaatına zekât fonu harcanamaz.
36. **Usûl ve Fürûa Verilmez:** Kişi kendi öz anne, baba, dede, nine (usûl) ile kendi çocuk ve torunlarına (fürû) zekât veremez; onlara bakmak şahsi nafaka borcudur.
37. **Eşe Zekât Yasağı (Kocanın Eşine):** Koca, nafakasını temin etmekle mükellef olduğu nikâhlı hanımına zekât veremez.
38. **Toprak Mahsulleri (Öşür):** Yağmur suyuyla sulanan arazide onda bir (%10), masraflı motor/kuyu suyuyla sulanan arazide yirmide bir (%5) öşür verilmesi farzdır.
39. **Ticaret Mallarında Niyet:** Bir malın zekâta tâbi olması için alırken kâr amacıyla "satmak" kastıyla alınmış olması şarttır; şahsi kullanım eşyasında zekât yoktur.
40. **Sadaka-i Fıtrın Vacibiyeti:** Ramazan bayramına kavuşan ve nisab malı bulunan her mükellefin kendi ve bakmakla yükümlü olduğu çocukları adına fitre vermesi vaciptir.

---

### BÖLÜM V: HAC, UMRE VE KUTSAL MEKÂN İTTİFAKLARI
41. **Ömürde Bir Defa Farziyet:** Maddi ve bedeni gücü yeten (istitâat) her müslümana ömründe bir kez hac yapmak farzdır.
42. **Arafat Vakfesi:** Zilhicce'nin 9. günü (Arefe) zeval vaktinden bayram sabahına kadar Arafat sınırları içinde bir an dahi bulunmayan kimsenin haccı bâtıl olur; telafisi kurbanla mümkün değildir.
43. **Tavâf-ı Ziyâret (İfâda):** Kâbe'yi usûlüne uygun 7 şavt tavaf etmek haccın farz rüknüdür; yapılmadıkça hac tamamlanamaz.
44. **İhram Yasakları:** İhrama girdikten sonra cinsel ilişki, vücuttan kıl/saç koparmak, tırnak kesmek ve kara avı avlamak icmâen haramdır.
45. **Mîkāt Sınırları:** Hac veya umre kastıyla Mekke haremi dışından gelenlerin belirlenen mîkāt sınırlarını ihramsız geçmeleri yasaktır.
46. **Mescid-i Harâm ve Harem Bölgesinin Hürmeti:** Harem sınırları içindeki tabii bitkileri koparmak, ağaçları kesmek ve hayvanları ürkütmek haramdır.
47. **Tıraş ve İhramdan Çıkış:** Hac ibadetini tamamlamak için saçları tıraş etmek veya kısaltmak vaciptir.
48. **Kâbe'nin Soluna Alınarak Tavaf:** Kâbe taşları etrafında tavaf ederken Beytullah'ı sol tarafa alarak yürümek farzdır.
49. **Kurban Bayramı Günleri Kurbanı:** Hacda hedy, memlekette udhiyye kurbanının ancak bayram günlerinde kesilmesi şarttır; bayramdan önce veya sonra kesilen kurban nafile sayılır.
50. **Safâ ve Merve Sa'yi:** Safâ tepesinden başlayıp Merve'de bitmek üzere iki tepe arasında yedi şavt sa'y etmek menâsik-i hacdandır.

---

### BÖLÜM VI: NİKÂH, TALÂK VE AİLE HUKUKUNDA KESİN İTTİFAKLAR
51. **Şahitsiz Gizli Nikâhın Bâtıllığı:** İki âdil erkek veya bir erkek iki kadın şahit huzurunda icap ve kabul ile kıyılmayan gizli nikâhlar dört mezhebin icmâıyla fâsittir; zina şüphesi doğurur.
52. **Ebedi Evlilik Yasakları (Nesep):** Anne, nine, kız evlat, torun, kız kardeş, hala, teyze ve yeğenlerle evlenmek ayetle ebediyen haramdır.
53. **Süt Hısımlığı Yasağı:** Süt emen çocuk ile emziren kadın ve kadının çocukları arasında nesep gibi evlilik yasağı doğar; süt kardeşler evlenemez.
54. **Sıhriyet (Evlilik Bağıyla Doğan) Yasaklar:** Kişi hanımının annesiyle (kayınvalide) zifaf olmasa dahi ebediyen evlenemez; zifaf gerçekleşmişse hanımının kızıyla da evlenemez.
55. **İki Kız Kardeşi Aynı Anda Nikâhlamak:** İki kız kardeşi, bir kadın ile halasını veya teyzesini aynı nikâh altında birleştirmek kat'iyyen haramdır.
56. **Mehrin Hak Oluşu:** Nikâh akdi esnasında belirlensin veya belirlenmesin, kadının mehir hakkı ilahi bir haktır; koca mehri ödemekten kaçınamaz.
57. **Kocanın Nafaka Mükellefiyeti:** Evli kadının barınma, beslenme, giyim ve sağlık masraflarını karşılamak kadının şahsi serveti olsa dahi kocanın üzerine farzdır.
58. **Üç Talak Sınırı:** Bir erkeğin karısı üzerindeki boşama hakkı azami üçtür; üç talak gerçekleştikten sonra kadın başka bir erkekle sahih evlilik yapıp ayrılmadıkça eski kocasına dönemez (Hülle haramdır).
59. **Boşanan Kadının İddeti:** Hamile olmayan ve hayız gören kadının boşanma sonrası üç kurluk iddet süresince beklemesi ve bu sürede başkasıyla evlenmemesi farzdır.
60. **Vefat İddeti:** Kocası vefat eden kadının hamile değilse 4 ay 10 gün iddet beklemesi ve süslenmeyi terk etmesi (ihdâd) Kur'an nassıyla farzdır.
61. **Çocuğun Nesebinin Korunması:** Sahih veya şüpheli nikâhtan doğan çocuğun babaya nispet edilmesi farzdır; sebepsiz nesep inkârı haramdır.
62. **Veled-i Zinânın Biyolojik Babaya Mirasçılığı:** Zinadan doğan çocuk biyolojik babasına şer'an mirasçı olamaz; sadece annesine mirasçı olur.
63. **Mut'a Nikâhının Bâtıllığı:** Belirli bir süreliğine para karşılığı akdedilen geçici mut'a nikâhı Hayber fethiyle birlikte ebediyen haram kılınmıştır; bâtıldır.
64. **Gayrimüslim Erkekle Müslüman Kadın Evliliği:** Müslüman bir kadının gayrimüslim bir erkekle (Ehl-i kitap dahi olsa) evlenmesi icmâen haramdır ve akit bâtıldır.
65. **Fuhuş ve Zina Yasağı:** Nikâh bağı olmaksızın rızaya dayalı dahi olsa cinsel ilişki büyük günah ve haramdır.

---

### BÖLÜM VII: TİCARET, MODERN FİNANS VE MÜLKİYET İTTİFAKLARI
66. **Ribâ'l-Kard (Borç Faizi):** Geri ödenirken fazlalık şart koşulan her borç faizdir ve haramdır; banka faizi veya tefeci faizi fark etmez.
67. **Ribevî Mallarda Vade ve Fazlalık:** Altın, gümüş, buğday, arpa, hurma ve tuzun kendi cinsiyle takasında fazlalık ve vade icmâen faizdir.
68. **Fahiş Garar ve Kumar (Meysir):** Teslimatı imkânsız, sonu meçhul ve taraflardan birinin mutlak kaybetmesi üzerine kurulan her türlü bahis, loto, şans oyunu ve spekülasyon icmâen haramdır.
69. **Gasp Edilen Malın Tazmini:** Başkasının malını veya parasını haksız yere alan kimsenin o malı aynen, telef olmuşsa mislini veya kıymetini derhal tazmin etmesi farzdır.
70. **Mütekavvim Olmayan Malların Ticareti:** Domuz, leş, şarap, uyuşturucu ve put gibi dinen gayrimeşru nesnelerin alım-satımı, üretimi ve nakliyesi bâtıldır; geliri haramdır.
71. **Hile ve Aldatma (Tağrîr/Gışş):** Satılan malın kusurunu gizlemek, ayıbını örtmek ve müşteriyi aldatmak hadisle men edilmiştir; kazanç haramdır.
72. **Ölçü ve Tartıda Hile:** Satılan malın litresini, kilosunu veya adedini eksik vermek Mutaffifîn sûresiyle lanetlenmiş büyük haramdır.
73. **İhtikâr (Karaborsacılık):** Toplumun temel gıda maddelerini stoklayıp fiyatların suni yükselmesine sebep olmak ve darlık zamanı mal saklamak haramdır.
74. **Karşılıksız Mal Tüketimi (Bâtıl Yolla Kazanç):** Rüşvet, hırsızlık, gasp, şantaj ve dolandırıcılıkla elde edilen her kuruş kul hakkıdır ve haramdır.
75. **Şirketlerde Zararın Sermayeye Tâbi Oluşu:** Bütün sermaye ortaklıklarında zarar hisse oranına göre sermayeden düşülür; sermayesi az olana fazla zarar yüklemek bâtıldır.
76. **Mudârabe Anapara Garantisi Yasağı:** Emek-sermaye ortaklığında sermayedara anaparanın batmayacağına dair garanti verilmesi akdi faize çevirir ve iptal eder.
77. **Emanete Hıyanet Yasağı:** Vedia, kiralık mülk veya şirket kasası emanettir; emanetçinin kastı ve kusuru olmaksızın telef olan malda tazminat yoktur, kusuru varsa tam öder.
78. **Bey'u'l-Medûm (Olmayan Şeyin Satışı):** Vasıfları belirsiz ve ileride teslimi şüpheli olan mevcutsuz malların satışı nehyedilmiştir.
79. **Necş (Suni Fiyat Artırma):** Satın alma niyeti olmadığı halde malın fiyatını alıcıların gözünde yükseltmek için sahte teklif vermek haramdır.
80. **Miras Paylarının İlahi Sınır Oluşu:** Terekenin Kur'an'daki hisselere göre dağıtılması farzdır; miras bırakan vasiyetiyle vârisini mirastan mahrum edemez.

---

### BÖLÜM VIII: ÇAĞDAŞ TIP, BİYOETİK VE YAŞAM HAKKI İTTİFAKLARI
81. **Haksız Yere Cana Kıymak (Cinayet):** Masum bir insanı kasten öldürmek bütün insanlığı öldürmek gibidir; kısas veya ağır diyet gerektirir.
82. **İntiharın Haramlığı:** İnsanın kendi bedenini yok etmesi, ötenazi talep etmesi ilahi emanete hıyanettir ve kebâirdendir.
83. **Ruh Üflendikten Sonra Kürtaj Cinayeti:** Annenin kesin ölüm tehlikesi bulunmadıkça, 120 günden sonra (ruh üflendikten sonra) hangi gerekçeyle olursa olsun cenini aldırmak kasten adam öldürme hükmündedir.
84. **Canlı İnsandan Hayati Organ Nakli Yasağı:** Donörün ölümüne yol açacak şekilde tek olan kalbinin veya iki böbreğinin birden canlıyken alınması haramdır.
85. **İnsan Ticareti ve Organ Satışı:** İnsan bedeni ve parçaları satılık meta değildir; organ satışı bâtıldır, karşılıksız bağış meşrudur.
86. **Soybağını Bozan Klonlama (İnsan Kopyalama):** İnsanın genetik kopyalanması aile, nesep ve fıtrat ilkelerini yıktığı için icmâen haramdır.
87. **Taşıyıcı Annelik (Sperm/Yumurta Bankaları):** Karı-koca dışındaki üçüncü bir şahsın menisi, yumurtası veya rahmiyle çocuk sahibi olmak nesep karışıklığı sebebiyle bâtıldır ve haramdır.
88. **Zaruret Halinde Harama Ruhsat (Mecelle 21):** Açlıktan veya susuzluktan ölüm tehlikesine düşen kimsenin ölmeyecek miktarda domuz eti yemesi veya necis sıvı tüketmesi farzdır; yemeyip ölürse intihar sayılır.
89. **Tıbbi Kusur ve Tazminat:** Hekimin mesleki bilgisizliği, ağır ihmali veya hastanın rızası olmadan yaptığı hatalı müdahaleden doğan ölümlerde diyet ve tazminat ödenir.
90. **Bulaşıcı Hastalıkta Karantina:** Veba ve salgın olan yere girilmemesi, oradakilerin de dışarı çıkmaması hadisle sabit kesin kamu sağlığı kuralıdır.

---

### BÖLÜM IX: GIDA, HELALLER VE ÇEVRE HUKUKU İTTİFAKLARI
91. **Domuzun Mutlak Haramlığı:** Domuzun eti, yağı, kemiği ve derisi Kur'an'ın muhkem nassıyla haramdır; hiçbir parçası gıda olarak tüketilemez.
92. **Meyte (Leş) Yasağı:** Kesilmeden eceliyle ölen, boğulan, vurularak öldürülen veya yüksekten düşen hayvanların eti leştir, haramdır.
93. **Hamr (Alkol) ve Uyuşturucular:** Akla zarar veren, sarhoşluk ve uyuşukluk veren her türlü alkollü içecek ve madde damlasına kadar haramdır.
94. **Akıtılmış Kan (Dem-i Mesfûh):** Boğazlama esnasında damarlardan fışkıran kanın tüketilmesi haram ve necistir.
95. **Besmele ile Boğazlama ve Tezkiye:** Kara hayvanlarının etinin helal olması için nefes ve yemek boruları ile şah damarlarının kesilerek kanının akıtılması şarttır.
96. **Ehl-i Kitabın Kestiği:** Hristiyan veya Yahudilerin kendi dinî kurallarına uygun olarak boğazladıkları helal hayvanların eti Kur'an nassıyla (Mâide 5) müslümanlara helaldir.
97. **Deniz Avının Helalliği:** Denizde yaşayan tabii balık türlerinin avlanması ve tüketilmesi helaldir; boğazlanma şartı aranmaz.
98. **Zulüm ve İşkence Yasağı:** Hayvana eziyet etmek, aç bırakmak, dövüştürmek veya hedef tahtası yapmak nehyedilmiştir.
99. **Kamu Mallarını ve Doğayı Korumak:** Ortak su kaynaklarını, ormanları ve kamu alanlarını kirletmek ve tahrip etmek bütün toplumun hakkına tecavüzdür.
100. **NİHAİ İCMÂ MÜHRÜ:** Dinde farzların terki küfür veya fısk; haramların irtikâbı azap sebebidir. Dört mezhebin ittifak ettiği bu 100 esas dinin sarsılmaz omurgasıdır; ihtilaflı fürûat ancak bu omurganın üzerinde hayat bulur.
"""

def main():
    print("=" * 80)
    print("[*] KÜLLİYATA 100 İCMÂ VE İTTİFAK HÜKMÜNÜN EKLENMESİ")
    print("=" * 80)

    if not os.path.exists(MASTER_BOOK_PATH):
        print(f"[-] Hata: {MASTER_BOOK_PATH} bulunamadı!")
        return

    with open(MASTER_BOOK_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Eğer daha önce eklenmişse mükerrer yazımı önle
    if "İKİNCİ KISIM: DÖRT MEZHEBİN ÇAĞDAŞ VE KLASİK İTTİFAK KANUNNAMESİ" in content:
        print("[!] İcmâ kanunnamesi zaten mevcut. Güncelleniyor...")
        base_content = content.split("# İKİNCİ KISIM: DÖRT MEZHEBİN ÇAĞDAŞ VE KLASİK İTTİFAK KANUNNAMESİ")[0]
        final_content = base_content.strip() + "\n\n" + ICMA_METNI.strip() + "\n"
    else:
        final_content = content.strip() + "\n\n" + ICMA_METNI.strip() + "\n"

    final_content = re.sub(r'(\n---\n)+', '\n\n---\n\n', final_content)

    with open(MASTER_BOOK_PATH, "w", encoding="utf-8") as f:
        f.write(final_content)

    size_kb = os.path.getsize(MASTER_BOOK_PATH) / 1024
    print(f"[✓] İcmâ Kanunnamesi Başarıyla Mühürlendi!")
    print(f"    Dosya: {MASTER_BOOK_PATH}")
    print(f"    Yeni Dosya Boyutu: {size_kb:.2f} KB")
    print("=" * 80)

if __name__ == "__main__":
    main()
