<script setup>
import { useWeb3Store } from '../store/web3'
const web3Store = useWeb3Store()
</script>

<template>
  <header class="bg-white border-bottom p-3 d-flex justify-content-between align-items-center sticky-top shadow-sm"
  style="z-index: 1020;">
    <div class="d-flex flex-column">
      <span class="text-muted small fw-medium">Network: <b class="text-primary">Sepolia Testnet</b></span>
      <small class="text-secondary extra-small text-truncate" style="max-width: 200px;">SC: {{ web3Store.contractAddress }}</small>
    </div>

    <!-- WALLET BUTTON -->
    <div v-if="!web3Store.isConnected">
      <button @click="web3Store.connectWallet" class="btn btn-primary rounded-pill px-4 shadow-sm fw-bold btn-sm">
        <i class="bi bi-wallet2 me-2"></i> Connect Wallet
      </button>
    </div>
    <div v-else class="dropdown">
      <button class="btn btn-outline-dark rounded-pill px-4 fw-bold dropdown-toggle shadow-sm btn-sm" data-bs-toggle="dropdown">
        <i class="bi bi-person-circle me-2 text-primary"></i> 
        {{ web3Store.address.substring(0, 6) }}...{{ web3Store.address.substring(38) }}
      </button>
      <ul class="dropdown-menu dropdown-menu-end shadow border-0">
        <li><button @click="web3Store.disconnectWallet" class="dropdown-item text-danger py-2">
          <i class="bi bi-box-arrow-right me-2"></i> Disconnect
        </button></li>
      </ul>
    </div>
  </header>
</template>