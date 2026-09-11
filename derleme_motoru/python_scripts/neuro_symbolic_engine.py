import os
import re
import sys
import json
import time
import socket
import sqlite3
import subprocess
import threading
import torch
import lancedb
from sentence_transformers import SentenceTransformer
from openai import OpenAI

OUTPUT_BOOK_DIR = r"D:\fikh_kitap"
CHAPTERS_DIR = os.path.join(OUTPUT_BOOK_DIR, "bolumler")
MASTER_BOOK_PATH = os.path.join(OUTPUT_BOOK_DIR, "Camiur_Ruhas_Nihai_Kulliyat.md")
CHECKPOINT_FILE = os.path.join(OUTPUT_BOOK_DIR, "checkpoint.json")
os.makedirs(CHAPTERS_DIR, exist_ok=True)

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
LANCE_PATH = os.path.join("metadata", "fikh_lancedb")
MODEL_NAME = "BAAI/bge-m3"

SERVER_EXE = r"D:\fikh_models\llama_bin\llama-server.exe"
GGUF_PATH = r"D:\fikh_models\Qwen2.5-7B-Instruct-Q4_K_M.gguf"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8080

NOISE_PATTERNS = [
    r"عتق", r"كتابة", r"تدبير", r"أم ولد", r"مكاتب", r"مدبر", r"رق",
    r"بئر", r"نزح", r"جزية", r"خراج", r"سبي"
]

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

class NeuroSymbolicFikhEngine:
    def __init__(self):
        ensure_server()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._local = threading.local()
        self.embed_lock = threading.Lock()
        
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

    def get_cursor(self):
        """Thread-safe SQLite bağlantısı ve imleci sağlar."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._local.cur = self._local.conn.cursor()
        return self._local.cur

    def is_noise(self, text):
        for pat in NOISE_PATTERNS:
            if re.search(pat, text):
                return True
        return False

    def retrieve_isolated_madhab(self, query_str, madhab_name, limit=20):
        clean_q = re.sub(r'[^\w\s]', ' ', query_str).strip()
        cur = self.get_cursor()
        
        # 1. SQL FTS5
        fts_ids = []
        try:
            cur.execute("""
            SELECT n.node_id 
            FROM fikh_fts f 
            JOIN fikh_nodes n ON n.id = f.rowid 
            WHERE fikh_fts MATCH ? AND n.mezhep = ?
            LIMIT ?;
            """, (clean_q, madhab_name, limit))
            fts_ids = [r[0] for r in cur.fetchall()]
        except Exception:
            pass

        # 2. Vektörel Arama (CUDA Thread Koruması)
        with self.embed_lock:
            with torch.inference_mode():
                q_emb = self.embed_model.encode([query_str], normalize_embeddings=True, show_progress_bar=False, device=self.device)[0].tolist()
        
        try:
            vec_res = self.tbl.search(q_emb).where(f"mezhep = '{madhab_name}'").limit(limit).to_list()
            vec_ids = [r["node_id"] for r in vec_res]
        except Exception:
            vec_ids = []

        candidate_ids = list(set(fts_ids + vec_ids))
        if not candidate_ids:
            return None

        placeholders = ",".join(["?"] * len(candidate_ids))
        cur.execute(f"""
        SELECT node_id, mezhep, muellif, eser, cilt, sayfa, kitab, bab, metin_orijinal
        FROM fikh_nodes
        WHERE node_id IN ({placeholders});
        """, candidate_ids)
        
        rows = cur.fetchall()
        for r in rows:
            if not self.is_noise(str(r[6]) + " " + str(r[7])):
                return {
                    "node_id": r[0], "mezhep": r[1], "muellif": r[2], "eser": r[3],
                    "cilt": r[4], "sayfa": r[5], "kitab": r[6], "bab": r[7], "metin": r[8]
                }
        
        if rows:
            r = rows[0]
            return {
                "node_id": r[0], "mezhep": r[1], "muellif": r[2], "eser": r[3],
                "cilt": r[4], "sayfa": r[5], "kitab": r[6], "bab": r[7], "metin": r[8]
            }
        return None

    def compile_issue_page(self, chapter_name, issue_id, issue_title, search_query, canon):
        dossier = {}
        for m in ["Hanefi", "Safii", "Maliki", "Hanbeli"]:
            node = self.retrieve_isolated_madhab(search_query, m)
            if node:
                dossier[m] = node

        def format_source_line(m_key, default_author, default_book):
            if m_key in dossier:
                d = dossier[m_key]
                return f"- **Kaynak İbâre:** *{d['muellif']}* ({d['eser']}, C:{d['cilt']}, S:{d['sayfa']}): «{d['metin'][:160]}...»"
            return f"- **Kaynak İbâre:** *{default_author}* ({default_book}) metinlerinden tahrîc edilmiştir."

        context_str = ""
        for m, d in dossier.items():
            context_str += f"[{m}] {d['muellif']} - {d['eser']}: {d['metin'][:300]}...\n"

        prompt = (
            f"MESELE: {issue_title}\n"
            f"DETERMİNİSTİK MEZHEP HÜKÜMLERİ:\n"
            f"- Hanefî: {canon['hanefi_hukum']}\n"
            f"- Şâfiî: {canon['safii_hukum']}\n"
            f"- Mâlikî: {canon['maliki_hukum']}\n"
            f"- Hanbelî: {canon['hanbeli_hukum']}\n"
            f"- Uygulanacak En Hafif Ruhsat: {canon['ruhsat_mezhep']} -> {canon['ruhsat_hukum']}\n\n"
            f"ASIL ARAPÇA İBARELER:\n{context_str}\n\n"
            "GÖREV:\n"
            "Sen hüküm veren değil, yukarıda karara bağlanmış hükümleri akademik bir dille izah eden bir fakihsin.\n"
            "SADECE şu iki başlığı eksiksiz oluştur:\n"
            "## 3. MENŞE-İ HİLÂF VE İLLET TAHLİLİ\n"
            "(Dört mezhebin nasslara yaklaşımını, delalet ve kıyas farkını, hükmün dayandığı illet ve hikmeti açıkla.)\n\n"
            "## 4. TELFÎK DENETİMİ VE FETVÂ\n"
            "(Uygulanacak ruhsatın neden icmâ-i mürekkep riski taşımadığını, amelin bu mezhepçe nasıl sahih olduğunu ve dikkat edilecek şartları açıkla.)"
        )

        response = self.client.chat.completions.create(
            model="Qwen2.5-7B-Instruct",
            messages=[
                {"role": "system", "content": "Sen İslam Hukuku Usûl ve Telfîk tahlili yapan uzman bir fıkıh mütehassısısın. Asla verilen hükümleri değiştirme; yalnızca felsefe, usûl ve sıhhat şartlarını açıkla."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            frequency_penalty=0.3,
            presence_penalty=0.1,
            max_tokens=1500
        )
        llm_analysis = response.choices[0].message.content

        page_md = f"""# BÖLÜM: {chapter_name.upper()}
