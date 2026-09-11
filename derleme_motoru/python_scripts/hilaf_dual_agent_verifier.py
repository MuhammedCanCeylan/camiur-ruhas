import os
import re
import sys
import json
import time
import socket
import sqlite3
import subprocess
import torch
import lancedb
from sentence_transformers import SentenceTransformer
from openai import OpenAI

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
LANCE_PATH = os.path.join("metadata", "fikh_lancedb")
INPUT_MATRIX = os.path.join("D:\\fikh_kitap", "fikh_hilaf_matrix.json")
OUTPUT_VERIFIED = os.path.join("D:\\fikh_kitap", "fikh_verified_canon.json")
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

class DualAgentFikhVerifier:
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

    def retrieve_context(self, query_str, limit=80, rrf_k=60):
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
        top_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:80]

        node_ids = [c[0] for c in top_candidates]
        if not node_ids:
            return {}
        placeholders = ",".join(["?"] * len(node_ids))

        self.cur.execute(f"""
        SELECT node_id, mezhep, muellif, eser, cilt, sayfa, metin_orijinal
        FROM fikh_nodes
        WHERE node_id IN ({placeholders});
        """, node_ids)
        nodes_map = {r[0]: r for r in self.cur.fetchall()}

        dossier = {}
        for nid, score in top_candidates:
            if nid not in nodes_map:
                continue
            row = nodes_map[nid]
            m = row[1]
            if m not in dossier:
                dossier[m] = {
                    "mezhep": m,
                    "muellif": row[2],
                    "eser": row[3],
                    "cilt": row[4],
                    "sayfa": row[5],
                    "metin": row[6]
                }
        return dossier

    def agent_a_extract(self, issue_title, dossier):
        context_str = ""
        for m, d in dossier.items():
            context_str += f"[{m}] {d['muellif']} - {d['eser']}: {d['metin'][:350]}...\n"

        system_prompt = (
            "Sen 4 hak mezhebin metinlerini inceleyen objektif bir müstahricsin (Ajan A).\n"
            "GÖREV: Sunulan Arapça fıkıh metinlerinden 4 mezhebin görüşlerini ve EN HAFİF RUHSATI çıkarıp saf JSON üretmektir.\n"
            "KURAL: JSON dışında hiçbir metin, markdown, selamlama veya açıklama yazma. Format tam olarak şudur:\n"
            "{\n"
            '  "ruhsat_mezhep": "En hafif ve caiz gören mezhep",\n'
            '  "ruhsat_hukum": "Kişinin amelini en çok kolaylaştıran kesin serbestlik/hafiflik hükmü",\n'
            '  "hanefi_hukum": "Hanefî mezhebinin net hükmü",\n'
            '  "safii_hukum": "Şâfiî mezhebinin net hükmü",\n'
            '  "maliki_hukum": "Mâlikî mezhebinin net hükmü",\n'
            '  "hanbeli_hukum": "Hanbelî mezhebinin net hükmü"\n'
            "}"
        )

        user_prompt = f"MESELE: {issue_title}\n\nKORPUSTAN METİNLER:\n{context_str}\n\nSaf JSON üret:"

        resp = self.client.chat.completions.create(
            model="Qwen2.5-7B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=600
        )
        content = resp.choices[0].message.content.strip()
        
        # JSON bloğunu ayıkla
        m = re.search(r"\{[\s\S]*\}", content)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

    def agent_b_audit(self, issue_title, extracted_json, dossier):
        """Müfettiş Ajan: Arapça metin ile çıkarılan Türkçe hükümleri mantıksal ve lafzen denetler."""
        if not extracted_json:
            return False, "JSON formatı geçersiz"

        # Otomatik Kural Tabanlı Assert Denetimi (Deterministic Regex Check)
        for m_name, field in [("Hanefi", "hanefi_hukum"), ("Safii", "safii_hukum"), ("Maliki", "maliki_hukum"), ("Hanbeli", "hanbeli_hukum")]:
            if m_name in dossier:
                raw_ar = dossier[m_name]["metin"]
                h_tr = extracted_json.get(field, "").lower()

                # 'Bozmaz' lafzı iddia edilmişken metinde kat'i 'bozar' (ينقض / يجب) edatsız geçiyor mu?
                if "bozmaz" in h_tr and ("لا ينقض" not in raw_ar and "ليس بحدث" not in raw_ar and "لا وضوء" not in raw_ar and "لا يفسد" not in raw_ar):
                    # Şüpheli durum: Arapçada olumsuzluk edatı görünmüyor
                    if "ينقض" in raw_ar or "يجب الوضوء" in raw_ar:
                        return False, f"{m_name} metninde olumsuzluk edatı olmadan 'ينقض/يجب' geçiyor, Türkçe 'bozmaz' yazılmış (Tersinme Şüphesi)."

        # LLM Müfettiş Denetimi
        audit_prompt = (
            f"MESELE: {issue_title}\n"
            f"AJAN A'NIN ÇIKARDIĞI HÜKÜMLER:\n{json.dumps(extracted_json, ensure_ascii=False, indent=2)}\n\n"
            "GÖREV: Bu hükümlerde mezhep karıştırması (Örn: Şâfiî'ye Hanefî görüşü yazılması), "
            "hükmün ters yazılması (bozana bozmaz denmesi) veya telfîk-i bâtıl var mı?\n"
            "Cevabını SADECE şu formatta ver:\n"
            "DURUM: ONAYLANDI veya DURUM: REDDET - [Sebep]"
        )

        resp = self.client.chat.completions.create(
            model="Qwen2.5-7B-Instruct",
            messages=[
                {"role": "system", "content": "Sen hata affetmeyen bir Fıkıh Müfettişisin. Görevin Ajan A'nın çıkarımlarındaki mantık ve nakil hatalarını bulmaktır."},
                {"role": "user", "content": audit_prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        verdict = resp.choices[0].message.content.strip()
        if "ONAYLANDI" in verdict.upper():
            return True, "Doğrulandı"
        return False, verdict

if __name__ == "__main__":
    print("=" * 80)
    print("[*] ÇİFT AJANLI FIKIH DOĞRULAMA MOTORU (MAKER - CHECKER)")
    print("=" * 80)

    if not os.path.exists(INPUT_MATRIX):
        print("[-] İhtilaf matrisi bulunamadı. Önce discover_hilaf_matrix.py çalıştırılmalı.")
        sys.exit(1)

    with open(INPUT_MATRIX, "r", encoding="utf-8") as f:
        matrix = json.load(f)

    verifier = DualAgentFikhVerifier()
    
    verified_list = []
    if os.path.exists(OUTPUT_VERIFIED):
        try:
            with open(OUTPUT_VERIFIED, "r", encoding="utf-8") as f:
                verified_list = json.load(f)
        except Exception:
            verified_list = []

    verified_indices = {item["index"] for item in verified_list}
    print(f"[+] Zaten doğrulanmış düğüm sayısı: {len(verified_indices)}")

    # İlk etapta test için 10 düğüm üzerinde çalıştır
    test_batch = [node for node in matrix if node["index"] not in verified_indices][:10]
    print(f"[*] İşlenecek test grubu boyutu: {len(test_batch)} düğüm\n")

    for node in test_batch:
        idx = node["index"]
        title = f"{node['kitab']} - {node['bab']}"
        print(f"--> [{idx:03d}] Tahrîc ve Denetim: {title}...")

        dossier = verifier.retrieve_context(f"{node['kitab']} {node['bab']}")
        if len(dossier) < 2:
            print(f"    [-] Korpusta yeterli mezhep metni bulunamadı ({len(dossier)} mezhep). Atlandı.")
            continue

        # 1. Aşama: Müstahric Ajan
        extracted = verifier.agent_a_extract(title, dossier)
        if not extracted:
            print("    [-] Ajan A geçerli JSON üretemedi.")
            continue

        # 2. Aşama: Müfettiş Ajan
        is_valid, reason = verifier.agent_b_audit(title, extracted, dossier)
        if is_valid:
            print(f"    [✓] MÜFETTİŞ ONAYLADI (Sıfır Hata).")
            verified_list.append({
                "index": idx,
                "kitab": node["kitab"],
                "bab": node["bab"],
                "canon": extracted
            })
            with open(OUTPUT_VERIFIED, "w", encoding="utf-8") as f:
                json.dump(verified_list, f, ensure_ascii=False, indent=2)
        else:
            print(f"    [X] MÜFETTİŞ REDDETTİ: {reason}")

    print("\n" + "=" * 80)
    print(f"[+] Denetim tamamlandı. Geçerli düğümler: {OUTPUT_VERIFIED}")
    print("=" * 80)
