<script setup>
import { onMounted, watch } from 'vue'
import { useWeb3Store } from '../store/web3'
const web3Store = useWeb3Store()

onMounted(() => {
  if (web3Store.contract) {
    web3Store.fetchProjects()
  }
})

// Jika user baru connect di tengah jalan, langsung fetch
watch(() => web3Store.contract, (newContract) => {
  if (newContract) web3Store.fetchProjects()
})
</script>

<template>
  <div class="p-4">
    <!-- Jumbotron Alert untuk yang belum daftar DID -->
    <div v-if="web3Store.isConnected && !web3Store.isRegistered" class="alert alert-primary border-0 shadow-sm d-flex justify-content-between align-items-center">
      <div>
        <h5 class="alert-heading fw-bold">Identity Required!</h5>
        <p class="mb-0">Your wallet does not have a registered DID yet. Register now to start contributing.</p>
        <small class="text-muted">Generated ID: {{ web3Store.did }}</small>
      </div>
      <button @click="web3Store.doRegisterDID" class="btn btn-primary px-4">Register DID</button>
    </div>
    
    <div class="container py-2">
      <div class="d-flex justify-content-between align-items-end mb-4">
        <div>
          <h2 class="fw-bold">Global Projects</h2>
          <p class="text-muted mb-0">Explore collaborative AI training on Sepolia Testnet.</p>
        </div>
        <button @click="web3Store.fetchProjects" class="btn btn-sm btn-outline-primary">
          <i class="bi bi-arrow-clockwise"></i> Refresh
        </button>
      </div>

      <!-- EMPTY STATE -->
      <div v-if="web3Store.projects.length === 0 && !web3Store.isLoading" class="text-center py-5">
        <i class="bi bi-folder2-open display-1 text-secondary"></i>
        <h5 class="mt-3 text-muted">No projects found on this contract.</h5>
      </div>

      <!-- GRID PROJECT -->
      <div class="row g-4">
        <div v-for="project in web3Store.projects" :key="project.id" class="col-md-6 col-lg-4">
          <div class="card h-100 shadow-sm border-0 transition-up">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between mb-3">
                <span class="badge bg-primary bg-opacity-10 text-primary px-3 py-2">
                  ID: #{{ project.id }}
                </span>
                <span class="badge bg-dark text-white px-3 py-2">
                  Round {{ project.currentRound }}
                </span>
              </div>
              
              <h5 class="card-title fw-bold mb-3">{{ project.name }}</h5>
              
              <div class="mb-4">
                <label class="extra-small text-muted d-block mb-1 text-uppercase fw-bold">Current Model CID</label>
                <code class="d-block p-2 bg-light rounded text-truncate text-dark small border">
                  {{ project.modelCID }}
                </code>
              </div>

              <div class="d-flex justify-content-between align-items-center mt-auto">
                <div class="text-truncate me-2">
                  <small class="text-muted d-block extra-small">INITIATOR</small>
                  <small class="fw-medium text-dark">{{ project.initiator.substring(0, 6) }}...{{ project.initiator.substring(38) }}</small>
                </div>
                <router-link :to="'/project/' + project.id" class="btn btn-primary px-4 shadow-sm">
                  View Detail
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>