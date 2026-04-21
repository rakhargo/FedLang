import { defineStore } from 'pinia'
import { ethers } from 'ethers'

export const useWeb3Store = defineStore('web3', {
  state: () => ({
    address: null,
    did: null,
    isConnected: false,
  }),
  actions: {
    async connectWallet() {
      if (window.ethereum) {
        const provider = new ethers.BrowserProvider(window.ethereum)
        const accounts = await provider.send("eth_requestAccounts", [])
        this.address = accounts[0]
        this.isConnected = true
        // Simulasi Generate DID Key sederhana
        this.did = `did:key:z6M${this.address.substring(2, 15)}...`
      } else {
        alert("Plese install MetaMask!")
      }
    }
  }
})
