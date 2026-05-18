import os
import json
import time
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from dotenv import load_dotenv

load_dotenv()

# === Konfigurasi Jaringan & Kontrak ===
RPC_URL = os.getenv("ANKR_SEPOLIA_RPC_URL")
CONTRACT_ADDRESS = "0xAc4f998dC647f8dBA4Ad9b6Bd5F0C1F3a83EA33b"
ABI_PATH = "./FederatedHub.json"

# Kunci Privat Tim FedLang selaku Platform Admin / Issuer Global
ADMIN_PRIVATE_KEY = os.getenv("DEV_PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
with open(ABI_PATH) as f:
    abi = json.load(f)['abi']
contract = w3.eth.contract(address=w3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)
admin_account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

def issue_verifiable_credential(client_address, client_did):
    """
    Menerbitkan berkas Verifiable Credential (VC) secara off-chain 
    dan memberikan verifikasi status secara on-chain di Smart Contract.
    """
    print(f"\n=== Memulai Proses Penerbitan VC untuk Klien ===")
    print(f"Target Wallet : {client_address}")
    print(f"Target DID    : {client_did}")
    
    # ------------------------------------------------------------------
    # 1. AKSI ON-CHAIN: Mengubah Status Klien menjadi isVerified = true
    # ------------------------------------------------------------------
    print("\n[1/2] Mengirim transaksi verifikasi ke Sepolia Blockchain...")
    try:
        # Cek apakah partisipan sudah terdaftar DID-nya di kontrak
        part_data = contract.functions.participants(w3.to_checksum_address(client_address)).call()
        if not part_data[1]: # part_data[1] adalah isRegistered
            print("  [Error] Klien belum memanggil registerDID() di Smart Contract! Batalkan.")
            return False
        
        if part_data[2]: # part_data[2] adalah isVerified
            print("  [Notice] Klien sudah terverifikasi secara on-chain sebelumnya. Lanjut buat file VC.")
        else:
            nonce = w3.eth.get_transaction_count(admin_account.address)
            tx = contract.functions.verifyParticipant(w3.to_checksum_address(client_address)).build_transaction({
                'from': admin_account.address,
                'nonce': nonce,
                'gas': 150000,
                'gasPrice': w3.eth.gas_price
            })
            signed_tx = w3.eth.account.sign_transaction(tx, ADMIN_PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"  [Blockchain] Transaksi dikirim. Menunggu resi...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"  [Success] Status On-chain Terverifikasi! TX: {receipt.transactionHash.hex()}")
            
    except Exception as e:
        print(f"  [Error On-Chain] Gagal melakukan verifikasi platform: {e}")
        return False

    # ------------------------------------------------------------------
    # 2. AKSI OFF-CHAIN: Membuat Kredensial Terverifikasi (W3C Standard)
    # ------------------------------------------------------------------
    print("\n[2/2] Membikin berkas Verifiable Credential (JSON)...")
    
    # Membuat struktur subjek klaim yang unik
    # Format data yang akan ditandatangani untuk mencegah manipulasi isi VC
    subject_string = f"{client_did}:{client_address.lower()}:VerifiedGlobalContributor"
    message = encode_defunct(text=subject_string)
    
    # Menandatangani subjek menggunakan Kunci Privat Admin (Platform Identity Provider)
    signed_message = Account.sign_message(message, private_key=ADMIN_PRIVATE_KEY)
    signature_hex = signed_message.signature.hex()
    
    # Menyusun struktur dokumen JSON VC resmi
    vc_document = {
        "context": ["https://www.w3.org/2018/credentials/v1"],
        "id": f"https://fedlang.id/credentials/{client_address.lower()}", # hanya contoh
        "type": ["VerifiableCredential", "FedLangVerifiedHumanCredential"],
        "issuer": f"did:ethr:{admin_account.address.lower()}",
        "issuanceDate": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "credentialSubject": {
            "id": client_did,
            "walletAddress": client_address.lower(),
            "platformStatus": "VerifiedGlobalContributor"
        },
        "proof": {
            "type": "Secp256k1Signature2021",
            "signature": signature_hex
        }
    }
    
    # Menyimpan file kredensial secara lokal
    output_filename = f"platform_credential_{client_address.lower()[:6]}.json"
    with open(output_filename, "w") as f:
        json.dump(vc_document, f, indent=2)
        
    print(f"  [Success] Berkas VC Berhasil Dibuat: {output_filename}")
    print("=== Proses Selesai Sempurna ===")
    return True

if __name__ == "__main__":
    # SIMULASI INTERAKTIF: Jalankan di terminal untuk menguji pendaftaran klien
    print("--- FEDLANG CREDENTIAL ISSUER TOOLS ---")
    target_wallet = input("Masukkan Alamat Wallet Client (0x...): ").strip()
    target_did = input("Masukkan string did:key Client (did:key:...): ").strip()
    
    if target_wallet and target_did:
        issue_verifiable_credential(target_wallet, target_did)
    else:
        print("Input tidak boleh kosong!")