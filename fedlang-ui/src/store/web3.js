import { defineStore } from 'pinia'
import bs58 from 'bs58'
import { ethers } from 'ethers'
import contractAbi from '../assets/FederatedHub.json' // Sesuaikan path-nya

export const useWeb3Store = defineStore('web3', {
  state: () => ({
    address: null,
    did: null,
    isConnected: false,
    isLoading: false, // Indikator loading global
    contractAddress: "0xf8d750191a2dFc3904b29dA5c5a836C4699DdD3B", 
    contract: null,
    isRegistered: false,
    // Chain ID Sepolia adalah 11155111
    requiredChainId: "0xaa36a7",

    projects: [],
  }),
  actions: {
    async connectWallet() {
      if (!window.ethereum) return alert("Install MetaMask!")
      this.isLoading = true

      const chainId = await window.ethereum.request({ method: 'eth_chainId' });
        if (chainId !== this.requiredChainId) {
          alert("Harap pindah network MetaMask ke Sepolia!");
          return;
        }

      try {
        const provider = new ethers.BrowserProvider(window.ethereum)
        const signer = await provider.getSigner()
        const accounts = await provider.send("eth_requestAccounts", [])
        
        this.address = accounts[0]
        this.isConnected = true
        
        // Inisialisasi Kontrak agar bisa dipanggil fungsinya
        this.contract = new ethers.Contract(this.contractAddress, contractAbi.abi, signer)
        
        // Generate DID sederhana (Sesuai riset did:key kita)
        // this.did = `did:key:z6M(address)...`
        
        // Cek status registrasi di blockchain
        await this.checkRegistrationStatus()
      } catch (error) {
        console.error("User rejected connection", error)
      } finally {
        this.isLoading = false // Matikan loading apa pun hasilnya
      }
    },

    disconnectWallet() {
      // Reset semua state ke awal
      this.address = null
      this.did = null
      this.isConnected = false
      this.isRegistered = false
      this.contract = null
      // Catatan: Secara teknis MetaMask tidak bisa "diputus" paksa dari JS, 
      // tapi kita menghapus jejaknya dari state aplikasi kita agar seamless.
    },

    async checkRegistrationStatus() {
      if (!this.contract) return
      // this.isLoading = true
      try {
        const participant = await this.contract.participants(this.address)
        this.isRegistered = participant.isRegistered
        this.did = participant.did
      } catch (e) {
        console.error("Gagal cek status DID", e)
      } 
      // finally {
      //   this.isLoading = false
      // }
    },

    async generateDidKey(address) {
      // 1. Prefix multicodec untuk Secp256k1: 0xe701
      const prefix = new Uint8Array([0xe7, 0x01]);
      
      // 2. Ubah address hex menjadi bytes (20 bytes)
      // Catatan: Sesuai simulasi Python kamu yang pakai address-based
      const addressBytes = ethers.getBytes(address);
      
      // 3. Gabungkan prefix dan bytes
      const combined = new Uint8Array(prefix.length + addressBytes.length);
      combined.set(prefix);
      combined.set(addressBytes, prefix.length);
      
      // 4. Encode ke Base58 dengan prefix 'z' (Multibase)
      return 'did:key:z' + bs58.encode(combined);
    },

    async doRegisterDID() {
      if (!this.contract || !this.address) return
      this.isLoading = true
      try {
        // Kalkulasi DID secara otomatis (Identitas Algoritmik)
        const calculatedDid = await this.generateDidKey(this.address);
        this.did = calculatedDid; // Update state UI

        // Kirim ke Blockchain
        const tx = await this.contract.registerDID(calculatedDid);
        await tx.wait();
        
        this.isRegistered = true;
        alert(`Sukses! DID terdaftar: ${calculatedDid}`);
      } catch (error) {
          console.error("Registrasi gagal:", error);
      } finally {
        this.isLoading = false;
      }
    },

    async fetchProjects() {
      if (!this.contract) return;
      this.isLoading = true;
      try {
        const count = await this.contract.projectCount();
        const tempProjects = [];

        for (let i = 1; i <= count; i++) {
          const p = await this.contract.projects(i);
          // Mapping struct Solidity ke Object JavaScript
          tempProjects.push({
            id: i,
            initiator: p.initiator,
            modelCID: p.globalModelCID,
            name: p.name,                
            description: p.description,  
            modelName: p.modelName,      
            currentRound: p.roundNumber.toString(),
            isActive: p.isActive
          });
        }
        this.projects = tempProjects;
      } catch (error) {
        console.error("Gagal mengambil daftar proyek:", error);
      } finally {
        this.isLoading = false;
      }
    },

    async doCreateProject(modelCID, name, desc, modelName) {
      if (!this.contract) return;
      this.isLoading = true;
      try {
        // Memanggil fungsi createProject pada smart contract
        console.log("function called");
        console.log(modelCID, name, desc, modelName);
        const tx = await this.contract.createProject(modelCID, name, desc, modelName);
        
        console.log("Mendaftarkan proyek ke Sepolia...", tx.hash);
        
        await tx.wait(); // Menunggu konfirmasi blok
        alert("Proyek Berhasil Dibuat di Blockchain!");
        
        // Refresh daftar proyek setelah berhasil
        await this.fetchProjects(); 
        return true;
      } catch (error) {
        console.error("Gagal membuat proyek:", error);
        alert("Terjadi kesalahan saat membuat proyek.");
        return false;
      } finally {
        this.isLoading = false;
      }
    },
  }
})