import time
import json
import torch
import torch.nn.functional as F
import os
import requests
from web3 import Web3
from safetensors.torch import load_file, save_file
from eth_account import Account
from eth_account.messages import encode_defunct
from dotenv import load_dotenv

load_dotenv()

# === Konfigurasi Utama ===
RPC_URL = os.getenv("ANKR_SEPOLIA_RPC_URL") 
CONTRACT_ADDRESS = "0x0779E41584F22cdbcFab337a721163890651d41e"  # Alamat kontrak pintar FedLang Anda
PROJECT_ID = 1
PRIVATE_KEY = os.getenv("INIT_PRIVATE_KEY")  # Kunci privat Inisiator Proyek untuk panggil finalizeRound
PLATFORM_ADMIN_ADDRESS = "0xadf00a2476c77163B607af6E55A6a90185ae33f6"  # Kunci publik Tim FedLang untuk verifikasi VC
ABI_PATH = "./FederatedHub.json" 
IPFS_RPC_URL = "http://127.0.0.1:5001/api/v0"
POLL_INTERVAL = 10 

# --- KONFIGURASI AUTOMATION & CHUNKING ---
STATE_FILE = f"state_project_{PROJECT_ID}.json"
CHUNK_SIZE = 2000 
START_BLOCK_DEFAULT = 10975295 

w3 = Web3(Web3.HTTPProvider(RPC_URL))
with open(ABI_PATH) as f:
    abi = json.load(f)['abi']
contract = w3.eth.contract(address=w3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)
account = w3.eth.account.from_key(PRIVATE_KEY)

# === Fungsi State Management ===
def load_last_block():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f).get("last_block", START_BLOCK_DEFAULT)
        except:
            return START_BLOCK_DEFAULT
    return START_BLOCK_DEFAULT

def save_last_block(block_number):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_block": block_number}, f)

# === SKEMA 2 DID-EFED: VERIFIKASI PLATFORM VC (OFF-CHAIN) ===
def verify_platform_vc(vc_data):
    """
    Membedah objek VC dan memverifikasi tanda tangan kriptografi secara off-chain.
    Memastikan kredensial diterbitkan resmi oleh Tim FedLang (Platform Admin).
    """
    try:
        subject = vc_data["credentialSubject"]
        proof = vc_data["proof"]
        
        # Rekonstruksi string subjek klaim sesuai format issue_vc.py
        subject_string = f"{subject['id']}:{subject['walletAddress']}:{subject['platformStatus']}"
        message = encode_defunct(text=subject_string)
        
        # Memulihkan (recover) alamat wallet penandatangan dari signature VC
        recovered_signer = Account.recover_message(message, signature=proof["signature"])
        
        # Validasi dengan kunci publik platform admin resmi
        if recovered_signer.lower() == PLATFORM_ADMIN_ADDRESS.lower():
            print(f"  [Identity Check] VC VALID. Terverifikasi diterbitkan oleh Tim FedLang untuk DID: {subject['id']}")
            return True
        else:
            print(f"  [Identity Check] VC REJECTED! Penandatangan ({recovered_signer}) bukan Otoritas FedLang.")
            return False
    except Exception as e:
        print(f"  [Identity Check] Gagal menguraikan dokumen Verifiable Credential: {e}")
        return False

# === Fungsi Tahap Verifikasi DID (Proof of Ownership) ===
def verify_did_signature(participant_addr, content_hash_bytes, signature_bytes):
    """
    Memastikan signature transaksi valid dan dibuat oleh pemilik wallet 
    yang terikat dengan did:key tersebut di Smart Contract.
    """
    try:
        # Ambil Identifier did:key dari Smart Contract untuk keperluan audit log
        did_data = contract.functions.participants(participant_addr).call()
        did_string = did_data[0]

        # Rekonstruksi pesan biner hash model
        message = encode_defunct(primitive=content_hash_bytes)
        
        # Recover address pengirim dari tanda tangan digital biner
        recovered_addr = Account.recover_message(message, signature=signature_bytes)
        is_valid = recovered_addr.lower() == participant_addr.lower()
        
        if is_valid:
            print(f"  [Identity] DID Signature Verified: {did_string} (Wallet cocok)")
        else:
            print(f"  [Identity] ALERT: Tanda tangan digital tidak cocok untuk wallet {participant_addr}")
            
        return is_valid
    except Exception as e:
        print(f"  [Identity] Error verifikasi tanda tangan DID: {e}")
        return False

