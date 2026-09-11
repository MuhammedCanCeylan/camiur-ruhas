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
    # Hanefî (Nihai Fetva Külliyatı)
    {
        "mezhep": "Hanefi",
        "eser": "Reddul_Muhtar",
        "author_kw": ["abidin", "cabidin"],
        "book_kw": ["radd", "muhtar", "hasyiyah"],
        "repos": ["1275AH", "1250AH", "1300AH"],
        "out_file": os.path.join(RAW_DIR, "hanefi_radd_muhtar_raw.txt")
    },
    # Şâfiî (Müteahhirîn Fetva Şerhi)
    {
        "mezhep": "Safii",
        "eser": "Nihayetul_Muhtac",
        "author_kw": ["ramli"],
        "book_kw": ["nihayat", "muhtaj"],
        "repos": ["1025AH", "1000AH", "1050AH"],
        "out_file": os.path.join(RAW_DIR, "safii_nihayat_raw.txt")
    },
    # Mâlikî (Kurucu Hadis-Fıkıh & Muhtasar-ı Halil Şerhi)
    {
        "mezhep": "Maliki",
        "eser": "el_Muvatta",
        "author_kw": ["malik"],
        "book_kw": ["muwatta"],
        "repos": ["0200AH"],
        "out_file": os.path.join(RAW_DIR, "maliki_muwatta_raw.txt")
    },
    {
        "mezhep": "Maliki",
        "eser": "Mawahibul_Jalil",
        "author_kw": ["hattab"],
        "book_kw": ["mawahib", "khalil"],
        "repos": ["0975AH", "0950AH", "1000AH"],
        "out_file": os.path.join(RAW_DIR, "maliki_mawahib_raw.txt")
    },
    # Hanbelî (Mezhep İçi Tahkik & Müntehâ Şerhi)
    {
        "mezhep": "Hanbeli",
        "eser": "el_Insaf",
        "author_kw": ["mardawi"],
        "book_kw": ["insaf"],
        "repos": ["0885AH", "0900AH", "0875AH"],
        "out_file": os.path.join(RAW_DIR, "hanbeli_insaf_raw.txt")
    },
    {
        "mezhep": "Hanbeli",
        "eser": "Kassafu_l_Kina",
        "author_kw": ["buhuti"],
        "book_kw": ["kashshaf", "qina"],
        "repos": ["1075AH", "1050AH", "1100AH"],
        "out_file": os.path.join(RAW_DIR, "hanbeli_kashshaf_raw.txt")
    }
]

def scan_and_download(target):
    found_repo = None
    found_path = None
    
    for repo in target["repos"]:
        for branch in ["master", "main"]:
            tree_url = f"https://api.github.com/repos/OpenITI/{repo}/git/trees/{branch}?recursive=1"
            try:
                r = requests.get(tree_url, headers=HEADERS, timeout=20)
                if r.status_code != 200:
                    continue
                tree = r.json().get("tree", [])
                for item in tree:
                    if item.get("type") == "blob":
                        p = item.get("path", "").lower()
                        if any(a in p for a in target["author_kw"]) and any(b in p for b in target["book_kw"]):
                            if not p.endswith((".yml", ".md", ".inreview", "-ara1.inreview")):
                                found_repo = repo
                                found_path = item.get("path", "")
                                break
                if found_path:
                    break
            except Exception:
                continue
        if found_path:
            break

    if not found_path:
        return False, 0.0

    urls = [
        f"https://raw.githubusercontent.com/OpenITI/{found_repo}/master/{found_path}",
        f"https://cdn.jsdelivr.net/gh/OpenITI/{found_repo}@{found_path}",
        f"https://raw.githack.com/OpenITI/{found_repo}/master/{found_path}"
    ]

    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, stream=True, timeout=40)
            if res.status_code == 200:
                total_size = int(res.headers.get("content-length", 0))
                with open(target["out_file"], "wb") as f, tqdm(
                    total=total_size, unit="iB", unit_scale=True, unit_divisor=1024, desc=os.path.basename(target["out_file"])
                ) as bar:
                    for chunk in res.iter_content(1024 * 64):
                        f.write(chunk)
                        bar.update(len(chunk))
                size_mb = os.path.getsize(target["out_file"]) / (1024 * 1024)
                return True, size_mb
        except requests.RequestException:
            continue
    return False, 0.0

print("=" * 70)
print("[*] 4 HAK MEZHEP NIHAI METINLERI INDIRME HATTI BASLATILDI")
print("=" * 70)

report = []
for t in EXPANSION_TARGETS:
    print(f"\n[*] {t['mezhep']} - {t['eser']} araniyor...")
    ok, size_mb = scan_and_download(t)
    if ok:
        print(f"[+] Indirildi: {t['out_file']} ({size_mb:.2f} MB)")
        report.append((t["mezhep"], t["eser"], "TAMAMLANDI", size_mb))
    else:
        print(f"[-] Hata: {t['eser']} indirilemedi.")
        report.append((t["mezhep"], t["eser"], "BULUNAMADI", 0.0))

print("\n" + "=" * 70)
print("INDIRME OZET RAPORU:")
for m, e, st, sz in report:
    print(f"  {m:<10} | {e:<18} | {st:<12} ({sz:.2f} MB)")
print("=" * 70)
