import os
import sys
import glob

# 1. NVIDIA ve CUDA DLL Dizinlerinin Windows'a Tanıtılması
search_paths = [
    os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib"),
    os.path.join(sys.prefix, "Lib", "site-packages", "llama_cpp", "lib"),
]

# pip ile kurulan nvidia paketlerinin bin dizinlerini tara
nvidia_base = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia")
if os.path.exists(nvidia_base):
    for root, dirs, files in os.walk(nvidia_base):
        if os.path.basename(root) == "bin":
            search_paths.append(root)

# Sistemde yüklü CUDA Toolkit dizinlerini tara
cuda_path = os.environ.get("CUDA_PATH", "")
if cuda_path:
    search_paths.append(os.path.join(cuda_path, "bin"))
for p in glob.glob(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\*\bin"):
    search_paths.append(p)

for p in set(search_paths):
    if os.path.exists(p):
        try:
            os.add_dll_directory(p)
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
            print(f"[+] DLL Arama Dizini Eklendi: {p}")
        except Exception:
            pass

# DLL çözümlemesi tamamlandıktan sonra llama_cpp import edilir
try:
    from llama_cpp import Llama
    print("[+] llama_cpp kütüphanesi başarıyla yüklendi (GPU Hazır).")
except Exception as e:
    print(f"[-] HATA: llama_cpp yüklenemedi: {e}")
    sys.exit(1)

from huggingface_hub import hf_hub_download

MODELS_DIR = r"D:\fikh_models"
MODEL_REPO = "bartowski/Qwen2.5-7B-Instruct-GGUF"
MODEL_FILE = "Qwen2.5-7B-Instruct-Q4_K_M.gguf"
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_FILE)

print("=" * 80)
print("[*] FAZ 3.1: D:\\ DISKINE YEREL MODEL KURULUMU VE GPU CINFER")
print("=" * 80)

if not os.path.exists("D:\\"):
    print("[-] HATA: D:\\ sürücüsü sistemde bulunamadı!")
    sys.exit(1)

os.makedirs(MODELS_DIR, exist_ok=True)
print(f"[+] Model Depolama Yolu : {MODELS_DIR}")

# 2. Modelin D:\ Dizinine İndirilmesi
if not os.path.exists(MODEL_PATH):
    print(f"\n[*] Model Hugging Face'ten D:\\ diskine indiriliyor: {MODEL_REPO}/{MODEL_FILE}")
    print("[*] Boyut: ~4.68 GB (İlerleme çubuğu aşağıda görünecektir)...")
    downloaded_path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=MODEL_FILE,
        local_dir=MODELS_DIR
    )
    print(f"[+] İndirme tamamlandı: {downloaded_path}")
else:
    size_gb = os.path.getsize(MODEL_PATH) / (1024**3)
    print(f"[+] Model D:\\ diskinde zaten mevcut: {MODEL_PATH} ({size_gb:.2f} GB)")

# 3. Modelin RTX 4060 GPU Belleğine Yüklenmesi (Tam Offload)
print("\n[*] Model RTX 4060 VRAM'ine yükleniyor (n_gpu_layers=-1, n_ctx=4096)...")
llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=-1,      # Tüm katmanlar RTX 4060 GPU belleğine alınır
    n_ctx=4096,           # 4K bağlam penceresi
    n_threads=8,
    verbose=False
)

print("[+] Model GPU'ya tam offload ile yüklendi.")

# 4. Donanım ve Fıkıh Terminolojisi Testi
test_prompt = "<|im_start|>system\nSen uzman bir İslam Hukuku (Fıkıh) bilginisin. Sadece fıkhi terminolojiyle net cevap ver.<|im_end|>\n<|im_start|>user\nFıkıhta 'illet' ile 'hikmet' arasındaki temel fark nedir? Tek cümleyle açıkla.<|im_end|>\n<|im_start|>assistant\n"

print("\n[*] Model Çıkarım Testi Yapılıyor...")
output = llm(
    test_prompt,
    max_tokens=150,
    temperature=0.1,
    top_p=0.9,
    stop=["<|im_end|>"]
)

cevap = output["choices"][0]["text"].strip()
print("-" * 80)
print(f"Model Cevabı:\n{cevap}")
print("-" * 80)
print(f"Üretilen Token: {output['usage']['completion_tokens']}")
print("=" * 80)
print("[+] YEREL LLM D:\\ ÜZERİNDE VE GPU'DA BAŞARIYLA ÇALIŞTI.")
print("=" * 80)
