import time
import json
import torch
import os
import requests
from web3 import Web3
from safetensors.torch import load_file, save_file
from eth_account import Account
from eth_account.messages import encode_defunct
from dotenv import load_dotenv

load_dotenv()

# === Konfigurasi ===
RPC_URL = os.getenv("ANKR_SEPOLIA_RPC_URL") 
CONTRACT_ADDRESS = "0x5d3763ADc9EFD4098279217584F66D554CD30f7B"
PROJECT_ID = 1 
PRIVATE_KEY = os.getenv("INIT_PRIVATE_KEY")
ABI_PATH = "./FederatedHub.json" 
IPFS_RPC_URL = "http://127.0.0.1:5001/api/v0"
POLL_INTERVAL = 10 

w3 = Web3(Web3.HTTPProvider(RPC_URL))
with open(ABI_PATH) as f:
    abi = json.load(f)['abi']
contract = w3.eth.contract(address=w3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)
account = w3.eth.account.from_key(PRIVATE_KEY)

def evaluate_model_quality(file_path):
    """
    Simulasi evaluasi kualitas model (Bab 4: Mekanisme Adil).
    Dalam riset asli, ini akan menguji model terhadap dataset validasi lokal.
    Mengembalikan skor 0-100.
    """
    print(f"  [Eval] Mengevaluasi {file_path}...")
    # Contoh logika: jika ukuran file valid, beri skor bagus
    if os.path.getsize(file_path) > 0:
        return 90 # Diasumsikan kualitasnya 90%
    return 0

def finalize_on_chain(new_cid, participants, scores):
    """Memanggil finalizeRound dengan data reward."""
    print(f"  [Blockchain] Mengirim finalisasi ronde ke Sepolia...")
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Kirim daftar address dan daftar skor secara paralel
    tx = contract.functions.finalizeRound(
        PROJECT_ID, 
        new_cid, 
        participants, 
        scores
    ).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 1000000, # Naikkan gas karena ada loop reward
        'gasPrice': w3.eth.gas_price
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)

def verify_data_integrity(data_bytes, expected_hash_bytes):
    """Memverifikasi integritas data menggunakan Keccak256 (EVM Compatible)."""
    actual_hash = w3.keccak(data_bytes)
    return actual_hash == expected_hash_bytes

def verify_did_signature(participant_addr, content_hash_bytes, signature_bytes):
    """
    Tahap Verifikasi DID: Memastikan signature valid dan dibuat oleh 
    pemilik wallet yang terdaftar dengan did:key tersebut.
    """
    try:
        # 1. Ambil Identifier did:key dari Smart Contract untuk logging/audit
        # Mapping participants(address) -> struct { string did, bool isRegistered }
        did_data = contract.functions.participants(participant_addr).call()
        did_string = did_data[0]

        # 2. Rekonstruksi pesan (hash model) untuk di-recover
        message = encode_defunct(primitive=content_hash_bytes)
        
        # 3. Recover address dari signature
        recovered_addr = Account.recover_message(message, signature=signature_bytes)
        
        # 4. Validasi identitas
        is_valid = recovered_addr.lower() == participant_addr.lower()
        
        if is_valid:
            print(f"  [Identity] DID Verified: {did_string}")
        else:
            print(f"  [Identity] ALERT: Signature mismatch for {participant_addr}")
            
        return is_valid
    except Exception as e:
        print(f"  [Identity] Error verifikasi: {e}")
        return False

def download_from_ipfs(cid):
    """Mengunduh file dari IPFS menggunakan RPC API."""
    print(f"  [IPFS] Mengunduh CID: {cid}")
    try:
        response = requests.post(f"{IPFS_RPC_URL}/cat?arg={cid}", timeout=60)
        response.raise_for_status()
        
        temp_path = f"temp_{cid}.bin"
        with open(temp_path, "wb") as f:
            f.write(response.content)
        return temp_path
    except Exception as e:
        print(f"  [Error] Gagal unduh dari IPFS: {e}")
        return None

def upload_to_ipfs(file_path):
    """Mengunggah file ke IPFS menggunakan RPC API."""
    print(f"  [IPFS] Mengunggah file: {file_path}")
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{IPFS_RPC_URL}/add", files=files, timeout=60)
            response.raise_for_status()
            return response.json()["Hash"]
    except Exception as e:
        print(f"  [Error] Gagal unggah ke IPFS: {e}")
        return None
    
def federated_averaging(model_paths):
    """Melakukan agregasi FedAvg pada format Safetensors."""
    print(f"--- Melakukan Agregasi pada {len(model_paths)} model (Safetensors) ---")
    
    global_dict = load_file(model_paths[0])
    multiplier = 1.0 / len(model_paths)
    
    for key in global_dict.keys():
        global_dict[key] = global_dict[key].float() * multiplier
        
    for i in range(1, len(model_paths)):
        local_dict = load_file(model_paths[i])
        for key in global_dict.keys():
            global_dict[key] += local_dict[key].float() * multiplier
            
    output_path = "global_model_updated.safetensors"
    save_file(global_dict, output_path)
    return output_path

def main():
    print(f"Aggregator aktif untuk Project ID: {PROJECT_ID}")
    while True:
        try:
            ready = contract.functions.canAggregate(PROJECT_ID).call()
            proj_data = contract.functions.projects(PROJECT_ID).call()
            current_round = proj_data[2]
            
            if ready:
                print(f"\n=== Memulai Agregasi Round {current_round} ===")
                model_files = []
                valid_addresses = []
                quality_scores = []
                
                logs = contract.events.ContributionSubmitted().get_logs(from_block=10826764)
                # Filter manual logs untuk project dan round saat ini
                current_logs = [l for l in logs if l.args.projectId == PROJECT_ID and l.args.round == current_round]

                for log in current_logs:
                    addr = log.args.participant
                    contrib = contract.functions.contributions(PROJECT_ID, current_round, addr).call()
                    
                    # Verifikasi Identitas & Integritas
                    if verify_did_signature(addr, contrib[1], contrib[2]):
                        path = download_from_ipfs(contrib[0])
                        if path and verify_data_integrity(open(path, "rb").read(), contrib[1]):
                            # HITUNG SKOR KUALITAS
                            score = evaluate_model_quality(path)
                            
                            model_files.append(path)
                            valid_addresses.append(addr)
                            quality_scores.append(score)
                    
                if len(model_files) >= 3:
                    updated_model = federated_averaging(model_files)
                    new_cid = upload_to_ipfs(updated_model)
                    
                    if new_cid:
                        receipt = finalize_on_chain(new_cid, valid_addresses, quality_scores)
                        print(f"  [Success] Ronde Selesai! TX: {receipt.transactionHash.hex()}")
                
                # Cleanup
                for f in model_files: os.remove(f) if os.path.exists(f) else None
            
            else:
                print(f"Menunggu partisipan... (Round {current_round})", end="\r")
        except Exception as e:
            print(f"\n  [Error] {e}")
            
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()