# === Fungsi Evaluasi Kualitas Model AI ===
def evaluate_model_quality(local_path, global_path):
    print(f"  [Eval] Menghitung Skor Kontribusi Kualitas Model: {local_path}")
    
    local_weights = load_file(local_path)
    global_weights = load_file(global_path)
    
    def clean_keys(weights):
        return {k.replace("transformer.", ""): v for k, v in weights.items()}

    l_weights = clean_keys(local_weights)
    g_weights = clean_keys(global_weights)

    cos_sims = []
    distances = []
    
    for key in g_weights.keys():
        if "weight" in key:
            v_g = g_weights[key].flatten().float()
            v_l = l_weights[key].flatten().float()
            
            delta = v_l - v_g
            sim = F.cosine_similarity(v_g.unsqueeze(0), v_l.unsqueeze(0))
            cos_sims.append(sim.item())
            
            dist = torch.norm(delta, p=2)
            distances.append(dist.item())
            
    avg_cos = sum(cos_sims) / len(cos_sims) if cos_sims else 0
    avg_dist = sum(distances) / len(distances) if distances else 0
    
    if avg_cos <= 0:
        return 0
    
    effort_weight = min(1.0, avg_dist * 10)
    final_score = int(avg_cos * effort_weight * 100)
    
    print(f"  [Eval] Hasil -> Cosine Similarity: {avg_cos:.4f}, Weight Distance: {avg_dist:.4f} -> Skor: {final_score}")
    return max(0, min(100, final_score))

# === Fungsi Blockchain Utility & Sync ===
def get_logs_in_chunks(from_block, to_block, round_number):
    all_logs = []
    current_start = from_block
    
    while current_start <= to_block:
        current_end = min(current_start + CHUNK_SIZE - 1, to_block)
        print(f"  [Sync] Memindai blok: {current_start} sampai {current_end}...")
        
        try:
            logs = contract.events.ContributionSubmitted().get_logs(
                from_block=current_start,
                to_block=current_end,
                argument_filters={'projectId': PROJECT_ID, 'round': round_number}
            )
            all_logs.extend(logs)
            current_start = current_end + 1
        except Exception as e:
            print(f"  [Error] Gagal menarik chunk pada blok {current_start}: {e}")
            break
            
    return all_logs, current_start - 1

def download_from_ipfs(cid, filename="model.safetensors"):
    """Mengunduh berkas dari IPFS node lokal. Otomatis mengenali file teks JSON atau biner."""
    paths_to_try = [cid, f"{cid}/{filename}"]
    
    for path in paths_to_try:
        try:
            response = requests.post(f"{IPFS_RPC_URL}/cat?arg={path}", timeout=60)
            if response.status_code == 200:
                # Jika file berupa JSON metadata package, buat nama ekstensi .json
                if path == cid and (response.content.startswith(b'{') or response.content.startswith(b'[')):
                    temp_path = f"temp_{cid.replace('/', '_')}.json"
                else:
                    temp_path = f"temp_{cid.replace('/', '_')}.bin"
                    
                with open(temp_path, "wb") as f:
                    f.write(response.content)
                return temp_path
        except Exception:
            continue
            
    print(f"  [Error] Gagal mengunduh data dari IPFS untuk CID: {cid}")
    return None

def upload_to_ipfs(file_path):
    print(f"  [IPFS] Mengunggah berkas agregasi global: {file_path}")
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{IPFS_RPC_URL}/add", files=files, timeout=60)
            response.raise_for_status()
            return response.json()["Hash"]
    except Exception as e:
        print(f"  [Error] Gagal mengunggah hasil ke IPFS: {e}")
        return None

def verify_data_integrity(data_bytes, expected_hash_bytes):
    actual_hash = w3.keccak(data_bytes)
    return actual_hash == expected_hash_bytes

def federated_averaging(model_paths):
    print(f"--- Memulai Eksekusi Rumus FedAvg pada {len(model_paths)} Model Kontributor ---")
    
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

def finalize_on_chain(new_cid, participants, scores):
    print(f"  [Blockchain] Mengirim instruksi eksekusi pembagian dana (finalizeRound) ke Sepolia...")
    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.finalizeRound(PROJECT_ID, new_cid, participants, scores).build_transaction({
        'from': account.address, 'nonce': nonce, 'gas': 1000000, 'gasPrice': w3.eth.gas_price
    })
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)

