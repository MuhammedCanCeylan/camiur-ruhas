import os
import sys

# 1. DLL Dizinlerini Tanıt
search_paths = [
    os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib"),
    os.path.join(sys.prefix, "Lib", "site-packages", "llama_cpp", "lib"),
]
nvidia_base = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia")
if os.path.exists(nvidia_base):
    for root, dirs, files in os.walk(nvidia_base):
        if os.path.basename(root) == "bin":
            search_paths.append(root)

for p in set(search_paths):
    if os.path.exists(p):
        try:
            os.add_dll_directory(p)
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
        except Exception:
            pass

from llama_cpp import Llama

MODEL_PATH = r"D:\fikh_models\Qwen2.5-7B-Instruct-Q4_K_M.gguf"

print("=" * 80)
print("[*] TEST 1: CPU BASLANGIC DENETIMI (n_gpu_layers=0, n_ctx=512, verbose=True)")
print("=" * 80)

try:
    llm_cpu = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=0,
        n_ctx=512,
        n_threads=4,
        verbose=True
    )
    print("\n[+] CPU TESTI BASARILI: Islemci komut seti (AVX/AVX2) uyumlu.")
except Exception as e:
    print(f"\n[-] CPU TESTI HATASI: {e}")

print("\n" + "=" * 80)
print("[*] TEST 2: GPU OFFLOAD DENETIMI (n_gpu_layers=20, n_ctx=1024, verbose=True)")
print("=" * 80)

try:
    llm_gpu = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=20,
        n_ctx=1024,
        n_threads=4,
        verbose=True
    )
    print("\n[+] GPU TESTI BASARILI: CUDA baglami ve RTX 4060 VRAM offload calisiyor.")
except Exception as e:
    print(f"\n[-] GPU TESTI HATASI: {e}")

print("=" * 80)
