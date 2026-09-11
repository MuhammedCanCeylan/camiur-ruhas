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

FAZ_2_PLANI = [
    {
        "bolum_id": "05_zekat",
        "bolum_adi": "Kitâbü'z-Zekât ve'l-Fıtr (Zekât ve Sadaka-i Fıtır)",
        "dosya": "05_zekat.md",
        "meseleler": [
            (17, "Kadının Kullandığı Ziynet Eşyasının (Altın/Gümüş) Zekâtı", "زكاة الحلي المباح للمرأة معد للاستعمال", {
                "ruhsat_mezhep": "Şâfiî, Mâlikî ve Hanbelî Mezhepleri",
                "ruhsat_hukum": "Kadının örfe uygun olarak şahsi süslenme amacıyla taktığı ve biriktirmediği ziynet altın ve mücevherlerinden zekât verilmez.",
                "hanefi_hukum": "Nisap miktarını aşan her türlü altın ve gümüş, kullanımda olsa dahi zekâta tâbidir.",
                "safii_hukum": "Mubah ve mutad kullanım için olan ziynet eşyasından zekât gerekmez.",
                "maliki_hukum": "Kullanım kastıyla bulundurulan ziynetler zekâttan muaftır.",
                "hanbeli_hukum": "Kadının mubah kullanımında olan ziynet eşyasında zekât yoktur."
            }),
            (18, "Vadesi Gelmiş veya Gelecek Borçların Zekât Malından Düşülmesi", "إسقاط الدين من مال الزكاة هل يمنع وجوبها", {
                "ruhsat_mezhep": "Şâfiî Mezhebi (Zekâtın düşmemesi/fakir lehine) ve Hanefî (Mükellef lehine en hafif ruhsat)",
                "ruhsat_hukum": "Hanefî mezhebine göre eldeki nakit ve ticaret malından mevcut borçlar düşülür; kalan miktar nisabın altına inerse zekât düşer.",
                "hanefi_hukum": "Borç, zekâta tâbi bâtınî mallardan düşülür; borcu karşılayan miktarın zekâtı verilmez.",
                "safii_hukum": "Borç zekâtın vücûbuna mâni değildir; eldeki nisap miktarı malın zekâtı borca bakılmaksızın tam verilir.",
                "maliki_hukum": "Yalnızca nakit paralarda borç düşülür, ticaret mallarında borç düşülmez.",
                "hanbeli_hukum": "Zâhir ve bâtın her türlü malda mevcut borçlar zekât matrahından tenzil edilir."
            }),
            (19, "Sadaka-i Fıtrın ve Zekâtın Nakit Para Olarak Ödenmesi", "إخراج القيمة في الزكاة والفطرة بالدراهم والدنانير", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Kıymet intikali ruhsatı)",
                "ruhsat_hukum": "Fitre ve zekâtta buğday, arpa, hurma gibi aynî mallar yerine bunların rayiç piyasa bedeli nakit para olarak ödenebilir; fakir için daha menfaatli ve caizdir.",
                "hanefi_hukum": "Zekât ve fıtır sadakasında aslolan kıymettir; nakden ödeme mutlak caizdir.",
                "safii_hukum": "Nasslarda sayılan cinslerin bizâtihi aynının verilmesi şarttır; kıymet/nakit ödeme geçersizdir.",
                "maliki_hukum": "Aynî ödeme esastır, zaruret olmaksızın nakden ödeme caiz görülmez.",
                "hanbeli_hukum": "Aslolan malın cinsinden vermektir; meşru maslahat veya ihtiyaç olmadıkça kıymet caiz değildir."
            })
        ]
    },
    {
        "bolum_id": "06_hac",
        "bolum_adi": "Kitâbü'l-Hac ve'l-Umre (Hac ve Umre Hükümleri)",
        "dosya": "06_hac.md",
        "meseleler": [
            (20, "Tavâf Esnasında Abdestin Şart Olup Olmaması", "الطهارة من الحدث لصحة الطواف بالبيت", {
                "ruhsat_mezhep": "Hanefî Mezhebi (Tavâfta abdestsizliğin geçerliliği ve ceza bedeli)",
                "ruhsat_hukum": "Tavâf-ı ifâda ve kudûmda abdestli olmak sıhhat şartı değil, vaciptir; abdestsiz yapılan tavâf geçerlidir ancak dem (koyun kurbanı) veya sadaka gerekir.",
                "hanefi_hukum": "Tavâfta hadesten tahâret vaciptir; abdestsiz tavâf bâtıl olmaz, kurban veya iade ile telafi edilir.",
                "safii_hukum": "Tavâf namaz gibidir; abdest tavâfın sıhhat şartıdır, abdestsiz tavâf kesinlikle bâtıldır.",
                "maliki_hukum": "Hadesten ve necâsetten tahâret tavâfın sıhhat şartıdır.",
                "hanbeli_hukum": "Tavâfın geçerli olması için abdest şarttır; abdestsiz dönülen şavtlar geçersizdir."
            }),
            (21, "Müzdelife Vakfesinin Terki ve İzdiham Sebebiyle Gece Yarısı Mina'ya Geçmek", "المبيت بمزدلفة والترخيص للضعفة والنساء بعد نصف الليل", {
                "ruhsat_mezhep": "Şâfiî ve Hanbelî Mezhepleri (Gece yarısından sonra intikal ruhsatı)",
                "ruhsat_hukum": "Kadınlar, hastalar, yaşlılar ve refakatçileri gece yarısından sonra Müzdelife'den ayrılıp fecirden önce Mina'ya geçebilir; herhangi bir ceza kurbanı gerekmez.",
                "hanefi_hukum": "Fecr-i sâdıktan sonra gün doğana kadar vakfe vaciptir; mazeretsiz terk eden ceza kurbanı (dem) keser.",
                "safii_hukum": "Gecenin ikinci yarısında Müzdelife'de bir an bulunmak kâfidir; fecri beklemek sünnettir.",
                "maliki_hukum": "Müzdelife'de eşyayı indirip biraz duraklamak vaciptir, geceyi orada geçirmek sünnettir.",
                "hanbeli_hukum": "Gece yarısından sonra Mina'ya intikal etmek zayıflar ve mazeretliler için meşrudur, fidye gerekmez."
            }),
            (22, "İzdiham Anında Şeytan Taşlamada (Ramy-i Cimar) Başkasına Vekâlet Vermek", "النيابة والتوكيل في رمي الجمار للعاجز والمشقة", {
                "ruhsat_mezhep": "Dört Mezhep İttifakı (Meşakkat anında vekâlet cevazı)",
                "ruhsat_hukum": "Hastalık, aşırı yaşlılık, ezilme tehlikesi veya şiddetli izdiham meşakkati halinde kişi kendi yerine taş atması için bir başkasını vekil tayin edebilir.",
                "hanefi_hukum": "Ayakta namaz kılamayacak derecedeki hasta ve acizler vekil tayin edebilir.",
                "safii_hukum": "Taşlama mahalline gidemeyecek meşakkati olanlar vekille taş attırabilir.",
                "maliki_hukum": "Hastalık sebebiyle bizzat atamayan vekile attırır; iyileşirse iade eder veya kurban keser.",
                "hanbeli_hukum": "Aşırı izdiham, kadınların ve güçsüzlerin ezilme riski vekâlet için meşru özürdür."
            })
        ]
    },
    {
        "bolum_id": "07_nikah",
        "bolum_adi": "Kitâbü'n-Nikâh ve't-Talâk (Aile Hukuku)",
        "dosya": "07_nikah.md",
        "meseleler": [
            (23, "Büluğa Ermiş Akıllı Kadının Velisiz Olarak Kendi Başına Evlenmesi", "تزويج الثيب والبكر الرشيدة نفسها بغير إذن الولي", {
                "ruhsat_mezhep": "Hanefî Mezhebi (İmam Ebû Hanîfe)",
                "ruhsat_hukum": "Büluğa ermiş ve akıl baliğ olmuş bir kadın (bakire veya dul), denk bir erkekle (küfüv) mehr-i misilden az olmamak şartıyla velisinin izni olmadan bizzat nikâh akdi yapabilir.",
                "hanefi_hukum": "Hür ve reşîde kadın malında tasarruf ettiği gibi nefsinde de tasarruf edebilir; nikâh geçerlidir.",
                "safii_hukum": "Velisiz nikâh kat'iyyen bâtıldır; kadının bizzat nikâh akdetme yetkisi yoktur.",
                "maliki_hukum": "Veli nikâhın sıhhat rüknüdür; velisiz kıyılan nikâh derhal feshedilir.",
                "hanbeli_hukum": "Velisiz nikâh sahih değildir; 'Velisiz nikâh bâtıldır' hadisi mutlaktır."
            }),
            (24, "Aynı Anda veya Tek Mecliste Verilen Üç Talâkın Sayısı", "إيقاع الطلاق الثلاث بلفظ واحد أو في مجلس واحد", {
                "ruhsat_mezhep": "İbn Teymiyye / İbnü'l-Kayyim ve Mütekaddimîn Tahrîci (Cumhur hilafına ruhsat)",
                "ruhsat_hukum": "Bir mecliste veya tek sözle söylenen 'üçten dokuza şart olsun' veya 'seni üç talakla boşadım' ifadesi sadece bir ric'î talâk sayılır; evlilik tamamen yıkılmaz.",
                "hanefi_hukum": "Bir lafızla üç talak vermek bid'î ve haramdır fakat hukuken üç talakın üçü de vaki olur; bâin olur.",
                "safii_hukum": "Tek lafızla üç talak vermek mubahtır ve üç talakın tamamı derhal düşer.",
                "maliki_hukum": "Üç talak birden geçerli olur; hülle olmaksızın tekrar evlenemezler.",
                "hanbeli_hukum": "Mezhep içi klasik kavilde üçü de vaki olur; İbn Teymiyye ve tahkik ehline göre ise sadece 1 talak sayılır."
            }),
            (25, "Öfke (Cinnet Derecesi Olmayan Şiddetli Gazap) Anında Boşama", "طلاق الغضبان وحكم وقوعه مع شدة الغضب", {
                "ruhsat_mezhep": "Hanbelî Mezhebi (İbn Teymiyye tahrîci) ve Hanefî müteahhirîn kavli",
                "ruhsat_hukum": "Kişinin iradesini baskılayan, ne dediğini kontrol edemeyecek derecedeki şiddetli gazap ve cinnet anında ağzından çıkan talak lafızları vaki olmaz.",
                "hanefi_hukum": "Akli melekeleri tamamen gitmedikçe öfkelinin talakı geçerlidir; ancak cinnet/hezeyan hali hariçtir.",
                "safii_hukum": "Kişi ne söylediğinin farkında olduğu sürece öfke boşamanın vukuuna mâni değildir.",
                "maliki_hukum": "Şiddetli galebe ve cinnet derecesinde şuursuzluk yoksa öfke talakı düşürür.",
                "hanbeli_hukum": "Aklı örten, kasıt ve tefekkürü engelleyen şiddetli öfke halinde talak vaki olmaz (İğlâk hadisi)."
            })
        ]
    },
    {
        "bolum_id": "08_etime",
        "bolum_adi": "Kitâbü'l-Et'ime ve'l-Eşribe (Gıdalar ve Helal/Haramlar)",
        "dosya": "08_etime.md",
        "meseleler": [
            (26, "Balık Suretinde Olmayan Deniz Canlılarının (Karides, Kalamar, Yengeç, Midye) Yenmesi", "أكل ما سوى السمك من حيوانات البحر كالروبيان والسرطان", {
                "ruhsat_mezhep": "Şâfiî, Mâlikî ve Hanbelî Mezhepleri",
                "ruhsat_hukum": "Denizde yaşayan ve suda barınan her türlü canlı (karides, kalamar, ahtapot, midye, yengeç) balık suretinde olmasa dahi helaldir ve boğazlanmadan yenir.",
                "hanefi_hukum": "Yalnızca balık cinsinden olan deniz canlıları helaldir; midye, karides, yengeç tahrîmen mekruhtur.",
                "safii_hukum": "'Denizin suyu temiz, ölüsü helaldir' hadisi gereği suda yaşayan her canlı helaldir.",
                "maliki_hukum": "Deniz canlılarının tamamı istisnasız helaldir; boğazlama şartı aranmaz.",
                "hanbeli_hukum": "Deniz hayvanlarının tamamı helaldir; timsah ve kurbağa gibi karada da yaşayanlar hariçtir."
            }),
            (27, "Katı ve Sıvı Yağların İçine Fare veya Pislik Düşmesi", "وقوع الفأرة أو النجاسة في السمن المائع والجامد", {
                "ruhsat_mezhep": "Cumhur Fıkhı (Katı yağda) ve Zührî/İbn Teymiyye (Sıvı yağda istihale/temizleme ruhsatı)",
                "ruhsat_hukum": "Katı yağa necis madde düşerse sadece temas ettiği çevre kısım atılır, kalanı temizdir; sıvı yağda ise renk, koku ve tadı bozulmadığı sürece necasetin yayılmadığı kabul edilir.",
                "hanefi_hukum": "Katı yağda pisliğin etrafı kazınır atılır; sıvı yağ ise tamamen necis olur, yenmesi haramdır.",
                "safii_hukum": "Katı ise çevresi atılır; akıcı sıvı yağ ise necaset damladığı anda tamamı pislenir.",
                "maliki_hukum": "Katı yağda temas eden kısım atılır; sıvı yağda su gibi vasıfları değişmemişse necis saymayan rivayetler vardır.",
                "hanbeli_hukum": "Sıvı yağ içine necaset düşerse istihale etmedikçe mutlak olarak pislenir."
            }),
            (28, "Tıbbî ve Hijyenik Amaçlı Sentetik Alkol ve Dezenfektan Kullanımı", "استعمال الكحول الطبية والمنظفات وحكم طهارتها", {
                "ruhsat_mezhep": "Hanefî Mezhebi (İmam Ebû Hanîfe ve Ebû Yûsuf - Üzüm/Hurma dışı alkoller)",
                "ruhsat_hukum": "Üzüm ve hurmadan imal edilmeyen sentetik, kimyasal ve etil alkol türleri necâset-i galîza değildir; temizlik, parfüm, tentürdiyot ve ilaçta kullanılması abdesti bozmaz ve namaza mâni değildir.",
                "hanefi_hukum": "Hamr (şarap) dışındaki maddelerden elde edilen alkolün kendisi necâset-i ayniye değildir; sarhoşluk vermeyecek miktar ve harici kullanım caizdir.",
                "safii_hukum": "Sarhoş edici her türlü sıvı necis-i ayndır; alkollü maddelerin tene sürülmesi necâsettir, yıkanmalıdır.",
                "maliki_hukum": "Hamr necis kabul edilmekle birlikte, kimyasal işlem görmüş veya ilaca karışmış maddelerde umum-ı belva sebebiyle ruhsat vardır.",
                "hanbeli_hukum": "Çoğu sarhoş edenin azı da haram ve necistir; ancak tedavi ve sanayi kullanımında zaruret hali gözetilir."
            })
        ]
    }
]

