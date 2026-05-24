<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useWeb3Store } from '../store/web3'

const web3Store = useWeb3Store()
const activeTab = ref('initiated')
const participatingProjects = ref([])
const isLoadingParticipating = ref(false)

// Filter proyek yang di-inisiasi oleh user yang sedang login
const initiatedProjects = computed(() => {
  if (!web3Store.address) return []
  return web3Store.projects.filter(
    p => p.initiator.toLowerCase() === web3Store.address.toLowerCase()
  )
})

// Fetch proyek yang diikuti user (bukan sebagai initiator)
const fetchParticipatingProjects = async () => {
  if (!web3Store.contract || !web3Store.address) return
  isLoadingParticipating.value = true
  try {
    const joined = []
    for (const project of web3Store.projects) {
      // Lewati proyek yang user sendiri buat (sudah ada di tab "initiated")
      if (project.initiator.toLowerCase() === web3Store.address.toLowerCase()) continue
      
      const isJoined = await web3Store.contract.isRegistered(project.id, web3Store.address)
      if (isJoined) {
        joined.push(project)
      }
    }
    participatingProjects.value = joined
  } catch (error) {
    console.error("Gagal mengambil proyek yang diikuti:", error)
  } finally {
    isLoadingParticipating.value = false
  }
}

const loadAllData = async () => {
  await web3Store.fetchProjects()
  await fetchParticipatingProjects()
}

onMounted(() => {
  if (web3Store.contract) {
    loadAllData()
  }
})

// Re-fetch jika contract baru siap (misal setelah refresh page)
watch(() => web3Store.contract, (newVal) => {
  if (newVal) loadAllData()
})
</script>

<template>
  <div class="container py-5">
    <div class="d-flex justify-content-between align-items-end mb-4">
      <div>
        <h2 class="fw-bold mb-1">My Dashboard</h2>
        <p class="text-muted mb-0">Manage projects you initiated or joined.</p>
      </div>
      <button @click="loadAllData" class="btn btn-sm btn-outline-primary" :disabled="web3Store.isLoading">
        <i class="bi bi-arrow-clockwise me-1"></i> Refresh
      </button>
    </div>
    
    <ul class="nav nav-pills mb-4 bg-white p-2 rounded shadow-sm">
      <li class="nav-item">
        <button class="nav-link" :class="{active: activeTab === 'initiated'}" @click="activeTab = 'initiated'">
          <i class="bi bi-rocket-takeoff me-1"></i>
          Projects I Initiated
          <span v-if="initiatedProjects.length" class="badge bg-white text-primary ms-2">{{ initiatedProjects.length }}</span>
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{active: activeTab === 'participating'}" @click="activeTab = 'participating'">
          <i class="bi bi-people me-1"></i>
          Projects I Join
          <span v-if="participatingProjects.length" class="badge bg-white text-primary ms-2">{{ participatingProjects.length }}</span>
        </button>
      </li>
    </ul>

    <!-- Loading State -->
    <div v-if="web3Store.isLoading || isLoadingParticipating" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="text-muted mt-3">Loading data from blockchain...</p>
    </div>

    <!-- ======================== TAB: INITIATED ======================== -->
    <div v-else-if="activeTab === 'initiated'">
      <!-- Empty State -->
      <div v-if="initiatedProjects.length === 0" class="card shadow-sm border-0 p-4 text-center">
        <div class="py-5">
          <i class="bi bi-folder2-open display-1 text-secondary d-block mb-3"></i>
          <p class="text-muted mb-3">You haven't initiated any projects yet.</p>
          <RouterLink to="/create" class="btn btn-primary">
            <i class="bi bi-plus-lg me-2"></i>Create New Project
          </RouterLink>
        </div>
      </div>

      <!-- Project List -->
      <div v-else class="row g-3">
        <div class="col-12" v-for="project in initiatedProjects" :key="project.id">
          <div class="card shadow-sm border-0 p-3">
            <div class="d-flex justify-content-between align-items-center">
              <div class="flex-grow-1">
                <div class="d-flex align-items-center gap-2 mb-1">
                  <h6 class="mb-0 fw-bold">{{ project.name }}</h6>
                  <span class="badge" :class="project.isActive ? 'bg-success' : 'bg-secondary'">
                    {{ project.isActive ? 'Active' : 'Finalized' }}
                  </span>
                </div>
                <div class="d-flex gap-3 mt-1">
                  <small class="text-muted">
                    <i class="bi bi-hash"></i> ID: {{ project.id }}
                  </small>
                  <small class="text-muted">
                    <i class="bi bi-cpu me-1"></i>{{ project.modelName }}
                  </small>
                  <small class="text-muted">
                    <i class="bi bi-arrow-repeat me-1"></i>Round {{ project.currentRound }}
                  </small>
                </div>
              </div>
              <router-link :to="'/project/' + project.id" class="btn btn-outline-primary btn-sm">
                <i class="bi bi-gear me-1"></i>Manage
              </router-link>
            </div>
          </div>
        </div>

        <!-- Tombol Create di bawah list -->
        <div class="col-12 text-center mt-3">
          <RouterLink to="/create" class="btn btn-outline-primary btn-sm">
            <i class="bi bi-plus-lg me-1"></i>Create Another Project
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- ======================== TAB: PARTICIPATING ======================== -->
    <div v-else-if="activeTab === 'participating'">
      <!-- Empty State -->
      <div v-if="participatingProjects.length === 0" class="card shadow-sm border-0 p-4 text-center">
        <div class="py-5">
          <i class="bi bi-search display-1 text-secondary d-block mb-3"></i>
          <p class="text-muted mb-3">You haven't joined any projects yet.</p>
          <RouterLink to="/" class="btn btn-primary">
            <i class="bi bi-globe me-2"></i>Explore Global Projects
          </RouterLink>
        </div>
      </div>

      <!-- Project List -->
      <div v-else class="row g-3">
        <div class="col-12" v-for="project in participatingProjects" :key="project.id">
          <div class="card shadow-sm border-0 p-3">
            <div class="d-flex justify-content-between align-items-center">
              <div class="flex-grow-1">
                <div class="d-flex align-items-center gap-2 mb-1">
                  <h6 class="mb-0 fw-bold">{{ project.name }}</h6>
                  <span class="badge" :class="project.isActive ? 'bg-success' : 'bg-secondary'">
                    {{ project.isActive ? 'Active' : 'Finalized' }}
                  </span>
                </div>
                <div class="d-flex gap-3 mt-1">
                  <small class="text-muted">
                    <i class="bi bi-hash"></i> ID: {{ project.id }}
                  </small>
                  <small class="text-muted">
                    <i class="bi bi-cpu me-1"></i>{{ project.modelName }}
                  </small>
                  <small class="text-muted">
                    <i class="bi bi-arrow-repeat me-1"></i>Round {{ project.currentRound }}
                  </small>
                  <small class="text-muted">
                    <i class="bi bi-person me-1"></i>By {{ project.initiator.substring(0, 6) }}...{{ project.initiator.substring(38) }}
                  </small>
                </div>
              </div>
              <router-link :to="'/project/' + project.id" class="btn btn-outline-primary btn-sm">
                <i class="bi bi-box-arrow-in-right me-1"></i>Open
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>