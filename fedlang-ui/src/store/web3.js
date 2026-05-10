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
    contractAddress: "0x5d3763ADc9EFD4098279217584F66D554CD30f7B", 
    contract: null,
    isRegistered: false,
    // Chain ID Sepolia adalah 11155111
    requiredChainId: "0xaa36a7",
    projects: [],
    userReward: "0",
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

    // Fungsi cek saldo reward
    async checkUserReward() {
      if (!this.contract || !this.address) return;
      const balance = await this.contract.rewards(this.address);
      this.userReward = ethers.formatEther(balance);
    },

    async doCreateProject(modelCID, name, desc, modelName, budget) {
      if (!this.contract) return;
      this.isLoading = true;
      try {
        // Mengirim ETH sebagai budget proyek (payable)
        const tx = await this.contract.createProject(modelCID, name, desc, modelName, {
          value: ethers.parseEther(budget.toString()) 
        });
        console.log("Mendaftarkan proyek ke Sepolia...", tx.hash);
        await tx.wait();
        alert("Proyek Berhasil Dibuat dengan Budget!");

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

    async doWithdraw() {
      this.isLoading = true;
      try {
        const tx = await this.contract.withdrawRewards();
        await tx.wait();
        await this.checkUserReward(); // Refresh saldo
        alert("Reward berhasil ditarik ke wallet!");
      } catch (error) {
        alert("Gagal menarik reward.");
      } finally {
        this.isLoading = false;
      }
    },

    async fetchProjectDetail(projectId) {
      if (!this.contract) return null;
      this.isLoading = true;
      try {
        const p = await this.contract.projects(projectId);
        const roundData = await this.contract.projectRounds(projectId, p.roundNumber);
        const isUserJoined = await this.contract.isRegistered(projectId, this.address);
        
        const contribution = await this.contract.contributions(projectId, p.roundNumber, this.address);
        const hasSubmitted = contribution.exists; // Field 'exists' dari struct Contribution

        return {
          id: projectId,
          initiator: p.initiator,
          modelCID: p.globalModelCID,
          name: p.name,
          description: p.description,
          modelName: p.modelName,
          currentRound: p.roundNumber.toString(),
          isActive: p.isActive,
          submissionCount: roundData.submissionCount.toString(),
          isUserJoined: isUserJoined,
          hasSubmitted: hasSubmitted
        };
      } catch (error) {
        console.error("Gagal ambil detail proyek:", error);
      } finally {
        this.isLoading = false;
      }
    },

    async doJoinProject(projectId) {
      this.isLoading = true;
      try {
        const tx = await this.contract.joinProject(projectId);
        await tx.wait();
        alert("Berhasil bergabung ke proyek!");
        return true;
      } catch (error) {
        alert(error.reason || "Gagal bergabung.");
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    async doSubmitUpdate(projectId, cid, contentHash, signature) {
      if (!this.contract) return;
      this.isLoading = true;
      try {
        // Pastikan hash diawali 0x dan signature dalam format bytes (hex)
        const tx = await this.contract.submitUpdate(
          projectId, 
          cid, 
          contentHash, 
          signature
        );
        await tx.wait();
        alert("Submisi berhasil! Kontribusi Anda telah tercatat di blockchain.");
        return true;
      } catch (error) {
        console.error("Gagal submit:", error);
        alert(error.reason || "Gagal mengirim submisi ke blockchain.");
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    async doFinalizeProject(projectId) {
      this.isLoading = true;
      try {
        const tx = await this.contract.finalizeProject(projectId);
        await tx.wait();
        alert("Proyek telah difinalisasi!");
        return true;
      } catch (error) {
        alert(error.reason || "Gagal finalisasi.");
        return false;
      } finally {
        this.isLoading = false;
      }
    }
  }
})