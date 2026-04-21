<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2 class="fw-bold">GPT-2 Sentiment Analysis Lab</h2>
        <span class="badge bg-primary">Project ID: #1</span>
        <span class="badge bg-success ms-2">Current: Round 3</span>
      </div>
      <router-link to="/submit/1" class="btn btn-primary px-4">Submit Update</router-link>
    </div>

    <div class="row">
      <div class="col-md-8">
        <div class="card shadow-sm mb-4">
          <div class="card-body">
            <h5 class="card-title fw-bold">Project Description</h5>
            <p class="text-muted">Riset kolaboratif untuk fine-tuning GPT-2 pada dataset lokal Indonesia menggunakan metode Federated Learning.</p>
            <hr>
            <h6 class="fw-bold">Current Global Model (CID)</h6>
            <code class="d-block p-2 bg-light border rounded text-dark text-truncate">
              QmbS5TR9yid1t3XjreXV1g63TwLFBh7hNPjGf1TwXHx3Fv
            </code>
          </div>
        </div>

        <div class="card shadow-sm">
          <div class="card-header bg-white fw-bold">Current Round Contributions</div>
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th>Participant (DID)</th>
                  <th>Status</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="text-truncate" style="max-width: 200px;">did:key:z6MkhaX...</td>
                  <td><span class="badge bg-success">Submitted</span></td>
                  <td class="small text-muted">2 hours ago</td>
                </tr>
                <tr>
                  <td class="text-truncate">did:key:z6MkfT7...</td>
                  <td><span class="badge bg-warning text-dark">Pending</span></td>
                  <td>-</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="card border-primary mb-3">
          <div class="card-body text-center">
            <h6 class="text-muted">Aggregation Progress</h6>
            <h2 class="fw-bold">3 / 5</h2>
            <p class="small mb-0">Nodes submitted</p>
          </div>
        </div>
        <div class="card bg-dark text-white">
          <div class="card-body">
            <h6>Round Timer</h6>
            <h4 class="text-warning">08:22:10</h4>
            <small class="text-secondary">Until timeout / auto-aggregate</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>