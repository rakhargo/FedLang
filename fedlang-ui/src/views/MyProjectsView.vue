<script setup>
import { ref } from 'vue'
const activeTab = ref('initiated')
</script>

<template>
  <div class="container py-5">
    <h2 class="fw-bold mb-4">My Dashboard</h2>
    
    <ul class="nav nav-pills mb-4 bg-white p-2 rounded shadow-sm">
      <li class="nav-item">
        <button class="nav-link" :class="{active: activeTab === 'initiated'}" @click="activeTab = 'initiated'">
          Projects I Initiated
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{active: activeTab === 'participating'}" @click="activeTab = 'participating'">
          Projects I Join
        </button>
      </li>
    </ul>

    <div v-if="activeTab === 'initiated'" class="card shadow-sm border-0 p-4 text-center">
      <div class="py-5">
        <p class="text-muted">You haven't started any projects yet.</p>
        <!-- <button class="btn btn-primary">+ Create New Project</button> -->
        <RouterLink to="/create" class="btn btn-primary">
          <i class="bi bi-plus-lg me-2"></i> Create New Project
        </RouterLink>
      </div>
    </div>
    
    <div v-else class="row g-3">
      <div class="col-12 card shadow-sm p-3 border-0">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <h6 class="mb-0 fw-bold">Medical Image Classification (X-Ray)</h6>
            <small class="text-muted">Next submission: 2 days left</small>
          </div>
          <router-link to="/project/2" class="btn btn-outline-secondary btn-sm">Manage</router-link>
        </div>
      </div>
    </div>
  </div>
</template>