import os
import sys
import requests
from tqdm import tqdm

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
OUT_FILE = os.path.join("raw", "safii_corpus_raw.txt")

# Şâfiî için aranacak öncelikli ana külliyatlar
CANDIDATES = [
    {"repo": "0700AH", "author": "0676Nawawi", "books": ["MinhajTalibin", "RawdatTalibin", "Majmu"]},
    {"repo": "0225AH", "author": "0204Shafii", "books": ["Umm"]}
]

selected_url = None
selected_book = ""

print("[*] Asıl Şâfiî külliyatı taranıyor...")

for cand in CANDIDATES:
    repo = cand["repo"]
    author = cand["author"]
    api_url = f"https://api.github.com/repos/OpenITI/{repo}/contents/data/{author}"
    
    try:
        r = requests.get(api_url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            continue
        
        book_dirs = [b["name"] for b in r.json() if b.get("type") == "dir"]
        
        for target_book in cand["books"]:
            # 'Daqaiq' içermeyen ve hedef eseri barındıran klasörü bul
            matched = [b for b in book_dirs if target_book.lower() in b.lower() and "daqaiq" not in b.lower()]
            if matched:
                book_folder = matched[0]
                # Klasör içindeki ana metin dosyasını bul
                r_files = requests.get(f"{api_url}/{book_folder}", headers=HEADERS, timeout=15)
                if r_files.status_code == 200:
                    for item in r_files.json():
                        fname = item["name"]
                        if not fname.endswith(".yml") and not fname.endswith(".md"):
                            rel_path = f"data/{author}/{book_folder}/{fname}"
                            selected_url = f"https://raw.githubusercontent.com/OpenITI/{repo}/master/{rel_path}"
                            selected_book = book_folder
                            break
            if selected_url:
                break
        if selected_url:
            break
    except Exception as e:
        continue

if not selected_url:
    print("[-] HATA: Şâfiî ana metni bulunamadı.", file=sys.stderr)
    sys.exit(1)

print(f"[+] Doğrulandı: {selected_book}")
print(f"[*] İndiriliyor: {selected_url}")

res = requests.get(selected_url, headers=HEADERS, stream=True, timeout=40)
if res.status_code != 200:
    print(f"[-] HTTP Hatası: {res.status_code}", file=sys.stderr)
    sys.exit(1)

total_size = int(res.headers.get("content-length", 0))
with open(OUT_FILE, "wb") as f, tqdm(
    total=total_size, unit="iB", unit_scale=True, unit_divisor=1024, desc="safii_corpus_raw.txt"
) as bar:
    for chunk in res.iter_content(1024 * 64):
        f.write(chunk)
        bar.update(len(chunk))

size_mb = os.path.getsize(OUT_FILE) / (1024 * 1024)
print("\n" + "=" * 50)
print(f"DURUM   : GUNCELLEME_TAMAMLANDI")
print(f"DOSYA   : {OUT_FILE}")
print(f"BOYUT   : {size_mb:.2f} MB")
print("=" * 50)