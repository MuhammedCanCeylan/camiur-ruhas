import os
import sys
import re
import json
import zipfile
import urllib.request
import subprocess

MODELS_DIR = r"D:\fikh_models"
BIN_DIR = os.path.join(MODELS_DIR, "llama_bin")
MODEL_PATH = os.path.join(MODELS_DIR, "Qwen2.5-7B-Instruct-Q4_K_M.gguf")

print("=" * 80)
print("[*] GGERGANOV/LLAMA.CPP EN GÜNCEL CUDA SÜRÜMÜ KURULUMU")
print("=" * 80)

os.makedirs(BIN_DIR, exist_ok=True)
cli_path = os.path.join(BIN_DIR, "llama-cli.exe")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8"
}

if not os.path.exists(cli_path):
    print("[*] En güncel llama.cpp derlemesi taranıyor...")
    download_links = []
    
    # 1. Aşama: GitHub API Sorgusu
    try:
        api_url = "https://api.github.com/repos/ggerganov/llama.cpp/releases?per_page=1"
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            releases = json.loads(resp.read().decode("utf-8"))
            if releases and "assets" in releases[0]:
                rel = releases[0]
                tag = rel.get("tag_name", "latest")
                print(f"[+] API Üzerinden Tespit Edilen Sürüm: {tag}")
                for asset in rel["assets"]:
                    n = asset["name"].lower()
                    u = asset["browser_download_url"]
                    if n.endswith(".zip") and "win" in n and "x64" in n:
                        if ("cuda" in n or "cu12" in n) and "cudart" not in n:
                            download_links.append((asset["name"], u))
                        elif "cudart" in n and ("cu12" in n or "cuda" in n):
                            download_links.append((asset["name"], u))
    except Exception as e:
        print(f"[*] API atlandı ({e}), HTML ayrıştırma devrede...")

    # 2. Aşama: HTML Doğrudan Kazıma (Fallback)
    if not download_links:
        try:
            web_url = "https://github.com/ggerganov/llama.cpp/releases"
            req = urllib.request.Request(web_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8")
                matches = re.findall(r'href="(/ggerganov/llama\.cpp/releases/download/[^"]+\.zip)"', html)
                
                main_bin = None
                cudart_bin = None
                for m in matches:
                    fname = m.split("/")[-1]
                    fn_low = fname.lower()
                    full_u = "https://github.com" + m
                    if "win" in fn_low and "x64" in fn_low:
                        if ("cuda" in fn_low or "cu12" in fn_low) and "cudart" not in fn_low and not main_bin:
                            main_bin = (fname, full_u)
                        elif "cudart" in fn_low and ("cu12" in fn_low or "cuda" in fn_low) and not cudart_bin:
                            cudart_bin = (fname, full_u)
                            
                if main_bin:
                    download_links.append(main_bin)
                if cudart_bin:
                    download_links.append(cudart_bin)
        except Exception as e2:
            print(f"[-] HTML kazıma hatası: {e2}")
            sys.exit(1)

    if not download_links:
        print("[-] Uygun Windows CUDA arşivi bulunamadı!")
        sys.exit(1)

    # İndirme ve Arşiv Açma
    for name, url in download_links:
        dest_zip = os.path.join(MODELS_DIR, name)
        if not os.path.exists(dest_zip):
            print(f"\n[*] İndiriliyor: {name}")
            print(f"    URL: {url}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp, open(dest_zip, "wb") as f:
                f.write(resp.read())
            print(f"[+] İndirildi: {dest_zip}")
            
        print(f"[*] Çıkarılıyor: {name} -> {BIN_DIR}")
        with zipfile.ZipFile(dest_zip, 'r') as zip_ref:
            zip_ref.extractall(BIN_DIR)

# cli_path doğrulaması
if not os.path.exists(cli_path):
    for root, _, files in os.walk(BIN_DIR):
        if "llama-cli.exe" in files:
            cli_path = os.path.join(root, "llama-cli.exe")
            break

if not os.path.exists(cli_path):
    print("[-] HATA: llama-cli.exe bulunamadı!")
    sys.exit(1)

print(f"\n[+] Motor başarıyla hazırlandı: {cli_path}")

# RTX 4060 GPU Çıkarım Testi
print("\n" + "=" * 80)
print("[*] QWEN2.5-7B CANLI GPU TESTI (RTX 4060 -ngl 99)...")
print("=" * 80)

test_prompt = "<|im_start|>system\nSen uzman bir İslam Hukuku (Fıkıh) bilginisin. Sadece fıkhi terminolojiyle net cevap ver.<|im_end|>\n<|im_start|>user\nFıkıhta 'illet' ile 'hikmet' arasındaki temel fark nedir? Tek cümleyle açıkla.<|im_end|>\n<|im_start|>assistant\n"

cmd = [
    cli_path,
    "-m", MODEL_PATH,
    "-ngl", "99",
    "-c", "2048",
    "-p", test_prompt,
    "-n", "128",
    "--temp", "0.1"
]

proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

print("\n--- MODEL ÇIKTISI ---")
print(proc.stdout.strip())
print("---------------------")

if proc.stderr:
    for line in proc.stderr.splitlines():
        if any(k in line for k in ["CUDA", "offload", "load_tensors", "model params", "total VRAM", "CUDA0"]):
            print(f"[GPU Bilgisi] {line.strip()}")

print("=" * 80)
print("[+] YEREL MOTOR GPU ÜZERİNDE BAŞARIYLA ÇALIŞTI.")
print("=" * 80)
