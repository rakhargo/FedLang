from huggingface_hub import snapshot_download
import os

# Konfigurasi Proyek
MODEL_ID = "openai-community/gpt2"
LOCAL_DIR = "./models"

allow_patterns = [
    "config.json",           # Konfigurasi arsitektur model
    "model.safetensors",     # Bobot model (format aman & cepat)
    "pytorch_model.bin",     # Fallback jika safetensors tidak tersedia
    "tokenizer.json",        # Definisi tokenizer
    "tokenizer_config.json", # Konfigurasi tokenizer
    "vocab.json",            # Kosakata model
    "merges.txt",            # Aturan penggabungan token (khusus GPT-2)
    "special_tokens_map.json"
]

snapshot_download(
    repo_id=MODEL_ID,
    local_dir=LOCAL_DIR,
    allow_patterns=allow_patterns,
    ignore_patterns=["*.h5", "*.msgpack", "*.tfraw", "README.md", ".gitattributes"]
)

print(f"\n[SUKSES] Model bersih tersimpan di: {os.path.abspath(LOCAL_DIR)}")