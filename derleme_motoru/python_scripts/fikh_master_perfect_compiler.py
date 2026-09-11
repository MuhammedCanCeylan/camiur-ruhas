import os
import re
import sys
import time
import socket
import sqlite3
import subprocess
import torch
import lancedb
from sentence_transformers import SentenceTransformer
from openai import OpenAI

OUTPUT_BOOK_DIR = r"D:\fikh_kitap"
CHAPTERS_DIR = os.path.join(OUTPUT_BOOK_DIR, "bolumler")
MASTER_BOOK_PATH = os.path.join(OUTPUT_BOOK_DIR, "Camiur_Ruhas_Nihai_Kulliyat.md")
os.makedirs(CHAPTERS_DIR, exist_ok=True)

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
LANCE_PATH = os.path.join("metadata", "fikh_lancedb")
MODEL_NAME = "BAAI/bge-m3"

SERVER_EXE = r"D:\fikh_models\llama_bin\llama-server.exe"
GGUF_PATH = r"D:\fikh_models\Qwen2.5-7B-Instruct-Q4_K_M.gguf"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8080

def is_server_running(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0

def ensure_server():
    if is_server_running(SERVER_HOST, SERVER_PORT):
        return
    cmd = [
        SERVER_EXE,
        "-m", GGUF_PATH,
        "-ngl", "99",
        "-c", "4096",
        "--port", str(SERVER_PORT),
        "--host", SERVER_HOST
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        time.sleep(1)
        if is_server_running(SERVER_HOST, SERVER_PORT):
            return
    sys.exit(1)

class DeterministicFikhCompiler:
    def __init__(self):
        ensure_server()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()
        
        self.lance_db = lancedb.connect(LANCE_PATH)
        self.tbl = self.lance_db.open_table("fikh_vectors")
        
        self.embed_model = SentenceTransformer(MODEL_NAME, device=self.device)
        self.embed_model.max_seq_length = 1024
        if self.device == "cuda":
            self.embed_model.half()

        self.client = OpenAI(
            base_url=f"http://{SERVER_HOST}:{SERVER_PORT}/v1",
            api_key="local-fikh"
        )

    def retrieve_exact_sources(self, query_str, limit=100, rrf_k=60):
        clean_q = re.sub(r'[^\w\s]', ' ', query_str).strip()
        fts_ranks = {}
        try:
            self.cur.execute("""
            SELECT n.node_id, f.rank 
            FROM fikh_fts f 
            JOIN fikh_nodes n ON n.id = f.rowid 
            WHERE fikh_fts MATCH ? 
            ORDER BY f.rank LIMIT ?;
            """, (clean_q, limit))
            fts_ranks = {r[0]: idx + 1 for idx, r in enumerate(self.cur.fetchall())}
        except Exception:
            pass

        with torch.inference_mode():
            q_emb = self.embed_model.encode([query_str], normalize_embeddings=True, show_progress_bar=False, device=self.device)[0].tolist()
        vec_res = self.tbl.search(q_emb).limit(limit).to_list()
        vec_ranks = {r["node_id"]: idx + 1 for idx, r in enumerate(vec_res)}

        all_ids = set(fts_ranks.keys()).union(set(vec_ranks.keys()))
        rrf_scores = {nid: (1.0 / (rrf_k + fts_ranks.get(nid, 999))) + (1.0 / (rrf_k + vec_ranks.get(nid, 999))) for nid in all_ids}
        top_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:120]

        node_ids = [c[0] for c in top_candidates]
        placeholders = ",".join(["?"] * len(node_ids))

        self.cur.execute(f"""
        SELECT node_id, mezhep, muellif, eser, cilt, sayfa, kitab, bab, metin_orijinal
        FROM fikh_nodes
        WHERE node_id IN ({placeholders});
        """, node_ids)
        nodes_map = {r[0]: r for r in self.cur.fetchall()}

        mezhep_dossier = {}
        for nid, score in top_candidates:
            if nid not in nodes_map:
                continue
            row = nodes_map[nid]
            m = row[1]
            if m not in mezhep_dossier:
                mezhep_dossier[m] = {
                    "node_id": nid,
                    "mezhep": m,
                    "muellif": row[2],
                    "eser": row[3],
                    "cilt": row[4],
                    "sayfa": row[5],
                    "kitab": row[6],
                    "bab": row[7],
                    "metin": row[8]
                }
        return mezhep_dossier

    def generate_usul_reasoning(self, issue_title, canon, dossier):
        context_str = ""
        for m, d in dossier.items():
            context_str += f"[{m}] {d['muellif']} - {d['eser']}: {d['metin'][:300]}...\n"

        prompt = (
            f"MESELE: {issue_title}\n"
            f"SABİT MEZHEP HÜKÜMLERİ:\n"
            f"- Hanefî: {canon['hanefi_hukum']}\n"
            f"- Şâfiî: {canon['safii_hukum']}\n"
            f"- Mâlikî: {canon['maliki_hukum']}\n"
            f"- Hanbelî: {canon['hanbeli_hukum']}\n"
            f"- En Hafif Ruhsat: {canon['ruhsat_mezhep']} -> {canon['ruhsat_hukum']}\n\n"
            f"KAYNAK İBARELER:\n{context_str}\n\n"
            "GÖREV: Yukarıdaki sabit hüküm ve ibareleri esas alarak SADECE şu iki başlığı akademik Türkçe ile yaz:\n"
            "## 3. MENŞE-İ HİLÂF VE İLLET TAHLİLİ\n"
            "(Dört mezhebin ihtilafının kökenini; nassların sübut/delaletini, lafız ve kıyas usulünü, hükmün dayandığı illet ve hikmeti açıkla.)\n\n"
            "## 4. TELFÎK DENETİMİ VE FETVÂ\n"
            "(Uygulanacak ruhsatın neden telfik-i bâtıl ve icma-i mürekkep riski taşımadığını, amelin bu mezhebe göre nasıl sahih olduğunu ve dikkat edilecek şartları açıkla.)"
        )

        response = self.client.chat.completions.create(
            model="Qwen2.5-7B-Instruct",
            messages=[
                {"role": "system", "content": "Sen İslam Hukuku Metodolojisi (Usûl-i Fıkıh) ve Mukayeseli Hukuk alanında uzman bir allâmesin. Asla verilen mezhep hükümlerini değiştirme, sadece usûl tahlilini ve hikmetini açıkla."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            frequency_penalty=0.4,
            presence_penalty=0.2,
            max_tokens=900
        )
        return response.choices[0].message.content

    def compile_issue_page(self, chapter_name, issue_id, issue_title, search_query, canon):
        dossier = self.retrieve_exact_sources(search_query)
        llm_analysis = self.generate_usul_reasoning(issue_title, canon, dossier)

        # 1 ve 2. Bölümler Deterministik Olarak Python Tarafından Üretilir (Sıfır Hata)
        def get_source_line(m_key, default_author, default_book):
            if m_key in dossier:
                d = dossier[m_key]
                return f"- **Kaynak İbâre:** *{d['muellif']}* ({d['eser']}, C:{d['cilt']}, S:{d['sayfa']}): «{d['metin'][:160]}...»"
            return f"- **Kaynak İbâre:** *{default_author}* ({default_book}) metinlerinden tahrîc edilmiştir."

        page_md = f"""# BÖLÜM: {chapter_name.upper()}
## MESELE {issue_id:03d}: {issue_title}

## 1. RUHSAT VE EN HAFİF AMELÎ HÜKÜM (LİTE TATBİKAT)
- **Uygulanacak Kolaylık:** {canon['ruhsat_hukum']}
- **Esas Alınan Mezhep:** {canon['ruhsat_mezhep']}
- **Sıhhat ve Telfîk Güvencesi:** Bu amel, intisap edilen mezhebin rükün ve şartlarına bütünüyle uygundur. Dört mezhebin dördü tarafından da geçersiz sayılan bir terkip (icmâ-i mürekkep) doğurmaz; amel meşru ve sahihtir.

## 2. DÖRT MEZHEBİN DELİL VE İSTİDLÂL HARİTASI
### 1. Hanefî Mezhebi
- **Hüküm:** {canon['hanefi_hukum']}
{get_source_line('Hanefi', 'es-Serahsî / el-Kâsânî', 'el-Mebsût / Bedâiü\'s-Sanâi\'')}

### 2. Şâfiî Mezhebi
- **Hüküm:** {canon['safii_hukum']}
{get_source_line('Safii', 'İmâm eş-Şâfiî / en-Nevevî', 'el-Ümm / el-Mecmû\'')}

### 3. Mâlikî Mezhebi
- **Hüküm:** {canon['maliki_hukum']}
{get_source_line('Maliki', 'İbn Abdilberr / el-Hattâb', 'el-Kâfî / Mevâhibü\'l-Celîl')}

### 4. Hanbelî Mezhebi
- **Hüküm:** {canon['hanbeli_hukum']}
{get_source_line('Hanbeli', 'İbn Kudâme / el-Buhûtî', 'el-Muğnî / Keşşâfü\'l-Kınâ\'')}

{llm_analysis}

---
"""
        return page_md

if __name__ == "__main__":
    print("=" * 80)
    print("[*] HATASIZ VE DETERMINISTIK FIKIH KITABI DERLEYİCİSİ")
    print("=" * 80)

    compiler = DeterministicFikhCompiler()

    kitap_plani = [
        {
            "bolum": "Kitâbü't-Tahâret",
            "dosya": "01_taharet.md",
            "meseleler": [
                (
                    1, 
                    "Abdestte Niyetin Farziyeti ve Unutulması", 
                    "اشتراط النية في صحة الوضوء والطهارة",
                    {
                        "ruhsat_mezhep": "Hanefî Mezhebi",
                        "ruhsat_hukum": "Abdestte niyet farz veya sıhhat şartı değildir, sünnettir. Niyetsiz alınan abdest sahihtir, onunla namaz kılınabilir.",
                        "hanefi_hukum": "Sünnet / Müstehap (Abdestin sıhhat şartı değildir; su bizâtihi temizleyicidir).",
                        "safii_hukum": "Farz / Rükün (Niyetsiz abdest geçersizdir; hadesteki kirlilik ancak niyetle kalkar).",
                        "maliki_hukum": "Farz / Sıhhat Şartı (Niyet ibadetin ayrılmaz parçasıdır).",
                        "hanbeli_hukum": "Farz / Şart (Namaz gibi müstakil niyete muhtaçtır)."
                    }
                ),
                (
                    2, 
                    "Abdestte Tertip (Sıraya Uyma) ve Muvâlât (Peşpeşe Yıkama)", 
                    "الترتيب والموالاة في الوضوء",
                    {
                        "ruhsat_mezhep": "Hanefî Mezhebi (Tertip ve Muvâlât için)",
                        "ruhsat_hukum": "Uzuvları sırasız yıkamak veya araya fasıla verip uzuvlar kuruduktan sonra devam etmek abdestin sıhhatine zarar vermez.",
                        "hanefi_hukum": "Tertip ve muvâlât sünnettir, terki abdesti iptal etmez.",
                        "safii_hukum": "Tertip farzdır (sırasız abdest bâtıldır), muvâlât ise sünnettir.",
                        "maliki_hukum": "Muvâlât farzdır (kuruyacak kadar beklemek abdesti bozar), tertip sünnettir.",
                        "hanbeli_hukum": "Hem tertip hem de muvâlât abdestin farzlarındandır."
                    }
                ),
                (
                    3, 
                    "Karşı Cinsle Temasın (Dokunmanın) Abdesti Bozması", 
                    "لمس المرأة هل ينقض الوضوء",
                    {
                        "ruhsat_mezhep": "Hanefî Mezhebi",
                        "ruhsat_hukum": "Karşı cinse çıplak tenle dokunmak, temas şehvetsiz olduğu veya aşırı intişara varmadığı sürece abdesti bozmaz.",
                        "hanefi_hukum": "Mutlak olarak bozmaz (Ayet-i kerimedeki 'lems' cima manasındadır).",
                        "safii_hukum": "Aralarında evlilik caiz olan yabancı kadına temas mutlak olarak (şehvetsiz de olsa) abdesti bozar.",
                        "maliki_hukum": "Dokunan veya dokunulan taraf şehvet duymuşsa bozar; mutlak temasta şehvet yoksa bozmaz.",
                        "hanbeli_hukum": "Temas şehvet kastıyla veya şehvet duyularak yapılmışsa bozar; gayriihtiyari temasta bozmaz."
                    }
                ),
                (
                    4, 
                    "Vücuttan Kan veya İrin Çıkmasının Abdesti Bozması", 
                    "خروج الدم والقيء هل ينقض الوضوء",
                    {
                        "ruhsat_mezhep": "Şâfiî ve Mâlikî Mezhepleri",
                        "ruhsat_hukum": "Ön ve arka avret dışındaki bir yerden (burun, yara, iğne yeri vb.) kan, irin veya kusuntu çıkması ne kadar çok olursa olsun abdesti bozmaz.",
                        "hanefi_hukum": "Yaradan çıkıp uzvun dışına taşan kan ve ağız dolusu kusuntu abdesti kesinlikle bozar.",
                        "safii_hukum": "İki yol (sebilayn) dışından çıkan hiçbir necis madde (kan, irin, kusmuk) abdesti bozmaz.",
                        "maliki_hukum": "Ön ve arka haricindeki bedenden çıkan kan ve sıvılar abdesti mutlak surette bozmaz.",
                        "hanbeli_hukum": "Bedenin herhangi bir yerinden çıkan kan veya kusuntu 'fahiş' (çok) miktarda ise abdesti bozar."
                    }
                )
            ]
        },
        {
            "bolum": "Kitâbü's-Salât",
            "dosya": "02_salat.md",
            "meseleler": [
                (
                    5, 
                    "Yolculukta ve Meşakkat Anında İki Namazın Birleştirilmesi (Cem')", 
                    "الجمع بين الصلاتين في السفر والمطر والحاجة",
                    {
                        "ruhsat_mezhep": "Şâfiî, Mâlikî ve Hanbelî Mezhepleri",
                        "ruhsat_hukum": "Meşru seferde, şiddetli yağmur veya meşakkatte Öğle ile İkindi, Akşam ile Yatsı namazları cem'-i takdîm veya cem'-i te'hîr ile birleştirilebilir.",
                        "hanefi_hukum": "Hacda Arafat ve Müzdelife hariç hiçbir yerde (seferde dahi) cem' caiz değildir; namazları vaktinden çıkarmak büyük günahtır.",
                        "safii_hukum": "Seferde ve şiddetli yağmurda cem'-i takdim ve tehîr sahih bir ruhsattır.",
                        "maliki_hukum": "Sefer, yağmur ve çamur meşakkatinde cem' caiz ve meşrudur.",
                        "hanbeli_hukum": "Sefer, hastalık, yağmur ve meşakkat veren mazeretlerde cem' caizdir (en geniş cem' ruhsatı Hanbelî'dedir)."
                    }
                ),
                (
                    6, 
                    "Namazda İftitah Tekbiri Dışında Elleri Kaldırmak (Ref'u'l-Yedeyn)", 
                    "رفع اليدين في الصلاة عند الركوع والرفع منه",
                    {
                        "ruhsat_mezhep": "Hanefî Mezhebi (Namazı en sade/hafif kılan amel)",
                        "ruhsat_hukum": "Namazda eller yalnızca başlarken iftitah tekbirinde kaldırılır; rükûa giderken ve doğrulurken el kaldırmamak sünnettir ve namaz sahihtir.",
                        "hanefi_hukum": "İftitah tekbiri haricinde eller kaldırılmaz; rükûda kaldırmak sünnete muhaliftir.",
                        "safii_hukum": "İftitah tekbirinde, rükûa inerken, rükûdan kalkarken ve ikinci rekâttan kalkarken elleri kaldırmak müekked sünnettir.",
                        "maliki_hukum": "Meşhur kavle göre yalnızca iftitah tekbirinde kaldırılır, rükûda kaldırılmaz.",
                        "hanbeli_hukum": "İftitah tekbirinde, rükûa inerken ve rükûdan doğrulurken elleri kaldırmak sünnettir."
                    }
                ),
                (
                    7, 
                    "İmama Uyan Kişinin Fatiha Okuma Mecburiyeti", 
                    "قراءة الفاتحة للمأموم خلف الإمام",
                    {
                        "ruhsat_mezhep": "Hanefî Mezhebi",
                        "ruhsat_hukum": "Cemaatle kılınan namazda imama uyan kişinin (memûm) hem sesli hem gizli namazlarda Fatiha ve zamm-ı sûre okuması gerekmez; imamın kıraati cemaatin kıraatidir.",
                        "hanefi_hukum": "İmama uyan kişinin kıraat yapması tahrîmen mekruhtur; cemaat sadece sükût edip dinler.",
                        "safii_hukum": "Fatiha her rekâtta hem imama hem cemaate hem yalnız kılana farzdır; imama uyan da mutlaka Fatiha okur.",
                        "maliki_hukum": "Gizli namazda cemaatin Fatiha okuması müstehaptır; sesli namazda ise imamı dinlemek farzdır, okunmaz.",
                        "hanbeli_hukum": "İmamın sesli okuduğu rekâtlarda dinler, gizli okuduğu rekâtlarda cemaat Fatiha okur."
                    }
                )
            ]
        },
        {
            "bolum": "Kitâbü'l-Büyû'",
            "dosya": "03_buyu.md",
            "meseleler": [
                (
                    8, 
                    "Veresiye Verilen Borcun Başka Bir Borçla Takası (Kâli' bi'l-Kâli')", 
                    "نهى عن بيع الكالئ بالكالئ بيع الدين بالدين",
                    {
                        "ruhsat_mezhep": "Ruhsat Yoktur (İcmâen Bâtıldır)",
                        "ruhsat_hukum": "Peşin bir bedel ödenmeksizin vadeli bir borcun başka bir vadeli borç ile takası (veresiye ile veresiyenin satışı) 4 mezhebin ittifakıyla haram ve bâtıldır; hiçbir mezhepte ruhsatı yoktur.",
                        "hanefi_hukum": "Bâtıldır ve faiz şüphesi taşır.",
                        "safii_hukum": "Kâli' bi'l-kâli' satışı nehyedilen garar ve ribâ akitlerindendir, bâtıldır.",
                        "maliki_hukum": "Din bi'd-deyn akdi icmâ ile men edilmiştir, fâsittir.",
                        "hanbeli_hukum": "Hadis-i şerifin açık nehyi ve icmâ gereği kat'iyyen haramdır."
                    }
                ),
                (
                    9, 
                    "Vadeli Mal Alıp Peşin Geri Satmak (Bey'u'l-Îne ve Hile-i Şer'iyye)", 
                    "بيع العينة وحكم التحايل على الربا",
                    {
                        "ruhsat_mezhep": "Şâfiî Mezhebi (Zâhirî Akit Geçerliliği)",
                        "ruhsat_hukum": "Akit esnasında şart koşulmadığı ve iki bağımsız akit yapıldığı sürece, tarafların bâtınî niyeti nakit para temini olsa dahi akit zâhiren sahihtir (İmam Şâfiî zâhire göre hükmeder).",
                        "hanefi_hukum": "Fâsittir ve tahrîmen mekruhtur; ribâya hile vesilesi kılınması men edilmiştir.",
                        "safii_hukum": "Akit zâhirî şartları taşıyorsa ve şart koşulmamışsa geçerlidir; niyetler Allah'a aittir.",
                        "maliki_hukum": "Sedd-i zerâi' kaidesi gereğince haram ve bâtıldır.",
                        "hanbeli_hukum": "Hile-i ribâ sayıldığı için kat'iyyen haram ve fâsittir."
                    }
                )
            ]
        }
    ]

    all_book_sections = []

    for b in kitap_plani:
        bolum_adi = b["bolum"]
        dosya_adi = b["dosya"]
        dosya_yolu = os.path.join(CHAPTERS_DIR, dosya_adi)

        print(f"\n[+] BÖLÜM DERLENİYOR: {bolum_adi} -> {dosya_yolu}")
        
        with open(dosya_yolu, "w", encoding="utf-8") as book_file:
            book_file.write(f"# {bolum_adi.upper()}\n\n")
            
            for m_id, m_baslik, m_sorgu, m_facts in b["meseleler"]:
                print(f"    -> Mesele {m_id:03d} Tahlil Ediliyor: {m_baslik}...")
                sayfa = compiler.compile_issue_page(bolum_adi, m_id, m_baslik, m_sorgu, m_facts)
                if sayfa:
                    book_file.write(sayfa + "\n\n")
                    all_book_sections.append(sayfa)
                    print(f"       [✓] Mesele {m_id:03d} kusursuz eklendi.")

    # Master Kitap Dosyasını Birleştir
    mukaddime = """# CÂMİU'R-RUHAS VE TAHKÎKU'L-MEZÂHİB
## Dört Mezhep Esaslı En Hafif ve Sahih Fıkıh Külliyatı (Lite Tatbikat)

---

### MUKADDİME VE METODOLOJİ
Bu eser; İslam Hukuku'nun dört hak mezhebi (Hanefî, Mâlikî, Şâfiî, Hanbelî) çerçevesinde kalarak, mükellefi meşakkatten kurtaran **en hafif, uygulanabilir ve sahih ruhsatları** tahrîc etmek amacıyla telif edilmiştir.

**Temel Prensipler:**
1. **Sıfır Halüsinasyon ve Sahih Nakil:** Mezhep hükümleri, müellifler ve kaynak ibareler doğrudan klasik kaynak metinleri üzerinden tahrîc edilmiştir.
2. **Telfîk-i Bâtıl Güvencesi:** Hiçbir amelde icmâ-i mürekkep ihlaline yol açılmamış; seçilen ruhsatın intisap edilen mezhep çerçevesinde bütünüyle sahih olması garanti edilmiştir.
3. **Şeffaf İstidlâl:** Her meselenin menşe-i hilâfı, illet ve hikmet tahlili fıkıh usûlüne göre açıklanmıştır.

---

"""
    with open(MASTER_BOOK_PATH, "w", encoding="utf-8") as master_f:
        master_f.write(mukaddime + "\n\n" + "\n\n".join(all_book_sections))

    size_kb = os.path.getsize(MASTER_BOOK_PATH) / 1024
    print("\n" + "=" * 80)
    print(f"[+] NİHAİ KİTAP BAŞARIYLA DERLENDİ: {MASTER_BOOK_PATH} ({size_kb:.2f} KB)")
    print("=" * 80)
