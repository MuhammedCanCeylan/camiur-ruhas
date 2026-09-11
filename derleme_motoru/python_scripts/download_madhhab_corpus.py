import os
import sys
import requests
from tqdm import tqdm

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
RAW_DIR = "raw"
os.makedirs(RAW_DIR, exist_ok=True)

# 25 yıllık OpenITI dilimlerine göre optimize edilmiş konfigürasyon
CORPUS_CONFIG = [
    {
        "mezhep": "Hanefi",
        "author_candidates": ["Marghinani", "Kasani", "Quduri"],
        "book_candidates": ["Hidaya", "Badai", "Mukhtasar"],
        "repos": ["0600AH", "0450AH"],
        "out_file": os.path.join(RAW_DIR, "hanefi_corpus_raw.txt")
    },
    {
        "mezhep": "Safii",
        "author_candidates": ["Nawawi", "Shafii"],
        "book_candidates": ["Minhaj", "Umm", "Majmu"],
        "repos": ["0700AH", "0675AH", "0225AH"],
        "out_file": os.path.join(RAW_DIR, "safii_corpus_raw.txt")
    },
    {
        "mezhep": "Maliki",
        "author_candidates": ["AbdBarr", "Sahnun", "Malik"],
        "book_candidates": ["Kafi", "Mudawwana", "Muwatta"],
        "repos": ["0475AH", "0500AH", "0250AH", "0200AH"],
        "out_file": os.path.join(RAW_DIR, "maliki_corpus_raw.txt")
    },
    {
        "mezhep": "Hanbeli",
        "author_candidates": ["Qudama", "Mardawi"],
        "book_candidates": ["Mughni", "Muqni", "Insaf"],
        "repos": ["0625AH", "0650AH", "0885AH"],
        "out_file": os.path.join(RAW_DIR, "hanbeli_corpus_raw.txt")
    }
]

def resolve_openiti_file(repos, author_candidates, book_candidates):
    for repo in repos:
        api_base = f"https://api.github.com/repos/OpenITI/{repo}/contents/data"
        try:
            r = requests.get(api_base, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            data_dirs = r.json()
            
            # 1. Yazar klasorunu bul
            matched_author_dir = None
            for item in data_dirs:
                name = item.get("name", "").lower()
                if any(ac.lower() in name for ac in author_candidates):
                    matched_author_dir = item["name"]
                    break
            
            if not matched_author_dir:
                continue

            # 2. Kitap klasorunu bul
            r_author = requests.get(f"{api_base}/{matched_author_dir}", headers=HEADERS, timeout=15)
            if r_author.status_code != 200:
                continue
            
            matched_book_dir = None
            for item in r_author.json():
                name = item.get("name", "").lower()
                if any(bc.lower() in name for bc in book_candidates):
                    matched_book_dir = item["name"]
                    break
            
            if not matched_book_dir:
                continue

            # 3. Metin dosyasini bul
            r_book = requests.get(f"{api_base}/{matched_author_dir}/{matched_book_dir}", headers=HEADERS, timeout=15)
            if r_book.status_code != 200:
                continue
            
            for item in r_book.json():
                fname = item.get("name", "")
                if not fname.endswith(".yml") and not fname.endswith(".md"):
                    rel_path = f"data/{matched_author_dir}/{matched_book_dir}/{fname}"
                    return repo, rel_path

        except Exception as e:
            continue
    return None, None

def stream_download(repo, rel_path, out_path):
    urls = [
        f"https://raw.githubusercontent.com/OpenITI/{repo}/master/{rel_path}",
        f"https://cdn.jsdelivr.net/gh/OpenITI/{repo}@{rel_path}",
        f"https://raw.githack.com/OpenITI/{repo}/master/{rel_path}"
    ]
    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, stream=True, timeout=30)
            if res.status_code == 200:
                total = int(res.headers.get("content-length", 0))
                with open(out_path, "wb") as f, tqdm(
                    total=total, unit="iB", unit_scale=True, unit_divisor=1024, desc=os.path.basename(out_path)
                ) as bar:
                    for chunk in res.iter_content(1024 * 64):
                        f.write(chunk)
                        bar.update(len(chunk))
                return True
        except requests.RequestException:
            continue
    return False

print("=" * 60)
print("[*] 4 MEZHEP ASIL METINLERI TESPIT VE INDIRME HATTI")
print("=" * 60)

report = []

for cfg in CORPUS_CONFIG:
    mezhep = cfg["mezhep"]
    print(f"\n[*] {mezhep} metin yolu araniyor...")
    
    repo, rel_path = resolve_openiti_file(
        cfg["repos"],
        cfg["author_candidates"],
        cfg["book_candidates"]
    )
    
    if not repo or not rel_path:
        print(f"[-] {mezhep} metni belirtilen depolar altinda eslesmedi.")
        report.append((mezhep, "ESLESME_YOK", 0.0))
        continue
    
    print(f"[+] Bulundu: [{repo}] {rel_path}")
    success = stream_download(repo, rel_path, cfg["out_file"])
    
    if success and os.path.exists(cfg["out_file"]):
        size_mb = os.path.getsize(cfg["out_file"]) / (1024 * 1024)
        print(f"[+] Basariyla indirildi: {cfg['out_file']} ({size_mb:.2f} MB)")
        report.append((mezhep, "TAMAMLANDI", size_mb))
    else:
        print(f"[-] Indirme hatasi: {cfg['out_file']}")
        report.append((mezhep, "INDIRME_HATASI", 0.0))

print("\n" + "=" * 60)
print("INDIRME RAPORU:")
for mezhep, durum, mb in report:
    print(f"  {mezhep:<10}: {durum:<15} ({mb:.2f} MB)")
print("=" * 60)