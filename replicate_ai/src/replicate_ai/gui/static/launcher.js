/** Launcher: pick pack, upload files/folder, start run. */

const MB = 1024 * 1024;
const WARN_MB = 100;
const CONFIRM_MB = 1000;

let selectedPack = null;
let uploadedPackPath = null;
let paperFile = null;
let dataFile = null;
let dirFiles = null;
let activeTab = "packs";

const noticeEl = document.getElementById("notice");
const packGrid = document.getElementById("pack-grid");
const providerSelect = document.getElementById("provider");
const btnStart = document.getElementById("btn-start");

function showNotice(msg, isError = false) {
  noticeEl.textContent = msg;
  noticeEl.className = isError ? "notice error" : "notice";
  noticeEl.style.display = "block";
}

function hideNotice() {
  noticeEl.style.display = "none";
}

function totalBytes(files) {
  return files.reduce((n, f) => n + (f.size || 0), 0);
}

function checkSizeWarning(bytes) {
  const mb = bytes / MB;
  if (mb >= CONFIRM_MB) {
    return confirm(
      `Very large upload (${mb.toFixed(0)} MB). This may take a while. Continue?`
    );
  }
  if (mb >= WARN_MB) {
    showNotice(`Large upload (${mb.toFixed(0)} MB) — this may take a while.`);
  } else {
    hideNotice();
  }
  return true;
}

function updateStartButton() {
  const ready =
    (activeTab === "packs" && selectedPack) ||
    (activeTab === "files" && uploadedPackPath) ||
    (activeTab === "directory" && uploadedPackPath);
  btnStart.disabled = !ready;
}

async function loadConfig() {
  const [cfg, ex] = await Promise.all([
    fetch("/api/config").then((r) => r.json()),
    fetch("/api/examples").then((r) => r.json()),
  ]);

  providerSelect.innerHTML = "";
  for (const p of cfg.providers || []) {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.label;
    if (p.id === cfg.default_provider) opt.selected = true;
    providerSelect.appendChild(opt);
  }

  packGrid.innerHTML = "";
  for (const pack of ex.examples || []) {
    const card = document.createElement("div");
    card.className = "pack-card";
    card.dataset.path = pack.path;
    const badges = [
      pack.has_pdf ? '<span class="badge ok">PDF</span>' : '<span class="badge miss">no PDF</span>',
      pack.has_csv ? '<span class="badge ok">CSV</span>' : '<span class="badge miss">no CSV</span>',
    ].join("");
    card.innerHTML = `<h3>${pack.label}</h3><div class="meta">${pack.citation || pack.id}</div><div style="margin-top:0.5rem">${badges}</div>`;
    card.addEventListener("click", () => {
      document.querySelectorAll(".pack-card").forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      selectedPack = pack.path;
      uploadedPackPath = null;
      updateStartButton();
    });
    packGrid.appendChild(card);
  }

  if (cfg.initial_run_id) {
    window.location.href = `/run.html?id=${cfg.initial_run_id}`;
  }
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    activeTab = tab.dataset.tab;
    document.getElementById("panel-packs").style.display = activeTab === "packs" ? "" : "none";
    document.getElementById("panel-files").style.display = activeTab === "files" ? "" : "none";
    document.getElementById("panel-directory").style.display = activeTab === "directory" ? "" : "none";
    updateStartButton();
  });
});

async function uploadFilesMode() {
  const form = new FormData();
  form.append("paper", paperFile);
  form.append("data", dataFile);
  const r = await fetch("/api/upload?mode=files", { method: "POST", body: form });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || "Upload failed");
  if (data.warnings?.length) showNotice(data.warnings.join(" · "));
  return data.pack_path;
}

async function uploadDirectoryMode(files) {
  const form = new FormData();
  for (const f of files) {
    const rel = f.webkitRelativePath || f.name;
    form.append("files", f, rel);
  }
  const r = await fetch("/api/upload?mode=directory", { method: "POST", body: form });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || "Upload failed");
  if (data.warnings?.length) showNotice(data.warnings.join(" · "));
  return data.pack_path;
}

