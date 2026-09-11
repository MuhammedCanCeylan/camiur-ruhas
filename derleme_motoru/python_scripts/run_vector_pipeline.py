import os
import sqlite3
import torch
import lancedb
import pyarrow as pa
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

DB_PATH = os.path.join("metadata", "fikh_corpus.db")
LANCE_PATH = os.path.join("metadata", "fikh_lancedb")
MODEL_NAME = "BAAI/bge-m3"
BATCH_SIZE = 64  # RTX 4060 8GB VRAM icin optimize batch

assert torch.cuda.is_available(), "[-] HATA: CUDA bulunamadi!"
device = "cuda"
gpu_name = torch.cuda.get_device_name(0)

print("=" * 75)
print(f"[*] GPU AKTIF : {gpu_name}")
print(f"[*] VRAM      : {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB | Mod: FP16 Tensor Core")
print("=" * 75)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM fikh_nodes WHERE is_embedded = 0;")
remaining_nodes = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM fikh_nodes WHERE is_embedded = 1;")
completed_nodes = cursor.fetchone()[0]

print(f"[*] Onceden Islenen : {completed_nodes:,}")
print(f"[*] Bekleyen Düğüm  : {remaining_nodes:,}")

# LanceDB Tablo Bağlantısı (Try-Except ile Kesin Çözüm)
db = lancedb.connect(LANCE_PATH)

schema = pa.schema([
    pa.field("node_id", pa.string()),
    pa.field("mezhep", pa.string()),
    pa.field("eser", pa.string()),
    pa.field("cilt", pa.string()),
    pa.field("sayfa", pa.string()),
    pa.field("kanonik_konu", pa.string()),
    pa.field("kitab", pa.string()),
    pa.field("bab", pa.string()),
    pa.field("fasl", pa.string()),
    pa.field("metin_orijinal", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), 1024))
])

try:
    tbl = db.open_table("fikh_vectors")
    print(f"[+] Mevcut 'fikh_vectors' tablosuna baglanildi. Kayit Sayisi: {len(tbl):,}")
except Exception:
    tbl = db.create_table("fikh_vectors", schema=schema)
    print(f"[+] 'fikh_vectors' tablosu sifirdan olusturuldu.")

print(f"\n[*] Model GPU bellegine yukleniyor: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME, device=device)
model.max_seq_length = 1024
model.half()  # FP16 Tensor Core

if remaining_nodes > 0:
    print(f"[*] GPU tabanli vektorlestirme baslatildi (Batch: {BATCH_SIZE})...\n")
    pbar = tqdm(total=remaining_nodes, desc="GPU Embedding", unit="node")

    while True:
        cursor.execute("""
        SELECT id, node_id, mezhep, eser, cilt, sayfa, kanonik_konu, kitab, bab, fasl, metin_arama, metin_orijinal
        FROM fikh_nodes
        WHERE is_embedded = 0
        ORDER BY id ASC
        LIMIT ?;
        """, (BATCH_SIZE,))

        rows = cursor.fetchall()
        if not rows:
            break

        row_ids = [r[0] for r in rows]
        texts = [r[10] if r[10] else r[11] for r in rows]

        with torch.inference_mode():
            embeddings = model.encode(
                texts,
                batch_size=len(texts),
                normalize_embeddings=True,
                show_progress_bar=False,
                device=device
            )

        records = [{
            "node_id": r[1],
            "mezhep": r[2],
            "eser": r[3],
            "cilt": r[4],
            "sayfa": r[5],
            "kanonik_konu": r[6],
            "kitab": r[7],
            "bab": r[8],
            "fasl": r[9],
            "metin_orijinal": r[11],
            "vector": emb.tolist()
        } for r, emb in zip(rows, embeddings)]

        tbl.add(records)
        cursor.executemany("UPDATE fikh_nodes SET is_embedded = 1 WHERE id = ?;", [(rid,) for rid in row_ids])
        conn.commit()

        pbar.update(len(rows))

    pbar.close()

conn.close()
print("\n" + "=" * 75)
print(f"[+] VEKTORLESTIRME BITTI. LanceDB Toplam Vektor: {len(tbl):,}")
print("=" * 75)
