import os
import re
import sqlite3
import torch
import lancedb
from sentence_transformers import SentenceTransformer

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
LANCE_PATH = os.path.join("metadata", "fikh_lancedb")
MODEL_NAME = "BAAI/bge-m3"

RE_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]")

def norm_ar(text):
    text = RE_TASHKEEL.sub("", str(text))
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    return text.strip()

class FikhHybridEngine:
    def __init__(self, db_path=DB_PATH, lance_path=LANCE_PATH, model_name=MODEL_NAME):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        self.lance_db = lancedb.connect(lance_path)
        self.tbl = self.lance_db.open_table("fikh_vectors")
        
        print(f"[*] Hibrit Motor Başlatılıyor (Donanım: {self.device.upper()})...")
        self.model = SentenceTransformer(model_name, device=self.device)
        self.model.max_seq_length = 1024
        if self.device == "cuda":
            self.model.half()

    def search_fts(self, query_str, limit=100):
        clean_q = re.sub(r'[^\w\s]', ' ', norm_ar(query_str)).strip()
        terms = [t for t in clean_q.split() if len(t) > 1]
        if not terms:
            return []
        
        fts_query = " ".join(terms)
        try:
            self.cursor.execute("""
            SELECT n.node_id, f.rank
            FROM fikh_fts f
            JOIN fikh_nodes n ON n.id = f.rowid
            WHERE fikh_fts MATCH ?
            ORDER BY f.rank
            LIMIT ?;
            """, (fts_query, limit))
            return [(row[0], idx + 1) for idx, row in enumerate(self.cursor.fetchall())]
        except Exception as e:
            return []

    def search_vector(self, query_str, limit=100):
        with torch.inference_mode():
            q_emb = self.model.encode(
                [query_str],
                normalize_embeddings=True,
                show_progress_bar=False,
                device=self.device
            )[0].tolist()
        
        res = self.tbl.search(q_emb).limit(limit).to_list()
        return [(r["node_id"], idx + 1) for idx, r in enumerate(res)]

    def hybrid_search(self, query_str, top_k_per_mezhep=1, rrf_k=60):
        fts_ranks = dict(self.search_fts(query_str, limit=150))
        vec_ranks = dict(self.search_vector(query_str, limit=150))
        
        all_node_ids = set(fts_ranks.keys()).union(set(vec_ranks.keys()))
        rrf_scores = {}
        
        for nid in all_node_ids:
            score = 0.0
            if nid in fts_ranks:
                score += 1.0 / (rrf_k + fts_ranks[nid])
            if nid in vec_ranks:
                score += 1.0 / (rrf_k + vec_ranks[nid])
            rrf_scores[nid] = score
            
        sorted_nodes = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        top_candidates = sorted_nodes[:300]
        if not top_candidates:
            return {}
            
        placeholders = ",".join(["?"] * len(top_candidates))
        id_to_score = dict(top_candidates)
        
        self.cursor.execute(f"""
        SELECT node_id, mezhep, eser, cilt, sayfa, kitab, bab, fasl, metin_orijinal
        FROM fikh_nodes
        WHERE node_id IN ({placeholders});
        """, list(id_to_score.keys()))
        
        mezhep_results = {}
        for row in self.cursor.fetchall():
            nid = row[0]
            m = row[1]
            item = {
                "node_id": nid,
                "mezhep": m,
                "eser": row[2],
                "cilt": row[3],
                "sayfa": row[4],
                "kitab": row[5],
                "bab": row[6],
                "fasl": row[7],
                "metin": row[8],
                "rrf_score": id_to_score.get(nid, 0.0)
            }
            if m not in mezhep_results:
                mezhep_results[m] = []
            mezhep_results[m].append(item)
            
        final_grouped = {}
        for m, items in mezhep_results.items():
            items_sorted = sorted(items, key=lambda x: x["rrf_score"], reverse=True)
            final_grouped[m] = items_sorted[:top_k_per_mezhep]
            
        return final_grouped

if __name__ == "__main__":
    print("=" * 80)
    print("[*] 4 HAK MEZHEP HİBRİT GETİRİM (BM25 + BGE-M3 + RRF) CANLI TESTİ")
    print("=" * 80)
    
    engine = FikhHybridEngine()
    
    test_queries = [
        ("Taharet / Niyet Şartı", "اشتراط النية في صحة الوضوء"),
        ("Muamelat / Borcun Borçla Satışı", "نهى عن بيع الكالئ بالكالئ الدين بالدين")
    ]
    
    for baslik, q in test_queries:
        print("\n" + "#" * 80)
        print(f"[?] MESELE: {baslik}")
        print(f"[?] ARAPÇA SORGU: '{q}'")
        print("#" * 80)
        
        results = engine.hybrid_search(q, top_k_per_mezhep=1)
        
        for m in ["Hanefi", "Maliki", "Safii", "Hanbeli", "Mukaren"]:
            if m in results and results[m]:
                r = results[m][0]
                print(f"[{r['mezhep'].upper()}] -> {r['eser']} (Cilt: {r['cilt']}, Sayfa: {r['sayfa']}) | RRF Puanı: {r['rrf_score']:.5f}")
                print(f"Bölüm  : {r['kitab']} / {r['bab']}")
                snippet = " ".join(r["metin"].split()[:32])
                print(f"Metin  : {snippet}...\n")
            else:
                print(f"[{m.upper()}] -> Eşleşme bulunamadı.\n")
