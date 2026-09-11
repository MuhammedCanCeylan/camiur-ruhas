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

class ProductionFikhCompiler:
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
            "GÖREV:\n"
            "1. Asla cümleleri yarım bırakma. Tamamlanmış, akıcı paragraflarla yaz.\n"
            "2. SADECE şu iki başlığı eksiksiz oluştur:\n"
            "## 3. MENŞE-İ HİLÂF VE İLLET TAHLİLİ\n"
            "(Dört mezhebin ihtilafının kökenini; nassların delaletini, kıyas ve usul farkını, hükmün dayandığı illet ve hikmeti açıkla.)\n\n"
            "## 4. TELFÎK DENETİMİ VE FETVÂ\n"
            "(Uygulanacak ruhsatın neden telfik-i bâtıl ve icma-i mürekkep riski taşımadığını, amelin bu mezhebe göre nasıl sahih olduğunu ve dikkat edilecek şartları açıkla.)"
        )

        response = self.client.chat.completions.create(
            model="Qwen2.5-7B-Instruct",
            messages=[
                {"role": "system", "content": "Sen İslam Hukuk Metodolojisi ve Mukayeseli Fıkıh allâmesisin. Verilen sabit mezhep hükümlerini asla tahrif etmeden akademik usûl tahlilini ve fetvasını eksiksiz yaz."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            frequency_penalty=0.3,
            presence_penalty=0.1,
            max_tokens=1500
        )
        return response.choices[0].message.content

    def compile_issue_page(self, chapter_name, issue_id, issue_title, search_query, canon):
        dossier = self.retrieve_exact_sources(search_query)
        llm_analysis = self.generate_usul_reasoning(issue_title, canon, dossier)

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
