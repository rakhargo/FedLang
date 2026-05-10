<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWeb3Store } from '../store/web3'

const route = useRoute()
const router = useRouter()
const web3Store = useWeb3Store()
const project = ref(null)

const isInitiator = computed(() => {
  return project.value && web3Store.address?.toLowerCase() === project.value.initiator.toLowerCase()
})

const loadData = async () => {
  const data = await web3Store.fetchProjectDetail(route.params.id)
  if (data) project.value = data
}

const handleJoin = async () => {
  const success = await web3Store.doJoinProject(project.value.id)
  if (success) loadData()
}

const handleFinalize = async () => {
  const success = await web3Store.doFinalizeProject(project.value.id)
  if (success) loadData()
}

const handleAggregate = async () => {
  const success = await web3Store.doAggregate(project.value.id)
  if (success) loadData()
}

onMounted(() => {
  // console.log(project.value)
  if (web3Store.contract) {
    loadData()
  }
})

</script>

<template>
  <div v-if="project" class="container py-2">
    <!-- Header Detail -->
    <div class="d-flex justify-content-between align-items-start mb-4">
      <div>
        <div class="d-flex align-items-center gap-2 mb-2">
          <span v-if="project.isActive" class="badge bg-success">Active</span>
          <span v-else class="badge bg-secondary">Finalized</span>
          <span class="text-muted small">Project ID: #{{ project.id }}</span>
        </div>
        <h2 class="fw-bold">{{ project.name }}</h2>
        <p class="text-secondary"><i class="bi bi-cpu me-1"></i> Base Model: {{ project.modelName }}</p>
      </div>
      
      <!-- Action Buttons for Initiator -->
      <div v-if="isInitiator && project.isActive">
        <button @click="handleFinalize" class="btn btn-outline-danger fw-bold">
          <i class="bi bi-stop-circle me-2"></i> Finalize Project
        </button>
      </div>
    </div>

    <div class="row g-4">
      <!-- Left Column: Info -->
      <div class="col-lg-8">
        <div class="card border-0 shadow-sm mb-4">
          <div class="card-body p-4">
            <h5 class="fw-bold mb-3">Description</h5>
            <p class="text-dark">{{ project.description }}</p>
            <hr>
            <div class="row text-center py-2">
              <div class="col-4 border-end">
                <small class="text-muted d-block text-uppercase extra-small fw-bold">Current Round</small>
                <span class="fs-4 fw-bold text-primary">{{ project.currentRound }}</span>
              </div>
              <div class="col-4 border-end">
                <small class="text-muted d-block text-uppercase extra-small fw-bold">Submissions</small>
                <span class="fs-4 fw-bold text-primary">{{ project.submissionCount }} / 3 (template)</span>
              </div>
              <div class="col-4">
                <small class="text-muted d-block text-uppercase extra-small fw-bold">Network</small>
                <span class="badge bg-light text-dark border mt-1">Sepolia</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Global Model Status -->
        <div class="card border-0 shadow-sm bg-dark text-white">
          <div class="card-body p-4">
            <h6 class="text-info fw-bold mb-3"><i class="bi bi-hdd-network me-2"></i> Current Global Model CID</h6>
            <div class="d-flex align-items-center bg-black bg-opacity-50 p-3 rounded border border-secondary">
              <code class="text-light text-truncate flex-grow-1">{{ project.modelCID }}</code>
              <button class="btn btn-sm btn-outline-info ms-2" @click="copyCID">Copy</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Control Panel -->
      <div class="col-lg-4">
        <div class="card border-0 shadow-sm position-sticky" style="top: 100px;">
          <div class="card-body p-4">
            <h5 class="fw-bold mb-4">Control Panel</h5>
            
            <!-- KONDISI 1: Jika user adalah Inisiator -->
            <div v-if="isInitiator" class="text-center py-2">
              <div class="p-3 bg-primary bg-opacity-10 border border-primary rounded-3 mb-3">
                <i class="bi bi-shield-lock-fill text-primary fs-3 d-block mb-2"></i>
                <span class="text-primary fw-bold">Project Owner Mode</span>
                <p class="extra-small text-muted mb-0 mt-1">Anda memiliki otoritas penuh untuk mengelola ronde dan finalisasi proyek.</p>
              </div>
              
              <div v-if="project.isActive" class="d-grid gap-2">
                <button @click="handleAggregate" class="btn btn-danger fw-bold">
                  <i class="bi bi-stop-circle me-2"></i> Agregasi TEMP
                </button>
                <!-- Tombol Finalize Round muncul jika kuota tercapai -->
                <button v-if="project.submissionCount >= 3" class="btn btn-outline-primary fw-bold">
                  Finalize Current Round
                </button>
              </div>
            </div>

            <!-- KONDISI 2: Jika user BUKAN Inisiator dan BELUM Join -->
            <div v-else-if="!project.isUserJoined && project.isActive" class="d-grid gap-3">
              <div class="alert alert-info small border-0">
                Daftarkan diri Anda untuk berkontribusi pada pelatihan model ini.
              </div>
              <button @click="handleJoin" class="btn btn-primary btn-lg fw-bold shadow-sm" :disabled="!web3Store.isRegistered">
                Join Project
              </button>
            </div>

            <!-- KONDISI 3: Jika user BUKAN Inisiator dan SUDAH Join -->
            <div v-else-if="project.isUserJoined && project.isActive" class="d-grid gap-3">
              <div class="p-3 bg-success bg-opacity-10 border border-success rounded-3 text-center">
                <i class="bi bi-check-circle-fill text-success me-2"></i>
                <span class="text-success fw-bold">Active Contributor</span>
              </div>
              <button class="btn btn-primary btn-lg fw-bold shadow-sm">
                Submit Local Update
              </button>
            </div>

            <!-- KONDISI 4: Proyek Selesai -->
            <div v-else class="text-center py-3">
              <i class="bi bi-lock-fill display-4 text-muted mb-3 d-block"></i>
              <p class="text-muted fw-bold">Proyek ini telah selesai.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>