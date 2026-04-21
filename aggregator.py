import time
import json
import torch
import hashlib
import os
from web3 import Web3
import requests
from safetensors.torch import load_file, save_file
from eth_account import Account
from eth_account.messages import encode_defunct

# === Konfigurasi ===
RPC_URL = "http://127.0.0.1:8545" 
CONTRACT_ADDRESS = "0x700b6A60ce7EaaEA56F065753d8dcB9653dbAD35" 
PROJECT_ID = 1 
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" 
ABI_PATH = "./FederatedHub.json" 

IPFS_RPC_URL = "http://127.0.0.1:5001/api/v0"
POLL_INTERVAL = 10 

# === Setup Web3 & Contract ===
w3 = Web3(Web3.HTTPProvider(RPC_URL))
with open(ABI_PATH) as f:
    json_data = json.load(f)
    abi = json_data['abi']
contract = w3.eth.contract(address=w3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)
account = w3.eth.account.from_key(PRIVATE_KEY)

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

def finalize_on_chain(new_cid):
    """Memanggil fungsi finalizeRound di Smart Contract."""
    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.finalizeRound(PROJECT_ID, new_cid).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': w3.eth.gas_price
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"  [Blockchain] finalizeRound dikirim: {tx_hash.hex()}")
    return w3.eth.wait_for_transaction_receipt(tx_hash)

def main():
    print(f"Aggregator aktif untuk Project ID: {PROJECT_ID}")
    
    while True:
        ready = contract.functions.canAggregate(PROJECT_ID).call()
        current_round = contract.functions.projects(PROJECT_ID).call()[2]
        
        if ready:
            print(f"\n=== Memulai Agregasi untuk Round {current_round} ===")
            model_files = []
            
            logs = contract.events.ContributionSubmitted().get_logs(
                from_block=0, 
                argument_filters={'projectId': PROJECT_ID, 'round': current_round}
            )
            
            for log in logs:
                participant_addr = log['args']['participant']
                
                # 3. Ambil detail dari mapping contributions (termasuk Signature)
                # Return: (modelUpdateCID, contentHash, signature, timestamp, exists)
                contrib = contract.functions.contributions(PROJECT_ID, current_round, participant_addr).call()
                cid = contrib[0]
                expected_hash = contrib[1]
                signature = contrib[2] # bytes signature untuk DID
                
                # Tahap Verifikasi Ganda:
                # A. Verifikasi Tanda Tangan (Identity Check)
                if not verify_did_signature(participant_addr, expected_hash, signature):
                    print(f"  [Audit Fail] Identitas tidak valid untuk {participant_addr}. Melewati...")
                    continue

                # B. Verifikasi Integritas File (Integritas Check)
                file_path = download_from_ipfs(cid)
                if file_path:
                    with open(file_path, "rb") as f:
                        if verify_data_integrity(f.read(), expected_hash):
                            model_files.append(file_path)
                            print(f"  [Success] Verified & Authenticated: {cid}")
                        else:
                            print(f"  [Audit Fail] Hash mismatch untuk: {cid}")
                            if os.path.exists(file_path): os.remove(file_path)

            if len(model_files) >= 3:
                global_file = federated_averaging(model_files)
                new_global_cid = upload_to_ipfs(global_file)
                
                if new_global_cid:
                    finalize_on_chain(new_global_cid)
                
                for f in model_files: 
                    if os.path.exists(f): os.remove(f)
            else:
                print("Kontribusi valid tidak cukup untuk melakukan agregasi.")
                
        else:
            print(f"Menunggu partisipan... (Round {current_round})", end="\r")
            
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()