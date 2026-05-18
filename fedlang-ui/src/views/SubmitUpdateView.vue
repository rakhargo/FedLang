<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWeb3Store } from '../store/web3'
import { ethers } from 'ethers'

const route = useRoute()
const router = useRouter()
const web3Store = useWeb3Store()

const projectId = route.params.id
const modelCID = ref('')
const contentHash = ref('') // Diisi manual dari hasil Keccak256 skrip Python
const signature = ref('')
const isSigned = ref(false)

// Step 1: Menandatangani Hash secara lokal (Off-chain)
const handleSign = async () => {
  if (!contentHash.value.startsWith('0x')) {
    return alert("Content Hash harus diawali dengan 0x (format hex 32 bytes)")
  }
  
  web3Store.isLoading = true
  try {
    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    
    // Menandatangani hash model sesuai standar EIP-191
    // Ini yang akan diverifikasi oleh aggregator.py nantinya
    const sign = await signer.signMessage(ethers.getBytes(contentHash.value))
    
    signature.value = sign
    isSigned.value = true
    alert("Signature berhasil dibuat secara lokal!")
  } catch (error) {
    console.error("Signing failed", error)
    alert("Gagal menandatangani data.")
  } finally {
    web3Store.isLoading = false
  }
}

// Step 2: Mengirim ke Blockchain (On-chain)
const handleSubmit = async () => {
  const success = await web3Store.doSubmitUpdate(
    projectId,
    modelCID.value,
    contentHash.value,
    signature.value
  )
  if (success) {
    router.push(`/project/${projectId}`)
  }
}
</script>

<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-lg-6">
        <div class="card shadow border-0">
          <div class="card-body p-4 p-md-5">
            <h4 class="fw-bold mb-4">Submit Local Update</h4>
            
            <div class="alert alert-warning py-2 small mb-4">
              <i class="bi bi-exclamation-triangle-fill me-2"></i>
              Pastikan Anda telah melakukan <b>Local Training</b> dan memiliki CID serta Hash yang valid.
            </div>

            <form @submit.prevent="handleSubmit">
              <div class="mb-3">
                <label class="form-label small fw-bold text-muted">PROJECT ID</label>
                <input type="text" class="form-control bg-light" :value="projectId" disabled>
              </div>

              <div class="mb-3">
                <label class="form-label small fw-bold">SUBMISSION PACKAGE CID (IPFS)</label>
                <input v-model="modelCID" type="text" class="form-control" placeholder="QmPaketGabungan..." required :disabled="isSigned">
                <div class="form-text extra-small text-primary">Masukkan Package CID (Kombinasi Model + VC) dari skrip Python.</div>
              </div>

              <div class="mb-3">
                <label class="form-label small fw-bold">CONTENT HASH (Keccak256)</label>
                <input v-model="contentHash" type="text" class="form-control" placeholder="0x..." required :disabled="isSigned">
                <div class="form-text extra-small text-primary">Masukkan data Hash Hex dari skrip Python.</div>
              </div>

              <div v-if="isSigned" class="mb-3 p-3 bg-light border rounded">
                <label class="form-label small fw-bold text-success"><i class="bi bi-check-circle-fill me-1"></i> SIGNATURE GENERATED</label>
                <code class="d-block extra-small text-break">{{ signature }}</code>
              </div>

              <div class="d-grid gap-2 mt-4">
                <button 
                  v-if="!isSigned" 
                  type="button" 
                  @click="handleSign" 
                  class="btn btn-dark fw-bold"
                  :disabled="!modelCID || !contentHash || web3Store.isLoading"
                >
                  <span v-if="web3Store.isLoading" class="spinner-border spinner-border-sm me-2"></span>
                  Step 1: Sign with Wallet
                </button>

                <button 
                  v-else 
                  type="submit" 
                  class="btn btn-primary fw-bold"
                  :disabled="web3Store.isLoading"
                >
                  <span v-if="web3Store.isLoading" class="spinner-border spinner-border-sm me-2"></span>
                  Step 2: Submit to Blockchain
                </button>
                
                <button v-if="isSigned" type="button" @click="isSigned = false" class="btn btn-link btn-sm text-muted">
                  Edit Data
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>