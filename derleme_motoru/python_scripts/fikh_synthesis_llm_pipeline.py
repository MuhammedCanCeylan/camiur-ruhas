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

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
LANCE_PATH = os.path.join("metadata", "fikh_lancedb")
MODEL_NAME = "BAAI/bge-m3"

SERVER_EXE = r"D:\fikh_models\llama_bin\llama-server.exe"
GGUF_PATH = r"D:\fikh_models\Qwen2.5-7B-Instruct-Q4_K_M.gguf"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8080

HUKUM_KOLAYLIK_PUANI = {
    "Caiz_Mubah": 1,
    "Sunnet_Mustehap": 2,
    "Mekruh": 3,
    "Farz_Vacip": 4,
    "Sart_Rukun": 4,
    "Haram": 5,
    "Batil_Fasit": 5,
    "Bilinmiyor": 99
}

def is_server_running(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0

def ensure_llama_server():
    if is_server_running(SERVER_HOST, SERVER_PORT):
        print(f"[+] llama-server zaten aktif: http://{SERVER_HOST}:{SERVER_PORT}")
        return

    print(f"[*] llama-server kapalı tespit edildi. GPU üzerinde arka planda başlatılıyor...")
    if not os.path.exists(SERVER_EXE) or not os.path.exists(GGUF_PATH):
        print(f"[-] HATA: Sunucu veya model dosyası bulunamadı:\n    {SERVER_EXE}\n    {GGUF_PATH}")
        sys.exit(1)

    cmd = [
        SERVER_EXE,
        "-m", GGUF_PATH,
        "-ngl", "99",
        "-c", "4096",
        "--port", str(SERVER_PORT),
        "--host", SERVER_HOST
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[*] Sunucunun hazır olması bekleniyor (VRAM yüklemesi)...", end="", flush=True)
    for _ in range(40):
        time.sleep(1)
        print(".", end="", flush=True)
        if is_server_running(SERVER_HOST, SERVER_PORT):
            print("\n[+] llama-server başarıyla bağlandı.")
            return
    print("\n[-] HATA: llama-server zaman aşımına uğradı!")
    sys.exit(1)

class StrictFikhRagPipeline:
    def __init__(self):
        ensure_llama_server()
        
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

    def determine_exact_hukum(self, text):
        clean_t = text[:350]
        if re.search(r"(نهى رسول|نهى النبي|لا يجوز|لا يحل|حرام|يحرم|باطل|فاسد|فساد|بطلان|لا صحة|لا يجزئ)", clean_t):
            return "Batil_Fasit" if re.search(r"(باطل|فاسد|فساد|بطلان)", clean_t) else "Haram"
        if re.search(r"(ليس بشرط|بدون النية|غير مفتقر إلى النية|سقوط|يجزئ بغير نية)", clean_t):
            return "Caiz_Mubah"
        if re.search(r"(شرط لصحة|ركن|فرض|واجب|لا بد منه|يجب|أوجب)", clean_t):
            return "Farz_Vacip"
        if re.search(r"(سنة|مستحب|مندوب|الأفضل|ندب)", clean_t):
            return "Sunnet_Mustehap"
        if re.search(r"(يجوز|جائز|يباح|مباح|لا بأس|أجزأ)", clean_t):
            return "Caiz_Mubah"
        return "Bilinmiyor"

    def retrieve_hybrid(self, query_str, limit=100, rrf_k=60):
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
        return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:150]

    def build_structured_context(self, query_str):
        candidates = self.retrieve_hybrid(query_str)
        if not candidates:
            return None

        node_ids = [c[0] for c in candidates]
        placeholders = ",".join(["?"] * len(node_ids))

        self.cur.execute(f"""
        SELECT node_id, mezhep, muellif, eser, cilt, sayfa, kitab, bab, metin_orijinal
        FROM fikh_nodes
        WHERE node_id IN ({placeholders});
        """, node_ids)
        nodes_map = {r[0]: r for r in self.cur.fetchall()}

        mezhep_data = {}
        for nid, score in candidates:
            if nid not in nodes_map:
                continue
            row = nodes_map[nid]
            m = row[1]
            if m not in mezhep_data:
                h_exact = self.determine_exact_hukum(row[8])
                mezhep_data[m] = {
                    "node_id": nid,
                    "mezhep": m,
                    "muellif": row[2],
                    "eser": row[3],
                    "cilt": row[4],
                    "sayfa": row[5],
                    "kitab": row[6],
                    "bab": row[7],
                    "metin": row[8],
                    "hukum": h_exact,
                    "puan": HUKUM_KOLAYLIK_PUANI.get(h_exact, 99)
                }

        valid_mezhepler = [d for m, d in mezhep_data.items() if m in ["Hanefi", "Maliki", "Safii", "Hanbeli"] and d["hukum"] != "Bilinmiyor"]
        all_forbidden = all(d["hukum"] in ["Haram", "Batil_Fasit"] for d in valid_mezhepler) if len(valid_mezhepler) >= 3 else False
        telfik_caiz_list = [d for d in valid_mezhepler if d["puan"] <= 2]

        return {
            "query": query_str,
            "mezhep_data": mezhep_data,
            "is_icma_forbidden": all_forbidden,
            "telfik": sorted(telfik_caiz_list, key=lambda x: x["puan"])[0] if telfik_caiz_list else None,
            "azimet": sorted(valid_mezhepler, key=lambda x: x["puan"], reverse=True)[0] if valid_mezhepler else None
        }

    def generate_synthesis(self, query_str):
        ctx = self.build_structured_context(query_str)
        if not ctx:
            return "[-] Yeterli bağlam getirilemedi."

        context_blocks = []
        for m in ["Hanefi", "Maliki", "Safii", "Hanbeli", "Mukaren"]:
            if m in ctx["mezhep_data"]:
                d = ctx["mezhep_data"][m]
                context_blocks.append(
                    f"[{m.upper()}]\n"
                    f"Kaynak: {d['muellif']} - {d['eser']} (C:{d['cilt']}, S:{d['sayfa']})\n"
                    f"Hüküm Kodu: {d['hukum']}\n"
                    f"Metin Parçası: {d['metin'][:300]}...\n"
                )

        system_instruction = (
            "Sen uzman bir Mukayeseli İslam Hukuku (Fıkh-ı Mukāren) akademisyenisin.\n"
            "GÖREVİN: Verilen kaynak metinlere tam sadakatle akademik bir fıkıh tahlili yazmaktır.\n"
            "KESİN KURALLAR:\n"
            "1. Asla uydurma terim üretme. غسل = yıkamak, مسح = meshetmek, طهارة = taharet/abdest, نية = niyet, ربا = faiz.\n"
            "2. Asla aynı cümleyi veya kelimeleri tekrar etme (döngüye girme).\n"
            "3. Çıktıyı MUTLAKA şu 4 başlık altında düzenle:\n"
            "   ## 1. Mesele ve İcmâ Durumu\n"
            "   ## 2. Dört Mezhebin Hüküm Özeti\n"
            "   ## 3. Telfîk ve Ruhsat Hükmü (Varsa en kolay mezhep ve delili; İcmâ varsa 'Telfîk Câiz Değildir' yaz)\n"
            "   ## 4. Azîmet ve İhtiyat Hükmü (Ameli şüpheden kurtaran en sağlam hüküm)"
        )

        user_content = (
            f"MESELE: {query_str}\n\n"
            f"KAYNAK METİNLER:\n" + "\n".join(context_blocks) + "\n"
            f"ALGORİTMA TESPİTİ:\n"
            f"- İcmâen Yasak/Haram mı: {'EVET' if ctx['is_icma_forbidden'] else 'HAYIR (Hilâf Var)'}\n"
            f"- Ruhsat Mezhebi: {ctx['telfik']['mezhep'] if ctx['telfik'] else 'Yok'}\n"
            f"- Azîmet Mezhebi: {ctx['azimet']['mezhep'] if ctx['azimet'] else 'Yok'}\n\n"
            f"Yukarıdaki kaynak ve tespitlere göre 4 başlığı doldurarak sentezini oluştur."
        )

        response = self.client.chat.completions.create(
            model="Qwen2.5-7B-Instruct",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2,
            frequency_penalty=0.5,
            presence_penalty=0.3,
            max_tokens=900
        )

        return response.choices[0].message.content

if __name__ == "__main__":
    print("=" * 80)
    print("[*] FAZ 3: STRICT RAG YEREL LLM SENTEZ BORU HATTI (OTOMATİK SUNUCU DESTEKLİ)")
    print("=" * 80)

    pipe = StrictFikhRagPipeline()

    testler = [
        "اشتراط النية في صحة الوضوء والطهارة",
        "نهى عن بيع الكالئ بالكالئ بيع الدين بالدين"
    ]

    for q in testler:
        print("\n" + "#" * 80)
        print(f"[?] MESELE: {q}")
        print("#" * 80)
        sentez = pipe.generate_synthesis(q)
        print("\n" + sentez + "\n")
