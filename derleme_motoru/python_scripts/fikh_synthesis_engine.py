import os
import re
import sqlite3
import torch
import lancedb
from sentence_transformers import SentenceTransformer

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
LANCE_PATH = os.path.join("metadata", "fikh_lancedb")
MODEL_NAME = "BAAI/bge-m3"

# Hüküm Kolaylık Skalası (Düşük puan = Daha kolay / Ruhsat)
HUKUM_KOLAYLIK_PUANI = {
    "Caiz_Mubah": 1,
    "Sunnet_Mustehap": 2,
    "Mekruh": 3,
    "Farz_Vacip": 4,
    "Sart_Rukun": 4,
    "Haram": 5,
    "Batil_Fasit": 5
}

class FikhSynthesisEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()
        
        self.lance_db = lancedb.connect(LANCE_PATH)
        self.tbl = self.lance_db.open_table("fikh_vectors")
        
        self.model = SentenceTransformer(MODEL_NAME, device=self.device)
        self.model.max_seq_length = 1024
        if self.device == "cuda":
            self.model.half()

    def retrieve_hybrid_pool(self, query_str, limit=120, rrf_k=60):
        # 1. FTS5 (Kök ve Lafız Taraması)
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

        # 2. Vector (LanceDB)
        with torch.inference_mode():
            q_emb = self.model.encode([query_str], normalize_embeddings=True, show_progress_bar=False, device=self.device)[0].tolist()
        vec_res = self.tbl.search(q_emb).limit(limit).to_list()
        vec_ranks = {r["node_id"]: idx + 1 for idx, r in enumerate(vec_res)}

        # 3. RRF Birleşimi
        all_ids = set(fts_ranks.keys()).union(set(vec_ranks.keys()))
        rrf_scores = {nid: (1.0 / (rrf_k + fts_ranks.get(nid, 999))) + (1.0 / (rrf_k + vec_ranks.get(nid, 999))) for nid in all_ids}
        return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:150]

    def synthesize_issue(self, query_str):
        candidates = self.retrieve_hybrid_pool(query_str)
        if not candidates:
            return None

        node_ids = [c[0] for c in candidates]
        placeholders = ",".join(["?"] * len(node_ids))

        # Düğüm üstverileri
        self.cur.execute(f"""
        SELECT node_id, mezhep, muellif, eser, cilt, sayfa, kitab, bab, metin_orijinal
        FROM fikh_nodes
        WHERE node_id IN ({placeholders});
        """, node_ids)
        nodes_map = {r[0]: r for r in self.cur.fetchall()}

        # Bilgi grafı ilişkileri
        self.cur.execute(f"""
        SELECT node_id, hukum, delil_turu, illet_snippet
        FROM graph_relations
        WHERE node_id IN ({placeholders});
        """, node_ids)
        rels_map = {}
        for nid, h, d, ill in self.cur.fetchall():
            rels_map.setdefault(nid, []).append({"hukum": h, "delil": d, "illet": ill})

        # 4 Mezhep + Mukāren filtreleme
        mezhep_data = {}
        for nid, score in candidates:
            if nid not in nodes_map:
                continue
            row = nodes_map[nid]
            m = row[1]
            if m not in mezhep_data:
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
                    "rrf_score": score,
                    "iliskiler": rels_map.get(nid, [])
                }

        # Telfîk (En Kolay / Ruhsat) ve Azîmet (En İhtiyatlı) Analizi
        mezhep_hukumleri = []
        for m_name in ["Hanefi", "Maliki", "Safii", "Hanbeli"]:
            if m_name in mezhep_data:
                item = mezhep_data[m_name]
                detected_h = item["iliskiler"][0]["hukum"] if item["iliskiler"] else "Caiz_Mubah"
                score = HUKUM_KOLAYLIK_PUANI.get(detected_h, 3)
                mezhep_hukumleri.append({
                    "mezhep": m_name,
                    "muellif": item["muellif"],
                    "eser": item["eser"],
                    "hukum": detected_h,
                    "puan": score,
                    "item": item
                })

        # Kolaylık sıralaması (Min Score = En Kolay)
        mezhep_hukumleri_sorted = sorted(mezhep_hukumleri, key=lambda x: x["puan"])
        telfik_secimi = mezhep_hukumleri_sorted[0] if mezhep_hukumleri_sorted else None
        azimet_secimi = mezhep_hukumleri_sorted[-1] if mezhep_hukumleri_sorted else None

        return {
            "query": query_str,
            "mezhep_data": mezhep_data,
            "telfik_ruhsat": telfik_secimi,
            "azimet_ihtiyat": azimet_secimi
        }

if __name__ == "__main__":
    print("=" * 80)
    print("[*] FAZ 3: TELFÎK VE GRAPH-RAG MUKĀREN SENTEZ MOTORU")
    print("=" * 80)

    engine = FikhSynthesisEngine()

    test_meseleleri = [
        "اشتراط النية في الوضوء",
        "نهى عن بيع الكالئ بالكالئ وبيع الدين بالدين"
    ]

    for q in test_meseleleri:
        print("\n" + "#" * 80)
        print(f"[?] MESELE: {q}")
        print("#" * 80)

        out = engine.synthesize_issue(q)
        if not out:
            print("[-] Sonuç bulunamadı.")
            continue

        print("\n--- 4 MEZHEBİN GÖRÜŞ VE HÜKÜM DAĞILIMI ---")
        for m in ["Hanefi", "Maliki", "Safii", "Hanbeli", "Mukaren"]:
            if m in out["mezhep_data"]:
                d = out["mezhep_data"][m]
                h = d["iliskiler"][0]["hukum"] if d["iliskiler"] else "Mesele içi içtihat"
                delil = d["iliskiler"][0]["delil"] if d["iliskiler"] else "Kıyas"
                print(f"[{m.upper():<7}] {d['muellif']} - {d['eser']} (C:{d['cilt']}, S:{d['sayfa']})")
                print(f"         Hüküm: {h:<16} | Asli Delil: {delil}")
                snippet = " ".join(d["metin"].split()[:25])
                print(f"         İbâre: {snippet}...\n")

        print("=" * 80)
        print("[*] NİHAİ MUKĀREN SENTEZ KARARI:")
        print("=" * 80)
        
        t = out["telfik_ruhsat"]
        if t:
            print(f"1. TELFÎK / RUHSAT GÖRÜŞÜ (En Kolay / İzin Veren İçtihat):")
            print(f"   - Tercih Edilen Mezhep : {t['mezhep'].upper()} ({t['muellif']})")
            print(f"   - Esas Alınan Hüküm    : {t['hukum']} (Kolaylık Derecesi: {t['puan']}/5)")
            print(f"   - Uygulama Mantığı     : 4 mezhepten en az biri ({t['mezhep']}) bu amele cevaz vermiştir.")
            print(f"                            Meşakkat, unutma veya ihtiyaç halinde bu ruhsatla amel edilir.\n")

        a = out["azimet_ihtiyat"]
        if a:
            print(f"2. AZÎMET / İHTİYAT GÖRÜŞÜ (Şüpheden Uzak / İttifak Zemini):")
            print(f"   - Esas Alınan Mezhep   : {a['mezhep'].upper()} ({a['muellif']})")
            print(f"   - İhtiyat Hükmü        : {a['hukum']} (Bağlayıcılık Derecesi: {a['puan']}/5)")
            print(f"   - Uygulama Mantığı     : İbadetin 4 mezhep nezdinde ittifakla sahih olması için bu şart gözetilir.")
        print("=" * 80)
