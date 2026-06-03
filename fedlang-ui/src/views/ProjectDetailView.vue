<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWeb3Store } from '../store/web3'
import { ethers } from 'ethers'

const route = useRoute()
const router = useRouter()
const web3Store = useWeb3Store()
const project = ref(null)

const isInitiator = computed(() => {
  return project.value && web3Store.address?.toLowerCase() === project.value.initiator.toLowerCase()
})

const loadData = async () => {
  const data = await web3Store.fetchProjectDetail(route.params.id)
  if (data) {
    project.value = data
    // Cek reward user setiap kali data project dimuat
    await web3Store.checkUserReward()
  }
}

const handleJoin = async () => {
  const success = await web3Store.doJoinProject(project.value.id)
  if (success) loadData()
}

const handleFinalize = async () => {
  const success = await web3Store.doFinalizeProject(project.value.id)
  if (success) loadData()
}

const handleWithdraw = async () => {
  await web3Store.doWithdraw()
}

// Re-fetch data jika contract baru siap (misal setelah refresh)
onMounted(() => {
  if (web3Store.contract) {
    loadData()
  }
})

watch(() => web3Store.contract, (newVal) => {
  if (newVal) loadData()
})
</script>

<template>
  <div v-if="project" class="container py-2">
    <div class="d-flex justify-content-between align-items-start mb-4">
      <div>
        <div class="d-flex align-items-center gap-2 mb-2">
          <span v-if="project.isActive" class="badge bg-success">Active Phase</span>
          <span v-else class="badge bg-secondary">Finalized</span>
          <span class="text-muted small">Project ID: #{{ project.id }}</span>
        </div>
        <h2 class="fw-bold">{{ project.name }}</h2>
        <p class="text-secondary"><i class="bi bi-cpu me-1"></i> Base Model: {{ project.modelName }}</p>
      </div>
      
      <div v-if="isInitiator && project.isActive">
        <button @click="handleFinalize" class="btn btn-outline-danger fw-bold shadow-sm">
          <i class="bi bi-stop-circle me-2"></i> Finalize Research
        </button>
      </div>
    </div>

    <div class="row g-4">
      <div class="col-lg-8">
        <div class="card border-0 shadow-sm mb-4">
          <div class="card-body p-4">
            <h5 class="fw-bold mb-3">Project Description</h5>
            <p class="text-dark">{{ project.description }}</p>
            <hr class="my-4">
            <div class="row text-center">
              <div class="col border-end">
                <small class="text-muted d-block text-uppercase extra-small fw-bold">Current Round</small>
                <span class="fs-4 fw-bold text-primary">{{ project.currentRound }}</span>
              </div>
              <div class="col border-end">
                <small class="text-muted d-block text-uppercase extra-small fw-bold">Submissions</small>
                <span class="fs-4 fw-bold text-primary">{{ project.submissionCount }} / {{ project.joinedCount || '0' }}</span>
              </div>
              <div class="col ">
                <small class="text-muted d-block text-uppercase extra-small fw-bold">Project Funds (Total / Remaining)</small>
                <div class="d-flex justify-content-center align-items-baseline gap-2">
                  <span class="fs-4 fw-bold text-dark">{{ project.totalBudget }}</span>
                  <span class="text-muted">/</span>
                  <span class="fs-4 fw-bold text-success">{{ project.remainingBudget }} ETH</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card border-0 shadow-sm bg-dark text-white">
          <div class="card-body p-4">
            <h6 class="text-info fw-bold mb-3">
              <i class="bi bi-hdd-network me-2"></i> Latest Global Model CID (Round {{ project.currentRound - 1 }})
            </h6>
            <div class="d-flex align-items-center bg-black bg-opacity-50 p-3 rounded border border-secondary">
              <code class="text-light text-truncate flex-grow-1">{{ project.modelCID }}</code>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-4">
        <div v-if="!isInitiator && web3Store.isRegistered" class="card border-0 shadow-sm mb-4 bg-primary bg-opacity-10">
          <div class="card-body p-4">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <h6 class="fw-bold text-primary mb-0">Your Rewards</h6>
              <i class="bi bi-gift-fill text-primary"></i>
            </div>
            <h3 class="fw-bold mb-3">{{ web3Store.userReward }} <small class="fs-6">ETH</small></h3>
            <button 
              v-if="parseFloat(web3Store.userReward) > 0" 
              @click="handleWithdraw" 
              class="btn btn-primary w-100 fw-bold shadow-sm"
              :disabled="web3Store.isLoading"
            >
              Withdraw to Wallet
            </button>
            <p v-else class="extra-small text-muted mb-0">Rewards will be available after the round is finalized.</p>
          </div>
        </div>

        <div class="card border-0 shadow-sm position-sticky" style="top: 100px;">
          <div class="card-body p-4">
            <h5 class="fw-bold mb-4">Control Panel</h5>
            
            <div v-if="isInitiator" class="text-center py-2">
              <div class="p-3 bg-light border rounded-3 mb-3">
                <i class="bi bi-shield-lock text-primary fs-3 d-block mb-2"></i>
                <span class="text-dark fw-bold">Initiator Authority</span>
                <p class="extra-small text-muted mb-0 mt-1">You are responsible for triggering aggregation when quorum is met.</p>
              </div>
              <div v-if="project.isActive" class="alert alert-warning small border-0">
                Use <b>aggregator.py</b> script to process rounds automatically.
              </div>
            </div>

            <div v-else-if="!project.isUserJoined && project.isActive" class="d-grid gap-3">
              <div class="alert alert-info small border-0 m-0">
                Join to contribute and earn ETH incentives based on your model quality.
              </div>
              <button @click="handleJoin" class="btn btn-primary btn-lg fw-bold shadow-sm" :disabled="!web3Store.isRegistered">
                Join Research Group
              </button>
              <small v-if="!web3Store.isRegistered" class="text-danger text-center">
                * Register your DID first in the sidebar.
              </small>
            </div>

            <div v-else-if="project.isUserJoined && project.isActive" class="d-grid gap-3">
              <div v-if="project.hasSubmitted" class="text-center p-3 bg-info bg-opacity-10 border border-info rounded-3">
                <i class="bi bi-cloud-check-fill text-info fs-3 d-block mb-2"></i>
                <span class="text-info fw-bold">Contribution Stored</span>
                <p class="extra-small text-muted mb-0 mt-1">
                  You have submitted your model update for this round. Waiting for round finalization.
                </p>
              </div>

              <div v-else>
                <div class="p-3 bg-success bg-opacity-10 border border-success rounded-3 text-center mb-3">
                  <i class="bi bi-check-circle-fill text-success me-2"></i>
                  <span class="text-success fw-bold">Active Contributor</span>
                </div>
                <router-link :to="`/submit/${project.id}`" class="btn btn-primary btn-lg w-100 fw-bold shadow-sm">
                  Submit Local Update
                </router-link>
              </div>
            </div>

            <div v-else class="text-center py-3">
              <i class="bi bi-lock-fill display-4 text-muted mb-3 d-block"></i>
              <p class="text-muted fw-bold">Project Finalized</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>