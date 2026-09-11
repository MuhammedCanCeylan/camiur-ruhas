import os
import sys
import requests
from tqdm import tqdm

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
RAW_DIR = "raw"
os.makedirs(RAW_DIR, exist_ok=True)

TARGETS = [
    {
        "mezhep": "Safii",
        "eser": "el_Umm",
        "author_patterns": ["shafi", "shafic", "idrisshafici"],
        "book_patterns": ["umm"],
        "repos": ["0225AH", "0250AH"],
        "out_file": os.path.join(RAW_DIR, "safii_umm_raw.txt")
    },
    {
        "mezhep": "Safii",
        "eser": "el_Mecmu",
        "author_patterns": ["nawawi"],
        "book_patterns": ["majmu", "majmuc"],
        "repos": ["0700AH", "0675AH"],
        "out_file": os.path.join(RAW_DIR, "safii_majmu_raw.txt")
    },
    {
        "mezhep": "Hanefi",
        "eser": "el_Mabsut",
        "author_patterns": ["sarakh", "sarax", "sarahsi"],
        "book_patterns": ["mabsut"],
        "repos": ["0500AH", "0475AH"],
        "out_file": os.path.join(RAW_DIR, "hanefi_mabsut_raw.txt")
    }
]

def scan_and_locate(repo, author_patterns, book_patterns):
    api_url = f"https://api.github.com/repos/OpenITI/{repo}/contents/data"
    try:
        r = requests.get(api_url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        dirs = r.json()
        
        # 1. Yazar klasörünü tespit et
        author_dir = None
        for item in dirs:
            dname = item.get("name", "").lower()
            if any(p in dname for p in author_patterns):
                author_dir = item["name"]
                break
        
        if not author_dir:
            return None

        # 2. Kitap klasörünü tespit et
        r_author = requests.get(f"{api_url}/{author_dir}", headers=HEADERS, timeout=15)
        if r_author.status_code != 200:
            return None

        book_dir = None
        for b in r_author.json():
            bname = b.get("name", "").lower()
            if any(bp in bname for bp in book_patterns):
                book_dir = b["name"]
                break

        if not book_dir:
            return None

        # 3. Dosyayı tespit et
        r_files = requests.get(f"{api_url}/{author_dir}/{book_dir}", headers=HEADERS, timeout=15)
        if r_files.status_code != 200:
            return None

        for f in r_files.json():
            fname = f.get("name", "")
            if not fname.endswith(".yml") and not fname.endswith(".md"):
                return repo, f"data/{author_dir}/{book_dir}/{fname}"

    except Exception as e:
        print(f"[-] Hata [{repo}]: {e}")
    return None

def download_file(repo, rel_path, target_path):
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
                with open(target_path, "wb") as f, tqdm(
                    total=total_size, unit="iB", unit_scale=True, unit_divisor=1024, desc=os.path.basename(target_path)
                ) as bar:
                    for chunk in res.iter_content(1024 * 64):
                        f.write(chunk)
                        bar.update(len(chunk))
                return True
        except requests.RequestException:
            continue
    return False

print("=" * 65)
print("[*] EKSIK ANA FIKIH KULLIYATLARI TESPIT VE INDIRME HATTI")
print("=" * 65)

report = []

for t in TARGETS:
    m = t["mezhep"]
    e = t["eser"]
    print(f"\n[*] {m} - {e} taranıyor...")
    
    found_repo = None
    found_path = None
    
    for r in t["repos"]:
        res = scan_and_locate(r, t["author_patterns"], t["book_patterns"])
        if res:
            found_repo, found_path = res
            break
            
    if not found_path:
        print(f"[-] {e} depolarda bulunamadı.")
        report.append((m, e, "BULUNAMADI", 0.0))
        continue

    print(f"[+] Doğrulandı: [{found_repo}] {found_path}")
    ok = download_file(found_repo, found_path, t["out_file"])
    
    if ok and os.path.exists(t["out_file"]):
        size_mb = os.path.getsize(t["out_file"]) / (1024 * 1024)
        print(f"[+] Başarıyla indirildi ({size_mb:.2f} MB)")
        report.append((m, e, "TAMAMLANDI", size_mb))
    else:
        report.append((m, e, "INDIRME_HATASI", 0.0))

print("\n" + "=" * 65)
print("INDIRME RAPORU:")
for m, e, status, mb in report:
    print(f"  {m:<10} | {e:<15} | {status:<12} ({mb:.2f} MB)")
print("=" * 65)