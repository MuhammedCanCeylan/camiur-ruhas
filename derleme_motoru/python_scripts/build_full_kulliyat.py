import os
import sys
import json
import time
import re
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

# 8 Ana Bab ve Kanonik Meseleler Listesi
KULLIYAT_PLANI = [
    {
        "bolum_id": "01_taharet",
        "bolum_adi": "Kitâbü't-Tahâret (Temizlik ve Abdest)",
        "dosya": "01_taharet.md",
        "meseleler": [
            (1, "Abdestte Niyetin Farziyeti ve Unutulması", "اشتراط النية في صحة الوضوء والطهارة", {
                "ruhsat_mezhep": "Hanefî Mezhebi",
                "ruhsat_hukum": "Abdestte niyet farz veya sıhhat şartı değildir, sünnettir. Niyetsiz alınan abdest sahihtir.",
                "hanefi_hukum": "Sünnet / Müstehap (Abdestin sıhhat şartı değildir; su bizâtihi temizleyicidir).",
                "safii_hukum": "Farz / Rükün (Niyetsiz abdest geçersizdir; hadesteki kirlilik ancak niyetle kalkar).",
                "maliki_hukum": "Farz / Sıhhat Şartı (Niyet ibadetin ayrılmaz parçasıdır).",
                "hanbeli_hukum": "Farz / Şart (Namaz gibi müstakil niyete muhtaçtır)."
            }),
            (2, "Abdestte Tertip ve Muvâlâtın Terki", "الترتيب والموالاة في الوضوء", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Tertip ve Muvâlât için)",
                "ruhsat_hukum": "Uzuvları sırasız yıkamak veya araya fasıla verip uzuvlar kuruduktan sonra devam etmek abdesti bozmaz.",
                "hanefi_hukum": "Tertip ve muvâlât sünnettir, terki abdesti iptal etmez.",
                "safii_hukum": "Tertip farzdır (sırasız abdest bâtıldır), muvâlât sünnettir.",
                "maliki_hukum": "Muvâlât farzdır (kuruyacak kadar beklemek abdesti bozar), tertip sünnettir.",
                "hanbeli_hukum": "Hem tertip hem de muvâlât abdestin farzlarındandır."
            }),
            (3, "Karşı Cinsle Temasın Abdesti Bozması", "لمس المرأة هل ينقض الوضوء", {
                "ruhsat_mezhep": "Hanefî Mezhebi",
                "ruhsat_hukum": "Karşı cinse çıplak tenle dokunmak, temas fahiş mübâşeret derecesinde olmadıkça abdesti bozmaz.",
                "hanefi_hukum": "Mutlak olarak bozmaz (Ayet-i kerimedeki 'lems' cima manasındadır).",
                "safii_hukum": "Aralarında evlilik caiz olan yabancı kadına temas mutlak olarak abdesti bozar.",
                "maliki_hukum": "Dokunan veya dokunulan taraf lezzet/şehvet duymuşsa bozar; mutlak temasta şehvet yoksa bozmaz.",
                "hanbeli_hukum": "Temas şehvet kastıyla veya şehvet duyularak yapılmışsa bozar; gayriihtiyari temasta bozmaz."
            }),
            (4, "Vücuttan Kan veya İrin Çıkması", "خروج الدم والقيء هل ينقض الوضوء", {
                "ruhsat_mezhep": "Şâfiî ve Mâlikî Mezhepleri",
                "ruhsat_hukum": "Ön ve arka avret dışındaki bir yerden kan, irin veya kusuntu çıkması ne kadar çok olursa olsun abdesti bozmaz.",
                "hanefi_hukum": "Yaradan çıkıp uzvun dışına taşan kan ve ağız dolusu kusuntu abdesti bozar.",
                "safii_hukum": "İki yol (sebilayn) dışından çıkan hiçbir necis madde abdesti bozmaz.",
                "maliki_hukum": "Ön ve arka haricindeki bedenden çıkan kan ve sıvılar abdesti mutlak surette bozmaz.",
                "hanbeli_hukum": "Bedenin herhangi bir yerinden çıkan kan veya kusuntu 'fahiş' miktarda ise abdesti bozar."
            }),
            (5, "Mestler Üzerine Meshte Süre ve Delik Sınırı", "المسح على الخفين والجوربين والخروق", {
                "ruhsat_mezhep": "Mâlikî Mezhebi (Süre sınırı olmaması) ve Hanefî (Geniş delik ruhsatı)",
                "ruhsat_hukum": "Mâlikî'de mukim veya seferi için mestte belirli bir süre tahdidi yoktur; Hanefî'de ise 3 küçük parmak miktarı yırtık aşılmadıkça mesh sahihtir.",
                "hanefi_hukum": "Mukime 1 gün 1 gece, yolcuya 3 gün 3 gece. 3 parmak genişliğinde delik bulunursa mesh câiz olmaz.",
                "safii_hukum": "Mukime 24 saat, yolcuya 72 saat. En küçük yırtıktan ten görünürse mesh bâtıldır.",
                "maliki_hukum": "Cünüplük olmadıkça veya mest ayaktan çıkarılmadıkça mestte gün/saat süre tahdidi yoktur.",
                "hanbeli_hukum": "Süre 24/72 saattir; ayaktan bağımsız durabilen kalın çoraplara da mesh câizdir."
            }),
            (6, "Büyük Abdest Temizliğinde (İstincâ) Su Kullanma Mecburiyeti", "الاستنجاء بالاحجار والمناديل والماء", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Cevaz) - Hanefî/Şâfiî Ruhsatı",
                "ruhsat_hukum": "Necâset mahrecin dışına taşmadığı sürece sadece tuvalet kâğıdı veya taşla kurulamak yeterlidir, su kullanmak farz değildir.",
                "hanefi_hukum": "Su ile yıkamak sünnettir; kuru temizleme ile necaset giderilirse namaz sahihtir.",
                "safii_hukum": "En az 3 silme ile mahrecin temizlenmesi kâfidir, su şart değildir.",
                "maliki_hukum": "Taş veya kâğıt ile necasetin izalesi mutlak olarak yeterlidir.",
                "hanbeli_hukum": "Temizleyici nesnelerle en az 3 defa silinmesiyle taharet tamamlanır."
            })
        ]
    },
    {
        "bolum_id": "02_salat",
        "bolum_adi": "Kitâbü's-Salât (Namaz ve Vakitler)",
        "dosya": "02_salat.md",
        "meseleler": [
            (7, "Yolculuk ve Meşakkat Anında İki Namazın Cem' Edilmesi", "الجمع بين الصلاتين في السفر والمطر والحاجة", {
                "ruhsat_mezhep": "Şâfiî, Mâlikî ve Hanbelî Mezhepleri",
                "ruhsat_hukum": "Meşru seferde, şiddetli yağmur veya meşakkatte Öğle-İkindi ve Akşam-Yatsı cem'-i takdîm veya cem'-i te'hîr ile birleştirilebilir.",
                "hanefi_hukum": "Hac (Arafat-Müzdelife) hariç cem' câiz değildir; namazları vaktinden çıkarmak büyük günahtır.",
                "safii_hukum": "Seferde ve şiddetli yağmurda cem'-i takdim ve tehîr meşrudur.",
                "maliki_hukum": "Sefer, yağmur ve çamur meşakkatinde cem' caizdir.",
                "hanbeli_hukum": "Sefer, hastalık, yağmur ve meşakkat veren mazeretlerde cem' caizdir (en geniş cem' ruhsatı Hanbelî'dedir)."
            }),
            (8, "Namazda İftitah Tekbiri Dışında Elleri Kaldırmak (Ref'u'l-Yedeyn)", "رفع اليدين في الصلاة عند الركوع والرفع منه", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Namazı en sade/hafif kılan amel)",
                "ruhsat_hukum": "Namazda eller yalnızca başlarken iftitah tekbirinde kaldırılır; rükûa giderken ve doğrulurken el kaldırmamak sünnettir.",
                "hanefi_hukum": "İftitah haricinde eller kaldırılmaz; rükûda kaldırmak sünnete muhaliftir.",
                "safii_hukum": "İftitahta, rükûa inerken, rükûdan kalkarken elleri kaldırmak müekked sünnettir.",
                "maliki_hukum": "Meşhur kavle göre yalnızca iftitah tekbirinde kaldırılır, rükûda kaldırılmaz.",
                "hanbeli_hukum": "İftitah, rükûa iniş ve kalkışta elleri kaldırmak sünnettir."
            }),
            (9, "İmama Uyan Kişinin Fatiha Okuma Mecburiyeti", "قراءة الفاتحة للمأموم خلف الإمام", {
                "ruhsat_mezhep": "Hanefî Mezhebi",
                "ruhsat_hukum": "Cemaatle kılınan namazda imama uyan kişinin sesli veya gizli namazda Fatiha okuması gerekmez; imamın kıraati cemaatin kıraatidir.",
                "hanefi_hukum": "İmama uyan kişinin kıraat yapması tahrîmen mekruhtur; sükût farzdır.",
                "safii_hukum": "Fatiha her rekâtta cemaate de farzdır; imama uyan mutlaka okur.",
                "maliki_hukum": "Gizli namazda okumak müstehaptır; sesli namazda dinlemek farzdır, okunmaz.",
                "hanbeli_hukum": "İmamın sesli okuduğu rekâtlarda dinler, gizli okuduğunda cemaat okur."
            }),
            (10, "Namazı Bozan Amel-i Kesîr (Fazla Hareket) Sınırı", "العمل الكثير المبطل للصلاة وحركاته", {
                "ruhsat_mezhep": "Mâlikî ve Hanbelî Mezhepleri",
                "ruhsat_hukum": "Namaz kılanın yönünü kıbleden tamamen çevirmeyen, peş peşe aşırıya kaçmayan ihtiyaç hareketleri namazı iptal etmez.",
                "hanefi_hukum": "Dışarıdan bakan birinin kesinlikle namazda olmadığını düşüneceği hareketler amel-i kesîrdir ve namazı bozar.",
                "safii_hukum": "Peş peşe yapılan 3 büyük hareket (adım, kaşınma vb.) namazı derhal bozar.",
                "maliki_hukum": "Örfte aşırı sayılmayan veya ihtiyaç sebebiyle yapılan hareketler namazı bozmaz.",
                "hanbeli_hukum": "Namazın heyetini tamamen bozmayan ve zarurete dayalı hareketler namazı iptal etmez."
            })
        ]
    },
    {
        "bolum_id": "03_siyam",
        "bolum_adi": "Kitâbü's-Sıyâm (Oruç ve İmsak)",
        "dosya": "03_siyam.md",
        "meseleler": [
            (11, "Unutarak Yiyip İçenin Orucunun Durumu", "أكل الصائم وشربه ناسيا هل يفطر", {
                "ruhsat_mezhep": "Hanefî, Şâfiî ve Hanbelî İttifakı",
                "ruhsat_hukum": "Unutarak ne kadar çok yenilip içilirse içilsin oruç bozulmaz, kaza veya keffâret gerekmez.",
                "hanefi_hukum": "Oruç bozulmaz, hatırladığı anda yemeyi bırakır.",
                "safii_hukum": "Oruç bozulmaz, hadis-i şerifin açık hükmüyle sahihtir.",
                "maliki_hukum": "Farz oruçta unutarak yemek orucu bozar, gününe gün kaza gerekir (keffaret gerekmez).",
                "hanbeli_hukum": "Oruç bozulmaz, hüküm kat'îdir."
            }),
            (12, "Göz Damlası, İğne ve Kan Aldırmanın Oruca Etkisi", "قطرة العين والحقنة والحجامة للصائم", {
                "ruhsat_mezhep": "Şâfiî (Göz damlası) ve Hanefî/Şâfiî/Mâlikî (Hacamat)",
                "ruhsat_hukum": "Göz damlası ve besleyici olmayan kas/damar enjeksiyonları mideye doğal yoldan ulaşmadığı için orucu bozmaz; hacamat orucu iptal etmez.",
                "hanefi_hukum": "Boğaza veya mideye doğrudan açılan tabii menfezlerden girmeyen maddeler orucu bozmaz. Hacamat orucu bozmaz.",
                "safii_hukum": "Göz tabii menfez değildir, damla orucu bozmaz. Kan aldırmak orucu bozmaz.",
                "maliki_hukum": "Tadı boğazda hissedilen damlalar bozar. Hacamat mekruhtur ama bozmaz.",
                "hanbeli_hukum": "Hacamat yapanın da yaptıranın da orucu bozulur (hadisin zâhirine göre)."
            }),
            (13, "Oruç Keffâretinin Sebepleri (Sadece Cima mı, Yeme-İçme mi?)", "موجب كفارة الصيام بين الجماع والأكل عمدا", {
                "ruhsat_mezhep": "Şâfiî ve Hanbelî Mezhepleri (Keffâretin daraltılması)",
                "ruhsat_hukum": "Ramazan ayında bilerek yemek ve içmek yalnızca kazayı gerektirir; 60 gün keffâret sadece bilerek cima etmekle vacip olur.",
                "hanefi_hukum": "Kasten meşru mazeretsiz yemek, içmek ve cima etmek hem kaza hem 60 gün keffaret gerektirir.",
                "safii_hukum": "Keffâret yalnızca bilerek yapılan cinsel ilişkiye mahsustur; bilerek yiyip içene sadece kaza gerekir.",
                "maliki_hukum": "Ramazan hürmetini kasten ihlal eden her yeme-içme ve cima keffâret gerektirir.",
                "hanbeli_hukum": "Keffâret yalnızca Ramazan'da gündüz yapılan cima sebebiyle terettüp eder."
            })
        ]
    },
    {
        "bolum_id": "04_buyu",
        "bolum_adi": "Kitâbü'l-Büyû' (Ticaret ve Muâmelât)",
        "dosya": "04_buyu.md",
        "meseleler": [
            (14, "Veresiye Verilen Borcun Başka Bir Borçla Takası (Kâli' bi'l-Kâli')", "نهى عن بيع الكالئ بالكالئ بيع الدين بالدين", {
                "ruhsat_mezhep": "Ruhsat Yoktur (İcmâen Bâtıldır)",
                "ruhsat_hukum": "Peşin bir bedel ödenmeksizin vadeli borcun borçla takası 4 mezhebin icmâıyla haram ve bâtıldır; ruhsatı yoktur.",
                "hanefi_hukum": "Bâtıldır ve faiz şüphesi taşır.",
                "safii_hukum": "Kâli' bi'l-kâli' satışı nehyedilen garar ve ribâ akitlerindendir, bâtıldır.",
                "maliki_hukum": "Din bi'd-deyn akdi icmâ ile men edilmiştir, fâsittir.",
                "hanbeli_hukum": "Hadis-i şerifin açık nehyi ve icmâ gereği haramdır."
            }),
            (15, "Vadeli Alıp Peşin Satmak (Bey'u'l-Îne ve Hile-i Şer'iyye)", "بيع العينة وحكم التحايل على الربا", {
                "ruhsat_mezhep": "Şâfiî Mezhebi (Zâhirî Akit Geçerliliği)",
                "ruhsat_hukum": "Akit esnasında şart koşulmadığı ve iki bağımsız akit yapıldığı sürece, tarafların bâtınî niyeti nakit temini olsa da zâhirî akit geçerlidir.",
                "hanefi_hukum": "Fâsittir ve tahrîmen mekruhtur; ribâya vesile kılınması men edilmiştir.",
                "safii_hukum": "Akit zâhirî rükünleri taşıyorsa geçerlidir; bâtınî niyetler Allah'a aittir.",
                "maliki_hukum": "Sedd-i zerâi' kaidesi gereğince haram ve bâtıldır.",
                "hanbeli_hukum": "Hile-i ribâ sayıldığı için haram ve fâsittir."
            }),
            (16, "Siparişe Dayalı Üretim ve Satış (İstisnâ' ve Selem Akdi)", "عقد الاستصناع والسلم في المعاملات", {
                "ruhsat_mezhep": "Hanefî Mezhebi (İstisnâ' akdinin kıyasa aykırı istihsanen meşruiyeti)",
                "ruhsat_hukum": "Henüz üretilmemiş bir malın vasıfları belirlenerek sipariş edilmesi ve bedelin peşin veya vadeli ödenmesi istihsânen sahihtir.",
                "hanefi_hukum": "İstisnâ' akdi örf ve teamül gereğince caizdir, bedelin mecliste peşin verilmesi şart değildir.",
                "safii_hukum": "Madumun satışı caiz değildir; ancak selem şartlarına (mecliste peşin bedel) tam uyulursa selem olarak caiz olur.",
                "maliki_hukum": "Sanatkârla yapılan sipariş akdi belirli teslim süresiyle caizdir.",
                "hanbeli_hukum": "Kabz şartlarına ve malın taayyününe göre istisna' veya selem olarak cevaz verilir."
            })
        ]
    }
]

