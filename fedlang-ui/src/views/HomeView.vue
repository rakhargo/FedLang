<template>
  <div class="container py-5">
    <div class="row mb-4">
      <div class="col-md-6">
        <h2 class="fw-bold">Global Projects</h2>
        <p class="text-muted">Explore collaborative AI training across the globe.</p>
      </div>
    </div>

    <div class="row g-4">
      <div v-for="i in 3" :key="i" class="col-md-4">
        <div class="card h-100 shadow-sm hover-shadow transition">
          <div class="card-body">
            <div class="d-flex justify-content-between mb-2">
              <span class="badge bg-soft-primary text-primary">NLP</span>
              <span class="text-muted small">Round 3/10</span>
            </div>
            <h5 class="card-title fw-bold">GPT-2 Indonesia Sentiment</h5>
            <p class="card-text text-muted small">Fine-tuning GPT-2 untuk deteksi emosi pada teks Bahasa Indonesia.</p>
            <div class="mt-4 pt-3 border-top">
              <div class="d-flex justify-content-between align-items-center">
                <span class="small fw-bold">5 Participants</span>
                <router-link to="/project/1" class="btn btn-sm btn-primary">Join & View</router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>