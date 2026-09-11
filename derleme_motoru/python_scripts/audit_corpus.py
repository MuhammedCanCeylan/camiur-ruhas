import os
import json

PROCESSED_DIR = "processed"
FILES = [
    "bidayat_al_mujtahid_refined.json",
    "hanefi_nodes.json",
    "safii_nodes.json",
    "maliki_nodes.json",
    "hanbeli_nodes.json"
]

print("=" * 75)
print(f"{'DOSYA':<30} | {'DUGUM':<6} | {'ORT. KARAKTER':<14} | {'KITAB %':<8} | {'BAB %':<8}")
print("=" * 75)

for fname in FILES:
    fpath = os.path.join(PROCESSED_DIR, fname)
    if not os.path.exists(fpath):
        continue
    
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    total = len(data)
    avg_len = sum(len(n.get("metin_orijinal", "")) for n in data) / total if total else 0
    has_kitab = sum(1 for n in data if n.get("kitab") and n.get("kitab") not in ["Giriş", ""])
    has_bab = sum(1 for n in data if n.get("bab") and n.get("bab") not in ["Genel", ""])
    
    k_pct = (has_kitab / total) * 100 if total else 0
    b_pct = (has_bab / total) * 100 if total else 0
    
    print(f"{fname:<30} | {total:<6} | {avg_len:<14.1f} | %{k_pct:<7.1f} | %{b_pct:<7.1f}")

print("=" * 75)