def main():
    print("=" * 80)
    print("[*] NİHAİ KÜLLİYAT TOPLU ÜRETİM VE CHECKPOINT MOTORU")
    print("=" * 80)

    compiler = ProductionFikhCompiler()
    completed = load_checkpoints()
    print(f"[+] Mevcut tamamlanmış mesele sayısı: {len(completed)}")

    all_compiled_pages = []

    for bolum in KULLIYAT_PLANI:
        bolum_adi = bolum["bolum_adi"]
        dosya_adi = bolum["dosya"]
        dosya_yolu = os.path.join(CHAPTERS_DIR, dosya_adi)

        print(f"\n[+] BÖLÜM DENETLENİYOR: {bolum_adi}")
        chapter_pages = []

        for m_id, m_baslik, m_sorgu, m_canon in bolum["meseleler"]:
            key = f"{bolum['bolum_id']}_{m_id:03d}"
            
            if key in completed:
                print(f"    [>] Mesele {m_id:03d} atlandı (Daha önce derlenmiş).")
                continue

            print(f"    [*] Mesele {m_id:03d} İşleniyor (BGE-M3 + RRF + Qwen2.5-7B): {m_baslik}...")
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
            with open(dosya_yolu, "a", encoding="utf-8") as bf:
                for p in chapter_pages:
                    bf.write(p + "\n\n")

    # Master Kitap Dosyasını Fihristle Birleştirme
    print("\n[*] Master Külliyat Birleştiriliyor...")
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
    toc_lines = []
    body_lines = []

    for b in KULLIYAT_PLANI:
        fpath = os.path.join(CHAPTERS_DIR, b["dosya"])
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            text = f.read()

        toc_lines.append(f"\n#### {b['bolum_adi'].upper()}")
        issues = re.findall(r"## MESELE (\d+):\s*(.+)", text)
        for num, name in issues:
            toc_lines.append(f"- **Mesele {num}:** {name}")

        body_lines.append(text)

    master_text = mukaddime + "\n".join(toc_lines) + "\n\n---\n\n" + "\n\n".join(body_lines)
    with open(MASTER_BOOK_PATH, "w", encoding="utf-8") as mf:
        mf.write(master_text)

    size_kb = os.path.getsize(MASTER_BOOK_PATH) / 1024
    print("=" * 80)
    print(f"[+] NİHAİ KİTAP GÜNCELLENDİ: {MASTER_BOOK_PATH} ({size_kb:.2f} KB)")
    print(f"[+] Toplam İşlenen Mesele: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()


