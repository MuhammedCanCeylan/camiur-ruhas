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

DUGUMLER_FAZ_8 = [
    {
        "bolum_id": "19_kaza_derin",
        "bolum_adi": "Kitâbü'l-Kazâ ve'ş-Şehâdât (İleri İspat ve Yargı Düğümleri)",
        "dosya": "19_kaza.md",
        "meseleler": [
            (91, "Kadınların Erkek Olmaksızın Tek Başına Şahitliği (Doğum ve Ayıplar)", "شهادة النساء منفردات فيما لا يطلع عليه الرجال غالبا", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Doğum ve kadın hastalıklarında tek kadının şahitlik cevazı)",
                "ruhsat_hukum": "Erkeklerin muttali olamayacağı doğum, bekâret, emzirme ve kadınlara mahsus bedensel ayıplarda erkek şahit aranmaz; tek bir âdil kadının (veya 4 kadının) şahitliğiyle hak ve nesep sabit olur.",
                "hanefi_hukum": "Erkeklerin görmediği hallerde tek bir ebenin veya kadının şahitliği nesep ve doğum için kâfidir.",
                "safii_hukum": "Erkeklerin muttali olmadığı hususlarda 4 kadının şahitliği şarttır, tek kadın yetmez.",
                "maliki_hukum": "Doğum ve kadın hallerinde 2 kadının şahitliği tam ispat sayılır.",
                "hanbeli_hukum": "Tek bir âdil kadının şahitliği ile doğum ve süt hısımlığı sübut bulur."
            }),
            (92, "Fâsıkın (Açıktan Günah İşleyenin) Şahitliği ve Haberi", "شهادة الفاسق وقبول خبره في المعاملات والديانات", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Muâmelâtta fâsıkın şehâdet ve vekâlet cevazı)",
                "ruhsat_hukum": "Açıktan kebîre işleyen veya fıskı zâhir olan kimsenin mahkemedeki dava şahitliği cumhura göre merdut olsa da, ticari muamelelerde, elçilikte, hediyede ve vekâlette verdiği haber geçerlidir; ticarî hayat kilitlenmez.",
                "hanefi_hukum": "Kazaî hükümlerde fâsıkın şehâdeti reddedilir; ancak vekâlet, alım-satım ve haber naklinde fâsıkın beyanı muteberdir.",
                "safii_hukum": "Fâsıkın şahitliği de rivayeti de dinde ve kazada hükümsüzdür.",
                "maliki_hukum": "Adalet şartı bulunmayan kimsenin şahitliğiyle hüküm verilemez.",
                "hanbeli_hukum": "Fısk şahitliği iptal eder; ancak umum-ı belvâ olan yerlerde zarureten kabul eden tahrîcler vardır."
            }),
            (93, "Hâkimin Kendi Şahsi Bilgisine (İlmiyle) Dayanarak Hüküm Vermesi", "قضاء القاضي بعلمه في غير الحدود والدماء", {
                "ruhsat_mezhep": "Şâfiî Mezhebi ve İmam Ebû Yûsuf (Hudûd dışı davalarda ilimle hüküm)",
                "ruhsat_hukum": "Hâkim, görevi esnasında bizzat gözüyle gördüğü ve kesin bildiği mali haklarda ve borçlarda ayrıca şahit veya delil aramaksızın kendi ilmiyle hak sahibi lehine hüküm verebilir.",
                "hanefi_hukum": "Hâkim kendi yargı bölgesinde ve görevdeyken vâkıf olduğu olaylarda ilmiyle hükmedebilir; had cezalarında ilimle hükmedemez.",
                "safii_hukum": "Hâkim adalet ehli olduğu sürece hadler hariç her davada kesin ilmiyle hüküm verebilir.",
                "maliki_hukum": "Töhmetsiz dahi olsa hâkimin kendi ilmiyle hüküm vermesi kat'iyyen caiz değildir.",
                "hanbeli_hukum": "Hâkim delillere ve beyyineye tâbidir; töhmet korkusuyla şahsi ilmiyle hükmedemez."
            })
        ]
    },
    {
        "bolum_id": "20_hudud_cinayat",
        "bolum_adi": "Kitâbü'l-Hudûd ve'l-Cinâyât (Ceza ve Kısas Hukuku)",
        "dosya": "20_hudud_cinayat.md",
        "meseleler": [
            (94, "Şüphe ve Tereddüt ile Had Cezalarının Düşmesi (İdrâü'l-Hudûd)", "إدرؤوا الحدود بالشبهات وسقوط العقوبة المقدرة بالشبهة", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Cumhur)",
                "ruhsat_hukum": "'Gücünüz yettiğince had cezalarını şüphelerle düşürünüz' nassı gereği, failin fiilinde en küçük bir akit şüphesi, mülkiyet zannı veya icbar tereddüdü varsa el kesme, recm ve celde hadleri derhal düşer; ta'zîre çevrilir.",
                "hanefi_hukum": "Fiil ve mahal şüphesi haddi tamamen iskāt eder; töhmetle had tatbik edilmez.",
                "safii_hukum": "Şüphe haddi düşürür; şüphe halinde af veya ta'zîr cihetine gidilir.",
                "maliki_hukum": "Mülkiyet ve tevil şüphesi haddi düşürür.",
                "hanbeli_hukum": "En küçük meşru mazeret ve kapalılık haddin tatbikine engeldir."
            }),
            (95, "Sarhoşun İşlediği Cinayet, Akit ve Talakın Geçerliliği", "تصرفات السكران من الطلاق والبيع والجناية", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (İbn Teymiyye tahrîci), Zâhirîler ve Osman b. Affân Kavli",
                "ruhsat_hukum": "Aklını ve idrakini tamamen yitirmiş sarhoşun ağzından çıkan talak, yaptığı alım-satım ve akitler hukuken bâtıldır, vaki olmaz; irade yok hükmündedir (ancak cezai/tazminat sorumluluğu saklıdır).",
                "hanefi_hukum": "Haram yolla sarhoş olan cezalandırma kastıyla uyanık gibi kabul edilir; talakı ve akitleri geçerlidir.",
                "safii_hukum": "Kendi isteğiyle sarhoş olanın cezalandırılması için talakı geçerli sayılır.",
                "maliki_hukum": "Sarhoşun tasarrufları aleyhine nafizdir; talakı vaki olur.",
                "hanbeli_hukum": "Mezhep içi tahkike göre şuursuz sarhoşun iradesi bulunmadığından talakı ve sözleşmeleri geçersizdir."
            }),
            (96, "Kasten Adam Öldürmede Maktulün Tek Bir Vârisinin Affıyla Kısasın Düşmesi", "سقوط القصاص بعفو أحد الأولياء وانقلابه إلى الدية", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Kasten adam öldürme davasında maktulün yüzlerce velisi olsa dahi, içlerinden sadece bir tek vâris katili affeder veya diyete razı olursa kısas cezası derhal düşer; diğer vârisler sadece diyet paylarını alırlar.",
                "hanefi_hukum": "Kısas bölünemez; velilerden biri affederse kısas düşer ve katil infaz edilemez.",
                "safii_hukum": "Tek bir vârisin affı kısası iptal eder, borç diyete tahavvül eder.",
                "maliki_hukum": "Bir vârisin af beyanı katilin canını kurtarır; kısas kalkar.",
                "hanbeli_hukum": "Velilerden birinin kısastan vazgeçmesiyle katlin kısas vasfı tamamen ortadan kalkar."
            }),
            (97, "Hırsızlık Haddi (Sirkat) İçin Çalınan Malın Koruma Altında (Hırz) Olması", "اشتراط الحرز في السرقة الموجبة للحد وما يعد حرزا", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Hırz şartının daraltılması ve haddin önlenmesi)",
                "ruhsat_hukum": "Kilitli, kapalı veya muhafız gözetiminde bulunmayan (hırz dışı) açık alandan, arabadan veya sokaktan çalınan mallarda el kesme haddi uygulanmaz; mal sahibinin ihmali haddi düşürür.",
                "hanefi_hukum": "Hırzın ihlali ve malın hırz dışına bizzat çıkarılması şarttır; ortak mahallerden çalmada had düşer.",
                "safii_hukum": "Örfe göre hırz sayılmayan yerden yapılan hırsızlık had gerektirmez.",
                "maliki_hukum": "Hırzın kamil olması şarttır; şüphe halinde had uygulanmaz.",
                "hanbeli_hukum": "Her malın kendi cinsine uygun hırzda olması gerekir; aksi halde sirkat haddi tatbik edilmez."
            }),
            (98, "İffete İftira (Kazf) Suçunda Mağdurun Affının Cezayı Düşürmesi", "عفو المقذوف عن القاذف هل يسقط حد القذف", {
                "ruhsat_mezhep": "Şâfiî ve Hanbelî Mezhepleri (Kazf haddinin kul hakkı ağırlıklı olması)",
                "ruhsat_hukum": "İffetine iftira atılan kimse mahkemede veya infazdan önce iftiracıyı affederse 80 celde kazf haddi derhal düşer; ceza tatbik edilmez.",
                "hanefi_hukum": "Kazf haddi Allah hakkıdır; dava açıldıktan sonra mağdur affetse dahi had cezası düşmez.",
                "safii_hukum": "Kazf cezası hâlis kul hakkıdır; mağdur affettiği anda had tamamen sakıt olur.",
                "maliki_hukum": "Dava kadıya intikal etmeden af caizdir; kadıya ulaştıktan sonra af haddi düşürmez.",
                "hanbeli_hukum": "Mağdurun hakkı galip olduğundan af ile had cezası ortadan kalkar."
            })
        ]
    },
    {
        "bolum_id": "21_sirketler_vakif",
        "bolum_adi": "Kitâbü'ş-Şirke ve'l-Vakf (Şirketler, Finans ve Vakıf Hukuku)",
        "dosya": "21_sirketler_vakif.md",
        "meseleler": [
            (99, "Emek-Sermaye Ortaklığında (Mudârabe) Sermayedara Sabit Kâr Garantisi", "ضمان رأس المال وتحديد ربح مقطوع في المضاربة", {
                "ruhsat_mezhep": "Ruhsat Yoktur (Dört Mezhebin İcmâıyla Bâtıldır)",
                "ruhsat_hukum": "Mudârabe veya yatırım ortaklığında sermaye sahibine aylık sabit kâr garantisi vermek veya anaparanın batmayacağını taahhüt etmek 4 mezhebin ittifakıyla haram ve faizdir; kâr oransal (%) olmalı, zarar sermayeden karşılanmalıdır.",
                "hanefi_hukum": "Maktu kâr tayini veya anapara garantisi akdi fâsid kılar, muameleyi faize çevirir.",
                "safii_hukum": "Kâr oranla belirlenmelidir; maktu meblağ veya garanti mudârabeyi iptal eder.",
                "maliki_hukum": "Zarar ve kâr ortaklığı ilkesi çiğnenemez; garanti şartı bâtıldır.",
                "hanbeli_hukum": "İcmâ ile men edilmiştir; anaparaya garanti verilen işlem borç ve ribâ sayılır."
            }),
            (100, "Şirket Ortaklığında Kâr Payının Sermaye Oranından Farklı Belirlenmesi", "تفاضل الشركاء في الربح مع تساوي رؤوس الأموال", {
                "ruhsat_mezhep": "Hanefî ve Hanbelî Mezhepleri (Emek ve tecrübe karşılığı serbest kâr oranı)",
                "ruhsat_hukum": "Sermayeleri eşit olan ortaklar, taraflardan birinin iş tecrübesi, itibarı veya yoğun emeği sebebiyle kârı %70 - %30 gibi farklı oranlarda paylaşmayı şart koşabilirler; geçerlidir.",
                "hanefi_hukum": "Kâr ortakların rızasıyla diledikleri oranda bölüşülebilir; sermaye oranına eşitlik şart değildir.",
                "safii_hukum": "Kâr sermayenin semeresidir; kâr oranı sermaye oranına birebir eşit olmak zorundadır, aksi fâsittir.",
                "maliki_hukum": "Kâr ve zarar sermaye nispetinde olmalıdır; fazlalık şartı akdi bozar.",
                "hanbeli_hukum": "Kâr akitteki şartlara bağlıdır; emeği üstün olanın fazla pay alması mubahtır."
            }),
            (101, "Vakıf Mallarının Amacı Dışında Satılması veya Değiştirilmesi (İstibdâl)", "استبدال الوقف وبيعه عند تعطل منافعه أو للمصلحة الراجحة", {
                "ruhsat_mezhep": "Hanefî Mezhebi (İmam Ebû Yûsuf) ve Hanbelî Tahrîci",
                "ruhsat_hukum": "Kullanılamaz hale gelen, geliri masrafını karşılamayan veya daha kârlı bir mülkle değiştirilmesinde açık kamu maslahatı bulunan vakıf gayrimenkulleri hâkim izniyle satılıp yerine yenisi alınabilir (istibdâl).",
                "hanefi_hukum": "Vâkıf şart koşmasa dahi menfaati tükenen mülk daha hayırlısıyla istibdâl edilebilir.",
                "safii_hukum": "Vakıf malı asla satılamaz, devredilemez ve istibdâl edilemez; harabe kalsa da vakıf kalır.",
                "maliki_hukum": "Taşınmaz vakıflarda istibdâl caiz değildir; sadece cami genişletme gibi zaruretlerde istisna tanınır.",
                "hanbeli_hukum": "Menfaati tamamen biten vakfın satılıp bedeliyle benzer bir vakıf kurulması meşrudur."
            }),
            (102, "Müslüman ile Gayrimüslim Vatandaşın Kan Parasının (Diyet) Eşitliği", "دية الذمي والمعاهد ومساواتها بدية المسلم", {
                "ruhsat_mezhep": "Hanefî Mezhebi (İnsan hayatının eşitliği ilkesi)",
                "ruhsat_hukum": "İslam yurdunda vatandaş veya izinli (muâhid) olarak yaşayan gayrimüslimin haksız yere öldürülmesi halinde ödenecek diyet miktarı tam bir müslümanın diyetiyle (100 deve / 1000 dinar) birebir aynıdır; can dokunulmazlığı eşittir.",
                "hanefi_hukum": "Dârülislâmda yaşayan gayrimüslimin kanı müslümanın kanı gibidir; diyeti tam olarak ödenir.",
                "safii_hukum": "Gayrimüslimin diyeti müslümanın diyetinin üçte biridir (1/3).",
                "maliki_hukum": "Diyeti müslümanın diyetinin yarısıdır (1/2).",
                "hanbeli_hukum": "Kitâbî olanın diyeti müslümanın diyetinin yarısı kadardır."
            }),
            (103, "Dârülharpte / Gayrimüslim Ülkede Gayrimüslimlerle Yapılan Fasit Akitler", "إجراء العقود الفاسدة والتعامل المالي في دار الحرب", {
                "ruhsat_mezhep": "Hanefî Mezhebi (İmam Ebû Hanîfe ve İmam Muhammed)",
                "ruhsat_hukum": "İslam hâkimiyeti altında olmayan gayrimüslim ülkelerde (Dârülharp), müslüman bir kimsenin oradaki gayrimüslimlerin rızasıyla onlardan faiz veya kâr elde etmesi dindaşının aleyhine olmamak kaydıyla tahrimen mekruh olsa da akden geçerlidir (fakat İslam ülkesinde mutlak haramdır).",
                "hanefi_hukum": "Dârülharpte müslüman ile harbî arasında faiz ve fasit muamele tahakkuk etmez; malı rızayla almak caizdir.",
                "safii_hukum": "Haram olan faiz ve fasit akit dünyanın her yerinde aynıdır; dâr ayrımı kabul edilmez.",
                "maliki_hukum": "İslam hükümleri şahsîdir; dârülharpte de faiz kat'iyyen haramdır.",
                "hanbeli_hukum": "Müslüman nerede olursa olsun şeriatın yasaklarına tâbidir; faiz hiçbir yerde caiz olmaz."
            }),
            (104, "Ölüm Tehdidi ve İkrah Altında Yapılan Tasarrufların Geçersizliği", "أثر الإكراه الملجئ على العقود والطلاق والإقرار", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî)",
                "ruhsat_hukum": "Öldürülme, ağır yaralanma veya hapsedilme tehdidi (ikrah-ı mülcî) altında zorla yaptırılan nikâh, talak, satış akitleri ve borç ikrarları hukuken kökten bâtıldır; fail hiçbir şekilde sorumlu tutulamaz.",
                "hanefi_hukum": "İkrah altında yapılan talak ve nikâh geçerli sayılır fakat fâsittir; satış ise fâsittir.",
                "safii_hukum": "'Ümmetimden hata, unutma ve zorlandıkları şeyler kaldırıldı' hadisi gereği ikrah altındaki tüm tasarruflar bâtıldır.",
                "maliki_hukum": "Baskı ve tehdit altındaki irade beyanları hükümsüzdür, talak vaki olmaz.",
                "hanbeli_hukum": "İkrah altındaki kişinin sözü ve akdi geçersizdir; hiçbir hukuki netice doğurmaz."
            }),
            (105, "Yapılan Hibe ve Bağıştan Mahkeme Yoluyla Dönmek (Rücû' bi'l-Hibe)", "الرجوع في الهبة والصدقة لغير الوالد", {
                "ruhsat_mezhep": "Cumhur Fukahâsı (Şâfiî, Mâlikî, Hanbelî - Hukuki istikrar ve rücû yasağı)",
                "ruhsat_hukum": "Bir kimseye mülkiyeti teslim edilerek yapılan bağıştan (hibe) sonradan vazgeçip malı geri istemek haramdır ve hukuken bâtıldır; bağışlanan mal geri alınamaz (yalnızca babanın evladına yaptığı bağış hariçtir).",
                "hanefi_hukum": "Akraba dışındakilere yapılan hibeden mahkeme kararıyla dönmek tahrîmen mekruh olmakla birlikte mümkündür.",
                "safii_hukum": "Kusmuğunu yutan köpek gibi olmamak adına babanın evladına hibesi hariç hiçbir bağıştan dönülemez.",
                "maliki_hukum": "Teslim edilen hibeden dönmek caiz değildir; mülkiyet kesinleşmiştir.",
                "hanbeli_hukum": "Hasedi önlemek ve nassın açık nehyi gereğince hibeden rücû haramdır ve geçersizdir."
            })
        ]
    }
]

def main():
    print("=" * 80)
    print("[*] NÖRO-SEMBOLİK FAZ 8 MOTORU: MESELE 091 - 105")
    print("=" * 80)

    compiler = NeuroSymbolicFikhEngine()
    completed = load_checkpoints()
    print(f"[+] Başlangıçtaki Doğrulanmış Mesele Sayısı: {len(completed)}")

    for bolum in DUGUMLER_FAZ_8:
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
        ("21_sirketler_vakif.md", "KİTÂBÜ'Ş-ŞİRKE VE'L-VAKF (ŞİRKETLER, FİNANS VE VAKIF HUKUKU)")
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
    print(f"[+] FAZ 8 BAŞARIYLA TAMAMLANDI:")
    print(f"    Master Kitap: {MASTER_BOOK_PATH}")
    print(f"    Toplam Boyut: {size_kb:.2f} KB")
    print(f"    Toplam Mesele Sayısı: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
