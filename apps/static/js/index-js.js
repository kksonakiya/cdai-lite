console.log("index-js loaded...");

/* ========================= */
/* IMAGE SELECTION */
/* ========================= */

function toggleSelect(el) {
  el.classList.toggle("selected");
}

function markWinner() {
  const all = document.querySelectorAll(".card-img-select");

  all.forEach((el) => el.classList.remove("winner"));

  const selected = document.querySelector(".card-img-select.selected");

  if (selected) {
    selected.classList.add("winner");
  } else {
    console.warn("No image selected");
  }
}

/* ========================= */
/* THEME SYSTEM */
/* ========================= */

function setTheme(type) {
  if (type === "indigo") {
    setVars("#6366f1", "#ec4899", "#e0e7ff", "#fce7f3");
  }

  if (type === "green") {
    setVars("#10b981", "#3b82f6", "#d1fae5", "#e0f2fe");
  }

  if (type === "warm") {
    setVars("#f59e0b", "#ef4444", "#fef3c7", "#fee2e2");
  }

  if (type === "minimal") {
    setVars("#111", "#555", "#e5e7eb", "#f3f4f6");
  }
}

function setVars(c1, c2, s1, s2) {
  document.documentElement.style.setProperty(
    "--grad-main",
    `linear-gradient(135deg,${c1},${c2})`,
  );
  document.documentElement.style.setProperty(
    "--grad-soft",
    `linear-gradient(135deg,${s1},${s2})`,
  );
}

/* ========================= */
/* PROMPT SYSTEM */
/* ========================= */

function getLabel(index) {
  return "Prompt " + String.fromCharCode(65 + index);
}

function refreshLabels() {
  const items = document.querySelectorAll("#prompt-container .prompt-item");

  items.forEach((item, i) => {
    let label = item.querySelector(".small");

    if (!label) {
      label = document.createElement("div");
      label.className = "small text-muted mb-1";
      item.prepend(label);
    }

    label.innerText = getLabel(i);
  });
}

function addPrompt() {
  const container = document.getElementById("prompt-container");

  if (!container) return;

  const div = document.createElement("div");
  div.className = "prompt-item mb-3";

  div.innerHTML = `
    <div class="small text-muted mb-1"></div>
    <textarea class="form-control" rows="2" placeholder="Enter prompt..."></textarea>
    <button class="remove-btn" onclick="removePrompt(this)">✕</button>
  `;

  container.appendChild(div);

  refreshLabels();
}

function removePrompt(el) {
  const parent = el.parentElement;
  if (parent) parent.remove();

  refreshLabels();
}

/* ========================= */
/* TAG SYSTEM (MODELS + LORA) */
/* ========================= */

function toggleTag(el) {
  el.classList.toggle("active");

  // debug log (optional)
  const selected = document.querySelectorAll(".tag.active").length;
  console.log("Selected tags:", selected);
}

/* ========================= */
/* INIT */
/* ========================= */

document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM ready");

  refreshLabels();

  // Safety: ensure at least 1 prompt exists
  const container = document.getElementById("prompt-container");
  if (container && container.children.length === 0) {
    addPrompt();
  }
});

function runBatchSimulation() {
  const status = document.getElementById("batch-status");
  const cards = document.querySelectorAll(".card-img-select");
  const boxes = document.querySelectorAll(".image-box");
  const compareBtn = document.getElementById("compare-btn");
  const selectBtn = document.getElementById("select-btn");

  if (!status || cards.length === 0) return;

  /* ===== RESET STATE ===== */
  compareBtn.disabled = true;
  selectBtn.disabled = true;

  status.innerText = "Preparing generation...";

  // clear selections + winners
  cards.forEach((card) => {
    card.classList.remove("selected", "winner");
  });

  /* ===== LOADING PHASE ===== */
  boxes.forEach((box) => {
    box.classList.add("loading");
    box.style.background = "#e5e7eb";
    box.style.transform = "scale(0.98)";
    setTimeout(() => {
      box.style.transform = "scale(1)";
    }, 150);
  });

  /* ===== START GENERATION ===== */
  setTimeout(() => {
    status.innerText = "Generating outputs...";
  }, 300);

  /* ===== PROGRESSIVE LOAD ===== */
  boxes.forEach((box, index) => {
    const delay = 800 + index * 450;

    setTimeout(() => {
      box.classList.remove("loading");

      // simulate slightly different outputs
      const gradients = [
        "linear-gradient(135deg,#c7d2fe,#fbcfe8)",
        "linear-gradient(135deg,#d1fae5,#bfdbfe)",
        "linear-gradient(135deg,#fef3c7,#fecaca)",
        "linear-gradient(135deg,#e9d5ff,#fbcfe8)",
      ];

      box.style.background = gradients[index % gradients.length];

      /* LAST ITEM DONE */
      if (index === boxes.length - 1) {
        status.innerText = "Generation complete";

        compareBtn.disabled = false;
        selectBtn.disabled = false;
      }
    }, delay);
  });
}
