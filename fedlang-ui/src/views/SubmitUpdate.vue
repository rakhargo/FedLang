<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card shadow border-0">
          <div class="card-body p-4">
            <h4 class="fw-bold mb-4 text-center">Submit Model Update</h4>
            
            <div class="mb-3">
              <label class="form-label small fw-bold">Model CID (IPFS)</label>
              <input type="text" class="form-control" placeholder="Qm..." required>
            </div>

            <div class="mb-3">
              <label class="form-label small fw-bold">Content Hash (Auto-generated)</label>
              <input type="text" class="form-control bg-light" value="0x8b32...f321" disabled>
            </div>

            <div class="alert alert-info py-2 small">
              <strong>Signature Notice:</strong> Dengan menekan tombol Sign, Anda menyetujui update model ini menggunakan DID Anda.
            </div>

            <div class="d-grid gap-2 mt-4">
              <button class="btn btn-dark">Step 1: Sign Transaction</button>
              <button class="btn btn-primary" disabled>Step 2: Submit to Blockchain</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>