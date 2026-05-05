<script setup>
import { RouterView } from 'vue-router'
import { useWeb3Store } from './store/web3'
import Sidebar from './components/SideBar.vue'
import Navbar from './components/NavBar.vue'
import { onMounted } from 'vue'

const web3Store = useWeb3Store()

// Opsional: Cek koneksi saat halaman di-refresh
onMounted(() => {
  if (window.ethereum && window.ethereum.selectedAddress) {
    web3Store.connectWallet()
  }
})
</script>

<template>
  <div class="container-fluid p-0 overflow-hidden">
    <!-- LOADING OVERLAY -->
    <div v-if="web3Store.isLoading" class="loading-overlay d-flex flex-column justify-content-center align-items-center">
      <div class="spinner-border text-primary mb-3" role="status"></div>
      <h5 class="text-white fw-bold">Processing...</h5>
    </div>

    <div class="row g-0">
      <Sidebar />
      <main class="col-md-9 ms-sm-auto col-lg-10 bg-light min-vh-100">
        <Navbar />
        <div class="p-4">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<style>
/* Memastikan RouterLink active punya style khusus */
.router-link-active {
  background-color: #0d6efd !important;
  font-weight: bold;
}
.nav-link:hover:not(.router-link-active) {
  background-color: rgba(255, 255, 255, 0.1);
}
.extra-small {
  font-size: 0.6rem;
}
/* Style Indikator Loading */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  z-index: 9999;
}

.shadow-inner {
  box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
}

</style>