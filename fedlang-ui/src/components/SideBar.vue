<script setup>
import { RouterLink } from 'vue-router'
import { useWeb3Store } from '../store/web3'
const web3Store = useWeb3Store()
</script>

<template>
  <nav class="col-md-3 col-lg-2 bg-dark text-white vh-100 p-3 position-fixed top-0 shadow d-flex flex-column">
    <h4 class="text-primary fw-bold mb-4 px-2">FedLang</h4>
    
    <ul class="nav flex-column gap-2">
      <li class="nav-item">
        <RouterLink to="/" class="nav-link text-white rounded px-3">
          <i class="bi bi-globe me-2"></i> Explore Projects
        </RouterLink>
      </li>
      <hr class="border-secondary">
      <li class="nav-item">
        <RouterLink to="/my-projects" class="nav-link text-white rounded px-3 text-truncate">
          <i class="bi bi-kanban me-2"></i> My Dashboard
        </RouterLink>
      </li>
    </ul>

    <!-- DID INFO -->
    <div v-if="web3Store.isConnected" class="mt-auto p-3 bg-secondary bg-opacity-25 rounded border border-secondary shadow-inner">
      <small class="text-info fw-bold d-block mb-1 text-uppercase small" style="letter-spacing: 1px;">Identity</small>
      <code class="text-light d-block mb-2" style="font-size: 0.7rem;">{{ web3Store.did }}</code>
      
      <span v-if="web3Store.isRegistered" class="badge bg-success w-100 py-2 small">
        <i class="bi bi-patch-check-fill me-1"></i> Verified
      </span>
      <button v-else @click="web3Store.doRegisterDID" class="btn btn-warning btn-sm w-100 fw-bold shadow-sm">
        Register DID
      </button>
    </div>
    <div v-else class="mt-auto p-3 bg-dark border border-secondary rounded text-center">
      <small class="text-muted small">Connect wallet to see DID</small>
    </div>

    <div v-if="web3Store.isRegistered" class="mt-3 p-3 bg-primary bg-opacity-10 rounded border border-primary border-opacity-25">
      <small class="text-primary fw-bold d-block mb-1">CLAIMABLE REWARD</small>
      <div class="d-flex justify-content-between align-items-center">
        <span class="fw-bold text-white">{{ web3Store.userReward }} ETH</span>
        <button 
          v-if="parseFloat(web3Store.userReward) > 0"
          @click="web3Store.doWithdraw" 
          class="btn btn-primary btn-sm py-0 px-2 small"
        >
          Claim
        </button>
      </div>
    </div>
  </nav>
</template>