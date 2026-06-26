import os
import json
import requests
from web3 import Web3

# === Konfigurasi Jalur ===
MODEL_LOCAL_PATH = "./output_client_1/update_model/model.safetensors"
VC_LOCAL_PATH = "./platform_credential.json" # File VC
IPFS_RPC_URL = "http://127.0.0.1:5001/api/v0"

w3 = Web3()

def upload_to_ipfs(file_path):
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{IPFS_RPC_URL}/add", files=files, timeout=60)
            response.raise_for_status()
            return response.json()["Hash"]
    except Exception as e:
        print(f"  [Error IPFS] Gagal mengunggah {file_path}: {e}")
        return None

def main():
    print("==========================================================")
    print("      FEDLANG LAYER 2: PACKAGING MODULE (BOX 2)           ")
    print("==========================================================")
    
    if not os.path.exists(MODEL_LOCAL_PATH):
        print(f"  [Error] Berkas model ({MODEL_LOCAL_PATH}) tidak ditemukan!")
        return
    if not os.path.exists(VC_LOCAL_PATH):
        print(f"  [Error] Berkas VC ({VC_LOCAL_PATH}) tidak ditemukan! Jalankan issue_vc.py dulu.")
        return

    # Langkah 1: Hitung Keccak256 dari model biner murni
    print("\n[1/3] Menghitung Content Hash dari model .safetensors...")
    with open(MODEL_LOCAL_PATH, "rb") as f:
        model_bytes = f.read()
    content_hash = w3.keccak(model_bytes)

    # Langkah 2: Unggah Model ke IPFS
    print("\n[2/3] Mengunggah bobot model murni ke IPFS...")
    model_cid = upload_to_ipfs(MODEL_LOCAL_PATH)
    if not model_cid: return

    # Langkah 3: Ambil VC lokal dan satukan menjadi Paket Kombinasi (Skema 2)
    print("\n[3/3] Membaca kredensial dan menyusun paket kombinasi (Model + VC)...")
    with open(VC_LOCAL_PATH, "r") as f:
        vc_data = json.load(f)

    submission_package = {
        "model_update_cid": model_cid,
        "verifiable_credential": vc_data
    }

    # Unggah berkas JSON paket ke IPFS
    temp_package_path = "./temp_submission_package.json"
    with open(temp_package_path, "w") as f:
        json.dump(submission_package, f, indent=2)

    package_cid = upload_to_ipfs(temp_package_path)
    if os.path.exists(temp_package_path): os.remove(temp_package_path)
    
    if not package_cid: return

    # OUTPUT AKHIR: Ini yang akan kamu input ke UI Vue
    print("\n==========================================================")
    print("         DATA BERHASIL DIKEMAS (SIAP UNTUK UI VUE)         ")
    print("==========================================================")
    print(f" SUBMISSION PACKAGE CID : {package_cid}")
    print(f" CONTENT HASH (HEX)     : {"0x" + content_hash.hex()}")
    print("==========================================================")

if __name__ == "__main__":
    main()