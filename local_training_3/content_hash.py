from web3 import Web3
import os

def calculate_keccak256(file_path):
    w3 = Web3()
    
    if not os.path.exists(file_path):
        print(f"File {file_path} tidak ditemukan.")
        return None

    with open(file_path, "rb") as f:
        file_content = f.read()
        
    # Menghitung hash Keccak-256 (EVM Compatible)
    # Ini adalah 'sidik jari' digital yang akan disimpan di blockchain
    file_hash = w3.keccak(file_content)
    
    return "0x" + file_hash.hex()

# Penggunaan:
model_path = "output_client_3/update_model/model.safetensors"
hash_result = calculate_keccak256(model_path)

if hash_result:
    print(f"Model Path: {model_path}")
    print(f"Content Hash (Hex): {hash_result}")
    # Gunakan hash ini untuk variabel 'contentHash' di Smart Contract