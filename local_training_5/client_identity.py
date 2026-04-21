import base58
from eth_account import Account
from eth_account.messages import encode_defunct

def generate_did_key(public_key_bytes):
    """
    Mengonversi public key menjadi format did:key (W3C Standard).
    Menggunakan prefix multicodec untuk Secp256k1 (0xe701).
    """
    # 0xe7 0x01 adalah prefix multicodec untuk kunci publik Secp256k1
    prefix = b'\xe7\x01'
    codec_key = prefix + public_key_bytes
    # Encode ke Base58 (Multibase prefix 'z' untuk Base58BTC)
    did_identifier = base58.b58encode(codec_key).decode()
    return f"did:key:z{did_identifier}"

def sign_model_update(private_key, content_hash_hex):
    """Menandatangani hash model menggunakan kunci privat klien."""
    message = encode_defunct(hexstr=content_hash_hex)
    signed_message = Account.sign_message(message, private_key=private_key)
    return signed_message.signature.hex()

# --- SIMULASI DI LAB ---
PRIVATE_KEY = "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6" # Private key komputer lab
acct = Account.from_key(PRIVATE_KEY)

# 1. Buat DID (Cukup sekali saat registrasi)
# Ambil kunci publik (64 bytes non-compressed)
pub_key_bytes = acct.key.hex() # atau cara lain mendapatkan pubkey bytes
did_string = generate_did_key(acct._address.encode()) # Sederhananya kita pakai address-based
print(f"DID Anda: {did_string}")

# 2. Setelah training, tanda tangani hash model
model_hash = "e4165b31c118470a94276fbec7185c56a198479da50c63a1bc542277c8e29756" # Hasil Keccak256 dari model.safetensors
signature = sign_model_update(PRIVATE_KEY, model_hash)
print(f"Signature untuk submisi: {signature}")