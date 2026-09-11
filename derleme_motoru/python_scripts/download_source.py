import os
import sys
import requests
from tqdm import tqdm

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
OUTPUT_DIR = "raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "bidayat_al_mujtahid_raw.txt")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("[*] OpenITI 0600AH agaci taranarak dosya yolu tespit ediliyor...")
target_file_path = None

# 1. Katman: jsDelivr Flat Data API (Engelsiz ve hizli indeks taramasi)
try:
    api_url = "https://data.jsdelivr.com/v1/package/gh/OpenITI/0600AH/flat"
    r = requests.get(api_url, headers=HEADERS, timeout=20)
    if r.status_code == 200:
        files = r.json().get("files", [])
        for f in files:
            name = f.get("name", "")
            if "0595IbnRushd" in name and "Bidayat" in name and not name.endswith(".yml"):
                target_file_path = name
                print(f"[+] Dosya yolu dogrulandi (Index): {target_file_path}")
                break
except Exception as e:
    print(f"[-] Index API hatasi: {e}")

# 2. Katman: GitHub API Fallback
if not target_file_path:
    print("[*] GitHub Contents API ile dizin geziliyor...")
    try:
        gh_url = "https://api.github.com/repos/OpenITI/0600AH/contents/data"
        r = requests.get(gh_url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            authors = [i["name"] for i in r.json() if "0595IbnRushd" in i["name"]]
            if authors:
                author_dir = authors[0]
                r2 = requests.get(f"{gh_url}/{author_dir}", headers=HEADERS, timeout=20)
                books = [i["name"] for i in r2.json() if "Bidayat" in i["name"]]
                if books:
                    book_dir = books[0]
                    r3 = requests.get(f"{gh_url}/{author_dir}/{book_dir}", headers=HEADERS, timeout=20)
                    for item in r3.json():
                        if not item["name"].endswith(".yml"):
                            target_file_path = f"/data/{author_dir}/{book_dir}/{item['name']}"
                            print(f"[+] Dosya yolu dogrulandi (GitHub): {target_file_path}")
                            break
    except Exception as e:
        print(f"[-] GitHub API hatasi: {e}")

if not target_file_path:
    print("[-] HATA: Bidayat al-Mujtahid kaynak metni depoda bulunamadi.", file=sys.stderr)
    sys.exit(1)

clean_path = target_file_path.lstrip("/")
download_urls = [
    f"https://cdn.jsdelivr.net/gh/OpenITI/0600AH@{clean_path}",
    f"https://raw.githubusercontent.com/OpenITI/0600AH/master/{clean_path}",
    f"https://raw.githack.com/OpenITI/0600AH/master/{clean_path}"
]

download_stream = None
active_url = None
for url in download_urls:
    try:
        res = requests.get(url, headers=HEADERS, stream=True, timeout=25)
        if res.status_code == 200:
            download_stream = res
            active_url = url
            break
    except requests.RequestException:
        continue

if not download_stream:
    print("[-] HATA: Tespit edilen dosya indirilemedi.", file=sys.stderr)
    sys.exit(1)

total_size = int(download_stream.headers.get("content-length", 0))
block_size = 1024 * 64

print(f"[*] Indirme baslatildi: {active_url}")
with open(OUTPUT_FILE, "wb") as f, tqdm(
    total=total_size, unit="iB", unit_scale=True, unit_divisor=1024
) as bar:
    for chunk in download_stream.iter_content(block_size):
        f.write(chunk)
        bar.update(len(chunk))

size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
with open(OUTPUT_FILE, "r", encoding="utf-8", errors="ignore") as f:
    sample_header = [f.readline().strip() for _ in range(3)]
    f.seek(0)
    total_lines = sum(1 for _ in f)

print("\n" + "=" * 50)
print("DURUM         : INDIRME_BASARILI")
print(f"DOSYA         : {OUTPUT_FILE}")
print(f"BOYUT         : {size_mb:.2f} MB")
print(f"SATIR SAYISI  : {total_lines}")
print(f"ILK SATIRLAR  : {sample_header}")
print("=" * 50)