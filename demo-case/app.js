const cpFileInput = document.getElementById("cpFile");
const sofFileInput = document.getElementById("sofFile");
const runBtn = document.getElementById("runBtn");
const statusBox = document.getElementById("statusBox");
const contractTerms = document.getElementById("contractTerms");
const timelineOutput = document.getElementById("timelineOutput");

function setStatus(message, type = "") {
  statusBox.textContent = message;
  statusBox.classList.remove("error-state", "success-state");

  if (type) {
    statusBox.classList.add(type);
  }
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderSelectedFiles(cpFile, sofFile) {
  contractTerms.innerHTML = `
    <div class="term-grid">
      <div class="term-item">
        <div class="term-label">Charter Party File</div>
        <div class="term-value">${escapeHtml(cpFile.name)}</div>
      </div>
      <div class="term-item">
        <div class="term-label">File Type</div>
        <div class="term-value">${escapeHtml(cpFile.type || "Unknown")}</div>
      </div>
      <div class="term-item">
        <div class="term-label">Upload Status</div>
        <div class="term-value">Ready for live contract extraction</div>
      </div>
      <div class="term-item">
        <div class="term-label">Current Step</div>
        <div class="term-value">Waiting for backend response</div>
      </div>
    </div>
  `;

  timelineOutput.innerHTML = `
    <div class="timeline-list">
      <div class="timeline-item">
        <div class="timeline-step">Statement of Facts File</div>
        <div class="timeline-time">${escapeHtml(sofFile.name)}</div>
      </div>
      <div class="timeline-item">
        <div class="timeline-step">Demo Mode</div>
        <div class="timeline-time">This file will map to the prepared voyage timeline for v1</div>
      </div>
      <div class="timeline-item">
        <div class="timeline-step">Current Step</div>
        <div class="timeline-time">Waiting for extraction and timeline assembly</div>
      </div>
    </div>
  `;
}

runBtn.addEventListener("click", async () => {
  const cpFile = cpFileInput.files[0];
  const sofFile = sofFileInput.files[0];

  if (!cpFile || !sofFile) {
    setStatus("Please upload both a Charter Party and a Statement of Facts file before running extraction.", "error-state");
    return;
  }

  setStatus("Files received. Frontend is ready. Next we will connect this button to the live extraction backend.", "success-state");
  renderSelectedFiles(cpFile, sofFile);
});