// File dropzone
const dzFiles = document.getElementById("dropzone-files");
dzFiles.addEventListener("click", () => {
  document.getElementById("input-paper").click();
});
document.getElementById("input-paper").addEventListener("change", (e) => {
  paperFile = e.target.files[0];
  document.getElementById("input-data").click();
});
document.getElementById("input-data").addEventListener("change", async (e) => {
  dataFile = e.target.files[0];
  const sel = document.getElementById("files-selected");
  if (paperFile && dataFile) {
    sel.textContent = `${paperFile.name} · ${dataFile.name}`;
    const bytes = paperFile.size + dataFile.size;
    if (!checkSizeWarning(bytes)) return;
    try {
      uploadedPackPath = await uploadFilesMode();
      selectedPack = null;
      updateStartButton();
    } catch (err) {
      showNotice(err.message, true);
    }
  }
});

// Directory dropzone
const dzDir = document.getElementById("dropzone-dir");
const inputDir = document.getElementById("input-directory");
dzDir.addEventListener("click", () => inputDir.click());
inputDir.addEventListener("change", async (e) => {
  const files = Array.from(e.target.files || []);
  if (!files.length) return;
  dirFiles = files;
  document.getElementById("dir-selected").textContent = `${files.length} file(s) from folder`;
  const bytes = totalBytes(files);
  if (!checkSizeWarning(bytes)) return;
  try {
    uploadedPackPath = await uploadDirectoryMode(files);
    selectedPack = null;
    updateStartButton();
  } catch (err) {
    showNotice(err.message, true);
  }
});

function setupDragDrop(el, onFiles) {
  el.addEventListener("dragover", (e) => {
    e.preventDefault();
    el.classList.add("dragover");
  });
  el.addEventListener("dragleave", () => el.classList.remove("dragover"));
  el.addEventListener("drop", async (e) => {
    e.preventDefault();
    el.classList.remove("dragover");
    await onFiles(e.dataTransfer.files);
  });
}

setupDragDrop(dzFiles, async (files) => {
  const list = Array.from(files);
  paperFile = list.find((f) => f.name.toLowerCase().endsWith(".pdf"));
  dataFile = list.find((f) => f.name.toLowerCase().endsWith(".csv"));
  if (!paperFile || !dataFile) {
    showNotice("Drop both a PDF and a CSV file.", true);
    return;
  }
  document.getElementById("files-selected").textContent = `${paperFile.name} · ${dataFile.name}`;
  if (!checkSizeWarning(paperFile.size + dataFile.size)) return;
  try {
    uploadedPackPath = await uploadFilesMode();
    updateStartButton();
  } catch (err) {
    showNotice(err.message, true);
  }
});

setupDragDrop(dzDir, async (files) => {
  const list = Array.from(files);
  if (!list.length) return;
  if (!checkSizeWarning(totalBytes(list))) return;
  try {
    uploadedPackPath = await uploadDirectoryMode(list);
    document.getElementById("dir-selected").textContent = `${list.length} file(s)`;
    updateStartButton();
  } catch (err) {
    showNotice(err.message, true);
  }
});

btnStart.addEventListener("click", async () => {
  const example_dir =
    activeTab === "packs" ? selectedPack : uploadedPackPath;
  if (!example_dir) return;
  btnStart.disabled = true;
  btnStart.textContent = "Starting…";
  try {
    const r = await fetch("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        example_dir,
        provider: providerSelect.value,
      }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "Failed to start run");
    window.location.href = `/run.html?id=${data.run_id}`;
  } catch (err) {
    showNotice(err.message, true);
    btnStart.disabled = false;
    btnStart.textContent = "Start replication";
  }
});

loadConfig().catch((err) => showNotice(err.message, true));
