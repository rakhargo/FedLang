<script setup>
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div class="container-fluid">
    <div class="row">
      <nav class="col-md-3 col-lg-2 d-md-block bg-dark sidebar vh-100 p-3 collapse">
        <h5 class="text-primary mb-4">FedLang Node</h5>
        <ul class="nav flex-column">
          <li class="nav-item mb-2">
            <RouterLink to="/" class="nav-link text-white">Dashboard</RouterLink>
          </li>
          <li class="nav-item mb-2">
            <RouterLink to="/projects" class="nav-link text-white">My Projects</RouterLink>
          </li>
        </ul>
        
        <div class="mt-auto p-2 bg-secondary rounded text-white" style="font-size: 0.7rem;">
          <div>DID Status:</div>
          <div class="text-truncate">did:key:z6MkhaX...</div>
        </div>
      </nav>

      <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 bg-light min-vh-100">
        <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
          <h1 class="h2">Project Monitor</h1>
          <button class="btn btn-outline-primary btn-sm">Connect Wallet</button>
        </div>

        <RouterView />
      </main>
    </div>
  </div>
</template>

<style>
.nav-link:hover { background-color: #343a40; border-radius: 5px; }
.router-link-active { font-weight: bold; color: #0d6efd !important; }
</style>