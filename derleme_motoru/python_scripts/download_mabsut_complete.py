import os
import sys
import requests
from tqdm import tqdm

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
RAW_DIR = "raw"
os.makedirs(RAW_DIR, exist_ok=True)
OUT_FILE = os.path.join(RAW_DIR, "hanefi_mabsut_raw.txt")

REPOS = ["0500AH", "0475AH", "0525AH"]

print("=" * 65)
print("[*] SERAHSI - EL-MEBSUT BLOB TARAMASI VE INDIRME")
print("=" * 65)

target_repo = None
target_path = None

for repo in REPOS:
    for branch in ["master", "main"]:
        tree_url = f"https://api.github.com/repos/OpenITI/{repo}/git/trees/{branch}?recursive=1"
        try:
            r = requests.get(tree_url, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                continue
            tree_data = r.json().get("tree", [])
            for item in tree_data:
                if item.get("type") == "blob":
                    path = item.get("path", "")
                    if "sarakhsi" in path.lower() and "mabsut" in path.lower():
                        if not path.endswith((".yml", ".md", ".inReview")):
                            target_repo = repo
                            target_path = path
                            print(f"[+] Dosya tespit edildi (BLOB): [{repo}] {path}")
                            break
            if target_path:
                break
        except Exception:
            continue
    if target_path:
        break

if not target_path:
    print("[-] HATA: el-Mebsut blob dosyasi bulunamadi.", file=sys.stderr)
    sys.exit(1)

download_urls = [
    f"https://raw.githubusercontent.com/OpenITI/{target_repo}/master/{target_path}",
    f"https://cdn.jsdelivr.net/gh/OpenITI/{target_repo}@{target_path}",
    f"https://raw.githack.com/OpenITI/{target_repo}/master/{target_path}"
]

stream_success = False
for url in download_urls:
    try:
        res = requests.get(url, headers=HEADERS, stream=True, timeout=40)
        if res.status_code == 200:
            total_size = int(res.headers.get("content-length", 0))
            with open(OUT_FILE, "wb") as f, tqdm(
                total=total_size, unit="iB", unit_scale=True, unit_divisor=1024, desc="hanefi_mabsut_raw.txt"
            ) as bar:
                for chunk in res.iter_content(1024 * 64):
                    f.write(chunk)
                    bar.update(len(chunk))
            stream_success = True
            break
    except requests.RequestException:
        continue

if not stream_success or not os.path.exists(OUT_FILE):
    print("[-] HATA: Indirme basarisiz.", file=sys.stderr)
    sys.exit(1)

size_mb = os.path.getsize(OUT_FILE) / (1024 * 1024)
print("\n" + "=" * 65)
print("DURUM       : BASARIYLA_INDIRILDI")
print(f"DOSYA       : {OUT_FILE}")
print(f"BOYUT       : {size_mb:.2f} MB")
print("=" * 65)