def main():
    print("=" * 80)
    print("[*] FAZ 2: GENİŞLETİLMİŞ KÜLLİYAT ÜRETİMİ (MESELE 017 - 028)")
    print("=" * 80)

    compiler = ProductionFikhCompiler()
    completed = load_checkpoints()
    print(f"[+] Mevcut checkpoint sayısı: {len(completed)}")

    for bolum in FAZ_2_PLANI:
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
        ("03_siyam.md", "KİTÂBÜ'S-SIYÂM (ORUÇ VE İMSAK)"),
        ("04_buyu.md", "KİTÂBÜ'L-BÜYÛ' (TİCARET VE MUÂMELÂT)"),
        ("05_zekat.md", "KİTÂBÜ'Z-ZEKÂT VE'L-FITR (ZEKÂT VE SADAKA-I FITIR)"),
        ("06_hac.md", "KİTÂBÜ'L-HAC VE'L-UMRE (HAC VE UMRE HÜKÜMLERİ)"),
        ("07_nikah.md", "KİTÂBÜ'N-NİKÂH VE'T-TALÂK (AİLE HUKUKU)"),
        ("08_etime.md", "KİTÂBÜ'L-ET'İME VE'L-EŞRİBE (GIDALAR VE HELAL/HARAMLAR)")
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

    with open(MASTER_BOOK_PATH, "w", encoding="utf-8") as mf:
        mf.write(master_full)

    size_kb = os.path.getsize(MASTER_BOOK_PATH) / 1024
    print("=" * 80)
    print(f"[+] FAZ 2 BAŞARIYLA TAMAMLANDI:")
    print(f"    Master Kitap: {MASTER_BOOK_PATH}")
    print(f"    Dosya Boyutu: {size_kb:.2f} KB")
    print(f"    Toplam Mesele Sayısı: {len(completed)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
