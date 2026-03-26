// =============================
// DEBUG
// =============================
console.log("🚀 Landing Demo JS loaded...");

// =============================
// MODULE
// =============================
window.PixaDemo = (() => {
  const SELECTORS = {
    form: "#generateForm",
    promptInputs: ".prompt-input",
    modelTags: "#model-tags .tag",
    modelActive: "#model-tags .tag.active",
    loraActive: "#lora-tags .tag.active",
    resultSlots: ".result-img",
    resultCards: ".result-card",
  };

  // =============================
  // DATA COLLECTION
  // =============================
  function collectFormData() {
    const prompts = Array.from(
      document.querySelectorAll(SELECTORS.promptInputs),
    )
      .map((el) => el.value.trim())
      .filter(Boolean);

    const activeModel = document.querySelector(SELECTORS.modelActive)?.dataset
      .model;
    const activeLora = document.querySelector(SELECTORS.loraActive)?.dataset
      .lora;

    if (!prompts.length) {
      alert("Enter a prompt");
      return null;
    }

    const normalize = (s) => s.toLowerCase().replace(/\s+/g, "-");

    let payload = {
      prompts: [],
      base_models: [],
      loras: [],
    };

    // =============================
    // CASE 1 → PROMPT VARIATION
    // =============================
    if (prompts.length > 1) {
      payload.prompts = prompts;
      payload.base_models = [normalize(activeModel)];
      payload.loras = [activeLora];

      console.log("🧠 Mode: Prompt variation", payload);
      return payload;
    }

    // =============================
    // DEFAULT → SINGLE GENERATION
    // =============================
    payload.prompts = [prompts[0]];
    payload.base_models = [normalize(activeModel)];
    payload.loras = [activeLora];

    console.log("🧠 Mode: Single", payload);

    return payload;
  }

  // =============================
  // UI RESET
  // =============================
function resetResults() {
  document.querySelectorAll(SELECTORS.resultSlots).forEach((el) => {
    el.innerHTML = `<div class="placeholder-text">Your result</div>`;
  });

  const cards = document.querySelectorAll(SELECTORS.resultCards);

  cards.forEach((c) => {
    c.classList.remove("selected", "focused", "dimmed");
  });

  // ✅ Set first as default
  if (cards.length > 0) {
    cards[0].classList.add("selected");
    setFocus(0); // keep dots + focus in sync
  }
}
  // =============================
  // LOADING STATE
  // =============================
  function renderLoadingState(count) {
    const slots = document.querySelectorAll(SELECTORS.resultSlots);

    slots.forEach((el, index) => {
      if (index < count) {
        el.innerHTML = `
        <div class="spinner-box">
          <div class="spinner-border text-primary"></div>
        </div>
      `;
      } else {
        el.innerHTML = `<div class="placeholder-text">Your result</div>`;
      }
    });
  }
  // =============================
  // RENDER ERROR STATE
  // =============================
  function renderErrorState(message = "Something went wrong") {
    document.querySelectorAll(SELECTORS.resultSlots).forEach((el) => {
      el.innerHTML = `
      <div class="error-box text-danger text-center">
        <div>⚠️</div>
        <div style="font-size: 14px;">${message}</div>
      </div>
    `;
    });
  }

  // =============================
  // MODEL → SLOT MAP (DYNAMIC)
  // =============================
  function getModelSlotMap() {
    const tags = document.querySelectorAll(SELECTORS.modelTags);
    const map = {};

    tags.forEach((tag, index) => {
      if (index < 3) {
        // ✅ match UI slots
        map[tag.dataset.model.toLowerCase().replace(/\s+/g, "-")] = index;
      }
    });

    return map;
  }

  // =============================
  // RENDER IMAGE (MODEL BASED)
  // =============================
  function renderImage(base_model, imageUrl) {
    const map = getModelSlotMap();
    const index = map[base_model];

    if (index === undefined) {
      console.warn("⚠️ Unknown model:", base_model);
      return;
    }

    const slot = document.querySelector(`.result-img[data-index="${index}"]`);
    if (!slot) return;

    slot.innerHTML = `<img src="${imageUrl}" />`;
  }

  // =============================
  // RENDER IMAGE (INDEX BASED)
  // =============================
  function renderImageByIndex(index, imageUrl) {
    const slot = document.querySelector(`.result-img[data-index="${index}"]`);
    if (!slot) return;

    slot.innerHTML = `<img src="${imageUrl}" />`;
  }

  // =============================
  // Add Focus System (Image Results)
  // =============================
  function setFocus(index) {
    const cards = document.querySelectorAll(SELECTORS.resultCards);
    const dots = document.querySelectorAll(".dot");

    cards.forEach((card, i) => {
      if (i === index) {
        card.classList.add("focused");
        card.classList.remove("dimmed");
      } else {
        card.classList.remove("focused");
        card.classList.add("dimmed");
      }
    });

    dots.forEach((dot, i) => {
      dot.classList.toggle("active", i === index);
    });
  }
  // =============================
  // GENERATE BUTTON STATE
  // =============================
 function setGenerateButtonState(disabled) {
  const btn = document.querySelector("#generateForm button[type='submit']");
  if (!btn) return;

  btn.disabled = disabled;

  if (disabled) {
    btn.classList.add("disabled");

    // store original text once
    if (!btn.dataset.originalText) {
      btn.dataset.originalText = btn.innerText;
    }

    // 🔥 Add spinner + text
    btn.innerHTML = `
      <span class="spinner-border spinner-border-sm me-2"></span>
      Generating...
    `;
  } else {
    btn.classList.remove("disabled");
    btn.innerHTML = btn.dataset.originalText || "Generate Variations →";
  }
}
  // =============================
  // TAG SELECTION
  // =============================
  function setupTags(groupId) {
    const group = document.getElementById(groupId);
    if (!group) return;

    group.querySelectorAll(".tag").forEach((tag) => {
      tag.addEventListener("click", () => {
        group
          .querySelectorAll(".tag")
          .forEach((t) => t.classList.remove("active"));

        tag.classList.add("active");
      });
    });
  }

  function setupPromptStack() {
    const container = document.getElementById("prompt-container");
    const addBtn = document.getElementById("add-prompt");
    const counter = document.getElementById("prompt-count");

    if (!container || !addBtn) return;

    let count = container.querySelectorAll(".prompt-block").length || 1;
    const max = 3;

    if (counter) counter.innerText = count;

    addBtn.addEventListener("click", () => {
      if (count >= max) return;

      const block = document.createElement("div");
      block.className = "prompt-block mt-3";

      block.innerHTML = `
            <textarea 
                class="demo-input prompt-input" 
                rows="3"
                placeholder="Try another variation..."
            ></textarea>
            <button type="button" class="remove-prompt-btn">✕</button>

        `;

      container.appendChild(block);
      const removeBtn = block.querySelector(".remove-prompt-btn");

      removeBtn.addEventListener("click", () => {
        block.remove();
        count--;

        if (counter) counter.innerText = count;

        // Re-enable add button if it was disabled
        if (count < max) {
          addBtn.disabled = false;
          addBtn.innerText = "Add variation";
          addBtn.style.opacity = "1";
        }
      });
      count++;

      if (counter) counter.innerText = count;

      if (count === max) {
        addBtn.disabled = true;
        addBtn.innerText = "Max 3 variations";
        addBtn.style.opacity = "0.5";
      }
    });
  }

  // =============================
  // GENERATE (STREAMING)
  // =============================
async function generateImages(payload) {
  let receivedAnyImage = false;
  let currentIndex = 0;

  try {
    const response = await fetch("/stream-generate-image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    // ❌ BAD RESPONSE (must re-enable button)
    if (!response.ok) {
      renderErrorState("Server error. Try again.");
      setGenerateButtonState(false); // 🔥 FIX
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let parts = buffer.split("\n\n");
      buffer = parts.pop();

      for (let part of parts) {
        if (part.startsWith("data: ")) {
          try {
            const data = JSON.parse(part.slice(6));

            console.log("🖼️ Stream:", data);

            // ✅ Render image
            renderImageByIndex(currentIndex, data.image);
            currentIndex++;

            // ✅ Mark success
            receivedAnyImage = true;

          } catch (err) {
            console.error("Parse error:", err);
          }
        }
      }
    }

    // ❌ No images received
    if (!receivedAnyImage) {
      renderErrorState("No images generated.");
    }

    console.log("✅ Stream complete");

  } catch (err) {
    console.error("❌ Streaming error:", err);
    renderErrorState("Generation failed. Please retry.");
  }

  // ✅ ALWAYS re-enable (single exit point)
  setGenerateButtonState(false);
}

  // =============================
  // INIT
  // =============================
  function init() {
    document.addEventListener("DOMContentLoaded", () => {
      console.log("✅ DOM ready - initializing demo");

      // Setup interactions
      setupTags("model-tags");
      setupTags("lora-tags");
      setupPromptStack();
      // Card selection
      document.querySelectorAll(SELECTORS.resultCards).forEach((card) => {
        card.addEventListener("click", () => {
          document
            .querySelectorAll(SELECTORS.resultCards)
            .forEach((c) => c.classList.remove("selected"));

          card.classList.add("selected");

          const index = Number(card.dataset.index);
          setFocus(index); // 🔥 sync focus + dots
        });
      });

      const form = document.querySelector(SELECTORS.form);
      if (!form) return;

      form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const data = collectFormData();
        if (!data) return;

        resetResults();
        const count = data.prompts.length;
        renderLoadingState(count);
        setGenerateButtonState(true);
        await generateImages(data);
        setGenerateButtonState(false);
      });
      document.querySelectorAll(".dot").forEach((dot) => {
        dot.addEventListener("click", () => {
          const index = Number(dot.dataset.index);
          setFocus(index);
        });
      });
    });
  }

  return { init };
})();

// =============================
PixaDemo.init();
