import os
import re
import sys
import time
import json
import socket
import sqlite3
import subprocess
import torch
import lancedb
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# Dizin Yapılandırması
OUTPUT_BOOK_DIR = r"D:\fikh_kitap"
CHAPTERS_DIR = os.path.join(OUTPUT_BOOK_DIR, "bolumler")
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

class FikhBookCompiler:
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

    def retrieve_context(self, query_str, limit=100, rrf_k=60):
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

    def compile_issue_page(self, chapter_name, issue_id, issue_title, search_query):
        dossier = self.retrieve_context(search_query)
        if not dossier:
            return None

        context_blocks = []
        for m in ["Hanefi", "Maliki", "Safii", "Hanbeli", "Mukaren"]:
            if m in dossier:
                d = dossier[m]
                context_blocks.append(
                    f"### [{m.upper()} MEZHEBİ METNİ]\n"
                    f"- Eser/Müellif: {d['muellif']} - {d['eser']} (C:{d['cilt']}, S:{d['sayfa']})\n"
                    f"- İbâre: {d['metin'][:400]}...\n"
                )

        system_prompt = (
            "Sen 4 hak mezhebi kuşatan, telfîk-i bâtıldan arındırılmış, en sahih ve uygulanabilir 'Câmiu'r-Ruhas' "
            "(Ruhsatlar ve Kolaylıklar Külliyatı) kitabını yazan bir allâmesin.\n"
            "HEDEF: Okuyucuya 4 mezhepten en az birine tam uyan en hafif/kolay amel yolunu sunmak, "
            "aynı zamanda bu amelin hangi mezhepten, hangi nass ve illetle çıkarıldığını şüpheye yer bırakmayacak açıklıkta serdetmektir.\n\n"
            "KESİN BİÇİM KURALLARI:\n"
            "Çıktıyı ASLA serbest bırakma. YALNIZCA şu 4 ana başlığı kullanarak doğrudan Markdown üret:\n"
            "## 1. RUHSAT VE EN HAFİF AMELÎ HÜKÜM (LİTE TATBİKAT)\n"
            "- Uygulanacak Kolaylık: [Net, tereddütsüz hüküm]\n"
            "- Esas Alınan Mezhep ve İmam: [Mezhep, Müellif ve Eser]\n"
            "- Sıhhat ve Telfîk Güvencesi: [İcmâ-i mürekkep riskinin olmadığını, amelin bu mezhepçe bütünüyle sahih olduğunu açıkla]\n\n"
            "## 2. DÖRT MEZHEBİN DELİL VE İSTİDLÂL HARİTASI\n"
            "(Hanefî, Mâlikî, Şâfiî ve Hanbelî mezheplerinin nassa yaklaşımını, delillerini ve ibarelerini ayrı ayrı sırala)\n\n"
            "## 3. MENŞE-İ HİLÂF VE İLLET TAHLİLİ\n"
            "(İhtilafın usûlî sebebi, lafız ihtilafı mı, kıyas farkı mı, illet ve hikmet tahlili)\n\n"
            "## 4. FETVÂ VE NİHAİ UYARI\n"
            "(Ameli işlerken şüpheye düşülmemesi için dikkat edilecek asli şartlar)"
        )

        user_prompt = (
            f"KİTAP BÖLÜMÜ: {chapter_name}\n"
            f"MESELE NO: {issue_id}\n"
            f"MESELE BAŞLIĞI: {issue_title}\n\n"
            f"KORPUSTAN GELEN ASLÎ MEZHEP METİNLERİ:\n"
            f"{''.join(context_blocks)}\n\n"
            f"Bu meseleyi en hafif sahih görüşü izole ederek ve 4 mezhebin tahlilini eksiksiz sunarak kitap maddesi haline getir."
        )

        response = self.client.chat.completions.create(
            model="Qwen2.5-7B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            frequency_penalty=0.4,
            presence_penalty=0.2,
            max_tokens=1500
        )

        content = response.choices[0].message.content
        
        page_md = (
            f"# BÖLÜM: {chapter_name.upper()}\n"
            f"## MESELE {issue_id:03d}: {issue_title}\n\n"
            f"{content}\n\n"
            f"---\n"
        )
        return page_md

if __name__ == "__main__":
    print("=" * 80)
    print("[*] NİHAİ FIKIH KİTABI TOPLU DERLEME MOTORU (BATCH COMPILER)")
    print("=" * 80)

    compiler = FikhBookCompiler()

    kitap_plani = [
        {
            "bolum": "Kitâbü't-Tahâret",
            "dosya": "01_taharet.md",
            "meseleler": [
                (1, "Abdestte Niyetin Farziyeti ve Unutulması", "اشتراط النية في صحة الوضوء والطهارة"),
                (2, "Abdestte Tertip (Sıraya Uyma) ve Muvalat (Peşpeşe Yıkama)", "الترتيب والموالاة في الوضوء"),
                (3, "Karşı Cinsle Temasın (Dokunmanın) Abdesti Bozması", "لمس المرأة هل ينقض الوضوء"),
                (4, "Vücuttan Kan veya İrin Çıkmasının Abdesti Bozması", "خروج الدم والقيء هل ينقض الوضوء")
            ]
        },
        {
            "bolum": "Kitâbü's-Salât",
            "dosya": "02_salat.md",
            "meseleler": [
                (5, "Yolculukta ve Meşakkat Anında İki Namazın Birleştirilmesi (Cem')", "الجمع بين الصلاتين في السفر والمطر والحاجة"),
                (6, "Namazda İftitah Tekbiri Dışında Elleri Kaldırmak (Ref'u'l-Yedeyn)", "رفع اليدين في الصلاة عند الركوع والرفع منه"),
                (7, "İmama Uyan Kişinin Fatiha Okuma Mecburiyeti", "قراءة الفاتحة للمأموم خلف الإمام")
            ]
        },
        {
            "bolum": "Kitâbü'l-Büyû'",
            "dosya": "03_buyu.md",
            "meseleler": [
                (8, "Veresiye Verilen Borcun Başka Bir Borçla Takası", "نهى عن بيع الكالئ بالكالئ بيع الدين بالدين"),
                (9, "Peşin Alınıp Vadeli Geri Satılan Akitlerde Şüphe (Bey'u'l-Îne)", "بيع العينة وحكم التحايل على الربا")
            ]
        }
    ]

    for b in kitap_plani:
        bolum_adi = b["bolum"]
        dosya_adi = b["dosya"]
        dosya_yolu = os.path.join(CHAPTERS_DIR, dosya_adi)

        print(f"\n[+] BÖLÜM DERLENİYOR: {bolum_adi} -> {dosya_yolu}")
        
        with open(dosya_yolu, "w", encoding="utf-8") as book_file:
            book_file.write(f"% {bolum_adi.upper()}\n% NİHAİ 4 MEZHEP RUHSAT KÜLLİYATI\n\n")
            
            for m_id, m_baslik, m_sorgu in b["meseleler"]:
                print(f"    -> Mesele {m_id:03d} Tahlil Ediliyor: {m_baslik}...")
                sayfa = compiler.compile_issue_page(bolum_adi, m_id, m_baslik, m_sorgu)
                if sayfa:
                    book_file.write(sayfa + "\n\n")
                    print(f"       [✓] Mesele {m_id:03d} kitaba eklendi.")
                else:
                    print(f"       [-] Mesele {m_id:03d} metni korpusta bulunamadı.")

    print("\n" + "=" * 80)
    print(f"[+] KİTAP BÖLÜMLERİ BAŞARIYLA DERLENDİ: {CHAPTERS_DIR}")
    print("=" * 80)