# === Fungsi Utama Main Loop ===
def main():
    print(f"Aggregator Otomatis Aktif (Skema 2 W3C DID-eFed) untuk Project ID: {PROJECT_ID}")
    
    last_processed_block = load_last_block()
    
    while True:
        try:
            latest_block = w3.eth.block_number
            proj_data = contract.functions.projects(PROJECT_ID).call()
            current_round = proj_data[2]
            global_cid = proj_data[1]
            
            if latest_block > last_processed_block:
                print(f"\n--- Sinkronisasi Blok Jaringan: {last_processed_block} -> {latest_block} ---")
                
                # 1. Ambil log submisi terbaru lewat metode chunking
                all_logs, last_scanned = get_logs_in_chunks(last_processed_block + 1, latest_block, current_round)
                
                # 2. Periksa apakah batas minimal kuota partisipan proyek sudah terpenuhi
                ready = contract.functions.canAggregate(PROJECT_ID).call()
                
                if ready and len(all_logs) > 0:
                    print(f"=== Kriteria Terpenuhi. Memulai Pemrosesan Data Ronde {current_round} ===")
                    model_files = []
                    valid_addresses = []
                    quality_scores = []
                    
                    # Unduh file bobot model global ronde sebelumnya sebagai jangkar komparasi
                    global_path = download_from_ipfs(f"{global_cid}")

                    for log in all_logs:
                        addr = log.args.participant
                        contrib = contract.functions.contributions(PROJECT_ID, current_round, addr).call()
                        package_cid = contrib[0] # modelUpdateCID di kontrak pintar sekarang berisi CID paket JSON
                        
                        # A. Unduh paket metadata JSON kombinasi (Skema 2)
                        print(f"\n-> Mendeteksi Submisi dari Kontributor: {addr}")
                        package_path = download_from_ipfs(package_cid)
                        if not package_path: continue
                        
                        try:
                            with open(package_path, "r") as f:
                                package_data = json.load(f)
                            model_cid = package_data["model_update_cid"]
                            vc_data = package_data["verifiable_credential"]
                        except Exception as e:
                            print(f"  [Error] Struktur data paket JSON kontributor rusak: {e}. Eliminasi.")
                            if os.path.exists(package_path): os.remove(package_path)
                            continue
                        
                        if os.path.exists(package_path): os.remove(package_path)

                        # B. VALIDASI KEAMANAN UTAMA (Uji Keabsahan Platform VC - Anti-Sybil Gate)
                        if not verify_platform_vc(vc_data):
                            print(f"  [Sybil Attack Busted] Kontributor menduplikasi identitas palsu tanpa izin platform! Lewati.")
                            continue

                        # C. Validasi Tanda Tangan Kepemilikan DID & Integritas File Model Murni
                        if verify_did_signature(addr, contrib[1], contrib[2]):
                            # Unduh file bobot model biner .safetensors yang asli
                            path = download_from_ipfs(model_cid)
                            
                            if path:
                                with open(path, "rb") as f:
                                    model_bytes = f.read()
                                    
                                if verify_data_integrity(model_bytes, contrib[1]):
                                    # Evaluasi keselarasan gradien menggunakan Cosine Similarity & L2 Norm
                                    score = evaluate_model_quality(path, global_path)
                                    print(f"  [Quality Check] Hasil Akhir Evaluasi Model: {score}/100")
                                    
                                    model_files.append(path)
                                    valid_addresses.append(addr)
                                    quality_scores.append(score)
                                else:
                                    print("  [Error] Content Hash biner tidak klop dengan on-chain record! Data rusak/diracuni.")
                                    if os.path.exists(path): os.remove(path)

                    # 3. Jika jumlah kontributor yang memiliki identitas & bobot sah memenuhi kuota, lakukan FedAvg
                    if len(model_files) >= 3:
                        updated_model = federated_averaging(model_files)
                        new_cid = upload_to_ipfs(updated_model)
                        
                        if new_cid:
                            receipt = finalize_on_chain(new_cid, valid_addresses, quality_scores)
                            print(f"  [Success] Ronde Selesai Sempurna! Tercatat di Blok Resi: {receipt.transactionHash.hex()}")
                    else:
                        print("  [Cancel] Jumlah kontributor beridentitas sah di bawah batas minimum (MIN_CLIENTS). Agregasi ditangguhkan.")
                    
                    # Pembersihan file-file biner sementara di lokal agar penyimpanan hemat
                    if global_path and os.path.exists(global_path): os.remove(global_path)
                    for f in model_files: 
                        if os.path.exists(f): os.remove(f)
                
                # Perbarui checkpoint blok terakhir yang berhasil dipindai
                last_processed_block = last_scanned
                save_last_block(last_processed_block)
            
            else:
                print(f"Menunggu kontribusi baru... (Sinkron pada blok: {latest_block} | Ronde Proyek: {current_round})", end="\r")
                
        except Exception as e:
            print(f"\n  [Loop Error Exception] Terjadi kendala teknis: {e}")
            
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()