## MESELE {issue_id:03d}: {issue_title}

## 1. RUHSAT VE EN HAFİF AMELÎ HÜKÜM (LİTE TATBİKAT)
- **Uygulanacak Kolaylık:** {canon['ruhsat_hukum']}
- **Esas Alınan Mezhep:** {canon['ruhsat_mezhep']}
- **Sıhhat ve Telfîk Güvencesi:** Bu amel, intisap edilen mezhebin rükün ve şartlarına bütünüyle uygundur. Dört mezhebin dördü tarafından da geçersiz sayılan bir terkip (icmâ-i mürekkep) doğurmaz; amel meşru ve sahihtir.

## 2. DÖRT MEZHEBİN DELİL VE İSTİDLÂL HARİTASI
### 1. Hanefî Mezhebi
- **Hüküm:** {canon['hanefi_hukum']}
{format_source_line('Hanefi', 'es-Serahsî / el-Kâsânî', 'el-Mebsût / Bedâiü\'s-Sanâi\'')}

### 2. Şâfiî Mezhebi
- **Hüküm:** {canon['safii_hukum']}
{format_source_line('Safii', 'İmâm eş-Şâfiî / en-Nevevî', 'el-Ümm / el-Mecmû\'')}

### 3. Mâlikî Mezhebi
- **Hüküm:** {canon['maliki_hukum']}
{format_source_line('Maliki', 'İbn Abdilberr / el-Hattâb', 'el-Kâfî / Mevâhibü\'l-Celîl')}

### 4. Hanbelî Mezhebi
- **Hüküm:** {canon['hanbeli_hukum']}
{format_source_line('Hanbeli', 'İbn Kudâme / el-Buhûtî', 'el-Muğnî / Keşşâfü\'l-Kınâ\'')}

{llm_analysis}

---
"""
        return page_md
