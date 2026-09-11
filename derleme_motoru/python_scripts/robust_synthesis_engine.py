import os
import re
import sqlite3
import torch
import lancedb
from sentence_transformers import SentenceTransformer

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
LANCE_PATH = os.path.join("metadata", "fikh_lancedb")
MODEL_NAME = "BAAI/bge-m3"

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

class RobustFikhSynthesisEngine:
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

    def determine_exact_hukum(self, text):
        clean_t = text[:300]
        # 1. Açık Yasak / Fesat / Butlan (Öncelikli)
        if re.search(r"(نهى رسول|نهى النبي|لا يجوز|لا يحل|حرام|يحرم|باطل|فاسد|فساد|بطلان|لا صحة|لا يجزئ)", clean_t):
            return "Batil_Fasit" if re.search(r"(باطل|فاسد|فساد|بطلان)", clean_t) else "Haram"
        
        # 2. Şartın Reddi (Hanefî niyet istisnası: 'ليس بشرط', 'يتأدى بدون نية')
        if re.search(r"(ليس بشرط|بدون النية|غير مفتقر إلى النية|سقوط|يجزئ بغير نية)", clean_t):
            return "Caiz_Mubah"
            
        # 3. Şart ve Rükün Vurgusu
        if re.search(r"(شرط لصحة|ركن|فرض|واجب|لا بد منه|يجب|أوجب)", clean_t):
            return "Farz_Vacip"
            
        # 4. Sünnet / Müstehap
        if re.search(r"(سنة|مستحب|مندوب|الأفضل|ندب)", clean_t):
            return "Sunnet_Mustehap"
            
        # 5. Açık Cevaz
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
            q_emb = self.model.encode([query_str], normalize_embeddings=True, show_progress_bar=False, device=self.device)[0].tolist()
        vec_res = self.tbl.search(q_emb).limit(limit).to_list()
        vec_ranks = {r["node_id"]: idx + 1 for idx, r in enumerate(vec_res)}

        all_ids = set(fts_ranks.keys()).union(set(vec_ranks.keys()))
        rrf_scores = {nid: (1.0 / (rrf_k + fts_ranks.get(nid, 999))) + (1.0 / (rrf_k + vec_ranks.get(nid, 999))) for nid in all_ids}
        return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:150]

    def synthesize(self, query_str):
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

        # İcmâ ve Hilaf Tespiti
        valid_mezhepler = [d for m, d in mezhep_data.items() if m in ["Hanefi", "Maliki", "Safii", "Hanbeli"] and d["hukum"] != "Bilinmiyor"]
        all_forbidden = all(d["hukum"] in ["Haram", "Batil_Fasit"] for d in valid_mezhepler) if valid_mezhepler else False
        all_obligatory = all(d["hukum"] in ["Farz_Vacip", "Sart_Rukun"] for d in valid_mezhepler) if valid_mezhepler else False

        telfik_caiz_list = [d for d in valid_mezhepler if d["puan"] <= 2]
        
        return {
            "query": query_str,
            "mezhep_data": mezhep_data,
            "is_icma_forbidden": all_forbidden,
            "is_icma_obligatory": all_obligatory,
            "telfik_adaylari": sorted(telfik_caiz_list, key=lambda x: x["puan"]),
            "en_ihtiyatli": sorted(valid_mezhepler, key=lambda x: x["puan"], reverse=True)[0] if valid_mezhepler else None
        }

if __name__ == "__main__":
    print("=" * 80)
    print("[*] GÜVENLİK DUVARLI TELFÎK VE İCMÂ SENTEZ TESTİ")
    print("=" * 80)

    engine = RobustFikhSynthesisEngine()

    testler = [
        "اشتراط النية في صحة الوضوء والطهارة",
        "نهى عن بيع الكالئ بالكالئ بيع الدين بالدين"
    ]

    for q in testler:
        print("\n" + "#" * 80)
        print(f"[?] MESELE: {q}")
        print("#" * 80)

        res = engine.synthesize(q)
        if not res:
            continue

        for m in ["Hanefi", "Maliki", "Safii", "Hanbeli", "Mukaren"]:
            if m in res["mezhep_data"]:
                d = res["mezhep_data"][m]
                print(f"[{m.upper():<7}] {d['muellif']} - {d['eser']} (C:{d['cilt']}, S:{d['sayfa']})")
                print(f"         Tespit Edilen Hüküm: {d['hukum']}")
                snip = " ".join(d["metin"].split()[:25])
                print(f"         Metin: {snip}...\n")

        print("=" * 80)
        print("[*] NİHAİ SENTEZ VE TELFÎK RAPORU:")
        print("=" * 80)

        if res["is_icma_forbidden"]:
            print("[!] İCMÂ TESPİT EDİLDİ: Dört mezhebin ittifakıyla bu işlem HARAM / BÂTILDIR.")
            print("    -> Telfîk (kolaylık seçimi) YAPILAMAZ. Çünkü hiçbir hak mezhepte cevaz yoktur.")
        elif res["telfik_adaylari"]:
            t = res["telfik_adaylari"][0]
            print(f"[+] MEŞRU TELFÎK / RUHSAT GÖRÜŞÜ BULUNDU:")
            print(f"    - Tercih Edilen Mezhep : {t['mezhep'].upper()} ({t['muellif']})")
            print(f"    - Ruhsat Hükmü         : {t['hukum']}")
            print(f"    - Delil Dayanağı       : {t['eser']} (Cilt: {t['cilt']}, Sayfa: {t['sayfa']})")
            print(f"    - Uygulama Esası       : Meselede hilaf mevcuttur. 4 mezhepten en az biri ({t['mezhep']})")
            print(f"                             cevaz verdiğinden meşakkat halinde bu ruhsatla amel caizdir.")
        else:
            print("[-] Bu meselede cevaz/ruhsat veren açık bir mezhep kavli tespit edilemedi.")

        if res["en_ihtiyatli"]:
            iht = res["en_ihtiyatli"]
            print(f"\n[+] AZÎMET / İHTİYAT GÖRÜŞÜ:")
            print(f"    - En Sıkı / İhtiyatlı  : {iht['mezhep'].upper()} ({iht['muellif']}) -> {iht['hukum']}")
            print(f"    - Tavsiye              : İbadetin sıhhatini riske atmamak için bu görüş esas alınmalıdır.")
        print("=" * 80)
