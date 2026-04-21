<template>
  <div class="row mt-4">
    <div class="col-md-4">
      <div class="card shadow-sm border-start border-primary border-4">
        <div class="card-body">
          <h6 class="text-muted">Round Status</h6>
          <h3>Round 2</h3>
        </div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="card shadow-sm border-start border-success border-4">
        <div class="card-body">
          <h6 class="text-muted">Participating Nodes</h6>
          <h3>5 Nodes</h3>
        </div>
      </div>
    </div>
  </div>

  <div class="row mt-4">
    <div class="col-12">
      <div class="card shadow-sm">
        <div class="card-header bg-white font-weight-bold">Training Progress (GPT-2)</div>
        <div class="card-body">
          <div class="progress mb-3" style="height: 25px;">
            <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 75%">75%</div>
          </div>
          <div class="bg-dark text-success p-3 rounded shadow-inner" style="font-family: monospace; font-size: 0.8rem;">
            > [INFO] Loading local_model.safetensors... <br>
            > [INFO] Epoch 1/5: Loss 0.4523 <br>
            > [INFO] Epoch 2/5: Loss 0.3112 <br>
            > [WAIT] Awaiting Blockchain Confirmation...
          </div>
        </div>
      </div>
    </div>
  </div>
</template>