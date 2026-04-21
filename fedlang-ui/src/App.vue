<template>
  <div class="container-fluid p-0 overflow-hidden">
    <div class="row g-0">
      <nav class="col-md-3 col-lg-2 bg-dark text-white vh-100 p-3 position-sticky top-0 shadow">
        <h4 class="text-primary fw-bold mb-4 px-2">FedLang.</h4>
        
        <ul class="nav flex-column gap-2">
          <li class="nav-item">
            <RouterLink to="/" class="nav-link text-white rounded px-3">
              <i class="bi bi-globe me-2"></i> Explore Projects
            </RouterLink>
          </li>
          <hr class="border-secondary">
          <li class="nav-item">
            <RouterLink to="/my-projects" class="nav-link text-white rounded px-3">
              <i class="bi bi-kanban me-2"></i> Initiated by Me
            </RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink to="/joined-projects" class="nav-link text-white rounded px-3">
              <i class="bi bi-people me-2"></i> Joined Projects
            </RouterLink>
          </li>
        </ul>

        <div class="mt-auto p-3 bg-secondary bg-opacity-25 rounded border border-secondary">
          <small class="text-info fw-bold d-block mb-1">YOUR DID</small>
          <code class="text-light d-block text-truncate mb-2" style="font-size: 0.7rem;">
            did:key:z6MkhaX...
          </code>
          <span class="badge bg-success w-100">Identity Verified</span>
        </div>
      </nav>

      <main class="col-md-9 ms-sm-auto col-lg-10 bg-light min-vh-100">
        <header class="bg-white border-bottom p-3 d-flex justify-content-between align-items-center sticky-top">
          <span class="text-muted fw-medium">Network: <b class="text-dark">Anvil Local</b></span>
          <button class="btn btn-primary rounded-pill px-4 shadow-sm">
            <i class="bi bi-wallet2 me-2"></i> Connect Wallet
          </button>
        </header>

        <div class="p-4">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>