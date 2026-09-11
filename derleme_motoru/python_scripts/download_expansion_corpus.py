import os
import sys
import requests
from tqdm import tqdm

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
RAW_DIR = "raw"
os.makedirs(RAW_DIR, exist_ok=True)

EXPANSION_TARGETS = [
    {
        "mezhep": "Safii",
        "eser": "el_Umm",
        "repo": "0225AH",
        "author_key": "Shafii",
        "book_key": "Umm",
        "out_file": os.path.join(RAW_DIR, "safii_umm_raw.txt")
    },
    {
        "mezhep": "Maliki",
        "eser": "el_Mudawwana",
        "repo": "0250AH",
        "author_key": "Sahnun",
        "book_key": "Mudawwana",
        "out_file": os.path.join(RAW_DIR, "maliki_mudawwana_raw.txt")
    },
    {
        "mezhep": "Hanefi",
        "eser": "el_Mabsut",
        "repo": "0500AH",
        "author_key": "Sarakhsi",
        "book_key": "Mabsut",
        "out_file": os.path.join(RAW_DIR, "hanefi_mabsut_raw.txt")
    }
]

def find_remote_file(repo, author_key, book_key):
    api_url = f"https://api.github.com/repos/OpenITI/{repo}/contents/data"
    try:
        r = requests.get(api_url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return None
        
        author_dir = None
        for item in r.json():
            if author_key.lower() in item.get("name", "").lower():
                author_dir = item["name"]
                break
        
        if not author_dir:
            return None

        r_books = requests.get(f"{api_url}/{author_dir}", headers=HEADERS, timeout=20)
        if r_books.status_code != 200:
            return None

        book_dir = None
        for b in r_books.json():
            if book_key.lower() in b.get("name", "").lower():
                book_dir = b["name"]
                break

        if not book_dir:
            return None

        r_files = requests.get(f"{api_url}/{author_dir}/{book_dir}", headers=HEADERS, timeout=20)
        if r_files.status_code != 200:
            return None

        for f in r_files.json():
            fname = f.get("name", "")
            if not fname.endswith(".yml") and not fname.endswith(".md"):
                return f"data/{author_dir}/{book_dir}/{fname}"
    except Exception:
        pass
    return None

def download_file(repo, rel_path, out_path):
    urls = [
        f"https://raw.githubusercontent.com/OpenITI/{repo}/master/{rel_path}",
        f"https://cdn.jsdelivr.net/gh/OpenITI/{repo}@{rel_path}",
        f"https://raw.githack.com/OpenITI/{repo}/master/{rel_path}"
    ]
    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, stream=True, timeout=40)
            if res.status_code == 200:
                total_size = int(res.headers.get("content-length", 0))
                with open(out_path, "wb") as f, tqdm(
                    total=total_size, unit="iB", unit_scale=True, unit_divisor=1024, desc=os.path.basename(out_path)
                ) as bar:
                    for chunk in res.iter_content(1024 * 64):
                        f.write(chunk)
                        bar.update(len(chunk))
                return True
        except requests.RequestException:
            continue
    return False

print("=" * 65)
print("[*] EKSIK ANA KULLIYATLAR INDIRILIYOR (EL-UMM, MUDAWWANA, MABSUT)")
print("=" * 65)

results = []

for target in EXPANSION_TARGETS:
    m = target["mezhep"]
    e = target["eser"]
    print(f"\n[*] {m} - {e} taranıyor...")
    
    rel_path = find_remote_file(target["repo"], target["author_key"], target["book_key"])
    if not rel_path:
        print(f"[-] Hata: {e} bulunamadı.")
        results.append((m, e, "BULUNAMADI", 0))
        continue
    
    print(f"[+] Konum doğrulandı: {rel_path}")
    ok = download_file(target["repo"], rel_path, target["out_file"])
    if ok and os.path.exists(target["out_file"]):
        size_mb = os.path.getsize(target["out_file"]) / (1024 * 1024)
        print(f"[+] İndirme tamamlandı: {target['out_file']} ({size_mb:.2f} MB)")
        results.append((m, e, "TAMAMLANDI", size_mb))
    else:
        results.append((m, e, "INDIRME_HATASI", 0))

print("\n" + "=" * 65)
print("INDİRME RAPORU:")
for m, e, st, sz in results:
    print(f"  {m:<10} | {e:<15} | {st:<12} ({sz:.2f} MB)")
print("=" * 65)