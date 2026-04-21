<script setup>
import { useWeb3Store } from '../store/web3'
const web3Store = useWeb3Store()
</script>

<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark border-bottom border-primary">
    <div class="container">
      <router-link class="navbar-brand fw-bold text-primary" to="/">FEDLANG</router-link>
      
      <div class="ms-auto d-flex align-items-center">
        <div v-if="web3Store.isConnected" class="me-3 text-end d-none d-md-block">
          <div class="text-white small">Identity Verified</div>
          <div class="text-info extra-small" style="font-size: 0.7rem;">{{ web3Store.did }}</div>
        </div>
        
        <button v-if="!web3Store.isConnected" @click="web3Store.connectWallet" class="btn btn-outline-primary btn-sm">
          Connect Wallet
        </button>
        <button v-else class="btn btn-primary btn-sm">
          {{ web3Store.address.substring(0, 6) }}...{{ web3Store.address.substring(38) }}
        </button>
      </div>
    </div>
  </nav>
</template>