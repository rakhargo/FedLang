<script setup>
import { ref } from 'vue'
import { useWeb3Store } from '../store/web3'
import { useRouter } from 'vue-router'

const web3Store = useWeb3Store()
const router = useRouter()

const projectName = ref('')
const modelName = ref('')
const description = ref('')
const modelCID = ref('')

const handleSubmit = async () => {
    // console.log(modelCID.value, projectName.value, description.value, modelName.value)
  const success = await web3Store.doCreateProject(modelCID.value, projectName.value, description.value, modelName.value)
  if (success) {
    router.push('/') // Kembali ke dashboard jika sukses
  }
}
</script>

<template>
  <div class="container py-2">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="d-flex align-items-center mb-4">
          <router-link to="/" class="btn btn-link text-decoration-none p-0 me-3">
            <i class="bi bi-arrow-left fs-4"></i>
          </router-link>
          <h2 class="fw-bold mb-0">Initiate New LLM Project</h2>
        </div>

        <div class="card shadow-sm border-0">
          <div class="card-body p-4 p-md-5">
            <form @submit.prevent="handleSubmit">
            
              <div class="mb-4">
                <label class="form-label fw-bold text-dark">Project Name</label>
                <input v-model="projectName" type="text" class="form-control" placeholder="Indonesian NLP Research" required>
                <!-- <div class="form-text"></div> -->
              </div>

              <div class="mb-4">
                <label class="form-label fw-bold text-dark">Model Architecture</label>
                <input v-model="modelName" type="text" class="form-control" placeholder="GPT-2 Small (124M)" required>
                <!-- <div class="form-text"></div> -->
              </div>

              <!-- Deskripsi Proyek -->
              <div class="mb-4">
                <label class="form-label fw-bold text-dark">Project Description</label>
                <textarea 
                  v-model="description" 
                  class="form-control form-control-lg" 
                  rows="3" 
                  placeholder="e.g., Fine-tuning GPT-2 for Indonesian Sentiment Analysis"
                  required
                ></textarea>
                <!-- <div class="form-text">Jelaskan tujuan projec kolaboratif ini secara singkat.</div> -->
              </div>

              <!-- Base Model CID -->
              <div class="mb-4">
                <label class="form-label fw-bold text-dark">Initial Model CID (IPFS)</label>
                <div class="input-group input-group-lg">
                  <span class="input-group-text bg-light text-muted border-end-0">
                    <i class="bi bi-box-seam"></i>
                  </span>
                  <input 
                    v-model="modelCID" 
                    type="text" 
                    class="form-control border-start-0 ps-0" 
                    placeholder="Qm..." 
                    required
                  >
                </div>
                <!-- <div class="form-text">Masukkan Hash konten dari model dasar (.safetensors) yang tersimpan di IPFS.</div> -->
              </div>

              <!-- Info Panel -->
              <div class="bg-primary bg-opacity-10 p-3 rounded-3 mb-4">
                <div class="d-flex gap-3 text-primary">
                  <i class="bi bi-info-circle-fill fs-5"></i>
                  <small>
                    Dengan membuat proyek ini, Anda bertindak sebagai <b>Inisiator</b>. 
                    Anda bertanggung jawab untuk memicu agregasi ronde setelah partisipan mencukupi.
                  </small>
                </div>
              </div>

              <!-- Submit Button -->
              <div class="d-grid">
                <button 
                  type="submit" 
                  class="btn btn-primary btn-lg fw-bold shadow-sm"
                  :disabled="web3Store.isLoading"
                >
                  <span v-if="web3Store.isLoading" class="spinner-border spinner-border-sm me-2"></span>
                  Deploy to Sepolia
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>