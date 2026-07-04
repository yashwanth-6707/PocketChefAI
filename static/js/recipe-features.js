/**
 * =============================================================
 * PocketChef AI — Premium Recipe Features
 * Voice synthesis, cooking timer, shopping list,
 * nutrition circles, ripple effects, autocomplete
 * =============================================================
 */

"use strict";

/* ======================== VOICE SYNTHESIS ======================== */
(function initVoice() {
  let speechInstance = null;
  let isSpeaking = false;

  window.readRecipe = function (btn) {
    if (!("speechSynthesis" in window)) {
      showToast("Not Supported", "Your browser does not support text-to-speech.", "error");
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      isSpeaking = false;
      if (btn) {
        btn.classList.remove("speaking");
        btn.innerHTML = `<i class="bi bi-volume-up me-1"></i>Read Recipe`;
      }
      return;
    }

    // Collect recipe text
    const titleEl = document.querySelector(".recipe-detail-title");
    const ingredients = document.querySelectorAll(".ingredient-item span:last-child");
    const steps = document.querySelectorAll(".timeline-step-text, .step-content");

    let text = "";
    if (titleEl) text += `Recipe: ${titleEl.textContent.trim()}. `;
    if (ingredients.length) {
      text += "Ingredients: ";
      ingredients.forEach(el => { text += el.textContent.trim() + ", "; });
      text += ". ";
    }
    if (steps.length) {
      text += "Instructions. ";
      steps.forEach((el, i) => { text += `Step ${i + 1}: ${el.textContent.trim()} ` ; });
    }

    if (!text.trim()) {
      showToast("Nothing to Read", "No recipe content found.", "error");
      return;
    }

    speechInstance = new SpeechSynthesisUtterance(text);
    speechInstance.rate = 0.95;
    speechInstance.pitch = 1;
    speechInstance.lang = "en-US";

    speechInstance.onend = () => {
      isSpeaking = false;
      if (btn) {
        btn.classList.remove("speaking");
        btn.innerHTML = `<i class="bi bi-volume-up me-1"></i>Read Recipe`;
      }
    };

    window.speechSynthesis.speak(speechInstance);
    isSpeaking = true;

    if (btn) {
      btn.classList.add("speaking");
      btn.innerHTML = `<i class="bi bi-stop-fill me-1"></i>Stop Reading`;
    }
  };
})();


/* ======================== COOKING TIMER ======================== */
(function initCookingTimer() {
  let timerInterval = null;
  let timerSeconds = 0;
  let timerRunning = false;
  let totalSeconds = 0;

  function getOrCreateWidget() {
    let w = document.getElementById("cookingTimerWidget");
    if (!w) {
      w = document.createElement("div");
      w.className = "timer-widget";
      w.id = "cookingTimerWidget";
      w.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
          <span style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--text-muted)">
            <i class="bi bi-alarm"></i> Timer
          </span>
          <button class="timer-btn danger" onclick="PocketTimer.close()" title="Close">
            <i class="bi bi-x"></i>
          </button>
        </div>
        <div class="timer-ring-wrap">
          <svg class="timer-ring" width="64" height="64" viewBox="0 0 64 64">
            <circle class="timer-ring-bg"   cx="32" cy="32" r="28"/>
            <circle class="timer-ring-fill" cx="32" cy="32" r="28"
              id="timerRingFill"
              stroke-dasharray="175.93"
              stroke-dashoffset="0"/>
          </svg>
        </div>
        <div class="timer-display" id="timerDisplay">00:00</div>
        <div class="timer-label"   id="timerLabel">Ready</div>
        <div class="timer-controls">
          <button class="timer-btn" onclick="PocketTimer.toggle()" id="timerPlayBtn" title="Start/Pause">
            <i class="bi bi-play-fill"></i>
          </button>
          <button class="timer-btn" onclick="PocketTimer.reset()" title="Reset">
            <i class="bi bi-arrow-counterclockwise"></i>
          </button>
        </div>
      `;
      document.body.appendChild(w);
    }
    return w;
  }

  function formatTime(secs) {
    const m = Math.floor(secs / 60).toString().padStart(2, "0");
    const s = (secs % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  }

  function updateRing(remaining, total) {
    const fill = document.getElementById("timerRingFill");
    if (!fill) return;
    const circumference = 175.93;
    const pct = total > 0 ? remaining / total : 1;
    fill.style.strokeDashoffset = circumference * (1 - pct);
  }

  function tick() {
    if (timerSeconds <= 0) {
      clearInterval(timerInterval);
      timerRunning = false;
      document.getElementById("timerDisplay").textContent = "00:00";
      document.getElementById("timerLabel").textContent = "Done! 🎉";
      document.getElementById("timerPlayBtn").innerHTML = `<i class="bi bi-play-fill"></i>`;
      updateRing(0, totalSeconds);
      if (typeof showToast !== "undefined") {
        showToast("⏱ Timer Done!", "Your step timer has finished!", "success");
      }
      return;
    }
    timerSeconds--;
    updateDisplay();
    updateRing(timerSeconds, totalSeconds);
  }

  function updateDisplay() {
    const el = document.getElementById("timerDisplay");
    if (el) el.textContent = formatTime(timerSeconds);
  }

  window.PocketTimer = {
    open: function (minutes, label) {
      const w = getOrCreateWidget();
      timerSeconds = (minutes || 5) * 60;
      totalSeconds = timerSeconds;
      updateDisplay();
      updateRing(timerSeconds, totalSeconds);
      const lbl = document.getElementById("timerLabel");
      if (lbl) lbl.textContent = label || `${minutes} min timer`;
      w.classList.add("visible");
      this.start();
    },
    start: function () {
      if (timerRunning) return;
      timerRunning = true;
      timerInterval = setInterval(tick, 1000);
      const btn = document.getElementById("timerPlayBtn");
      if (btn) btn.innerHTML = `<i class="bi bi-pause-fill"></i>`;
    },
    pause: function () {
      clearInterval(timerInterval);
      timerRunning = false;
      const btn = document.getElementById("timerPlayBtn");
      if (btn) btn.innerHTML = `<i class="bi bi-play-fill"></i>`;
    },
    toggle: function () {
      if (timerRunning) this.pause(); else this.start();
    },
    reset: function () {
      clearInterval(timerInterval);
      timerRunning = false;
      timerSeconds = totalSeconds;
      updateDisplay();
      updateRing(totalSeconds, totalSeconds);
      const btn = document.getElementById("timerPlayBtn");
      if (btn) btn.innerHTML = `<i class="bi bi-play-fill"></i>`;
      const lbl = document.getElementById("timerLabel");
      if (lbl) lbl.textContent = "Ready";
    },
    close: function () {
      clearInterval(timerInterval);
      timerRunning = false;
      const w = document.getElementById("cookingTimerWidget");
      if (w) w.classList.remove("visible");
    }
  };
})();


/* ======================== SHOPPING LIST ======================== */
window.buildShoppingList = function (missingIngredients, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const panel = document.getElementById("shoppingListPanel") ||
                container.closest("[data-shopping-panel]");

  if (!missingIngredients || missingIngredients.length === 0) {
    panel?.classList.add("d-none");
    return;
  }
  if (panel) panel.classList.remove("d-none");

  container.innerHTML = missingIngredients.map((ing, i) => `
    <div class="shopping-item" id="shop-item-${i}">
      <div class="shopping-checkbox" id="shop-check-${i}"
           onclick="PocketShopping.toggle(${i})"
           role="checkbox" tabindex="0"
           aria-label="Mark ${ing} as bought">
      </div>
      <span class="shopping-item-name">${capitalize2(ing)}</span>
      <span style="font-size:.72rem;color:var(--text-xmuted);margin-left:auto">needed</span>
    </div>
  `).join("");
};

window.PocketShopping = {
  toggle: function (idx) {
    const item = document.getElementById(`shop-item-${idx}`);
    const check = document.getElementById(`shop-check-${idx}`);
    if (!item || !check) return;
    const isChecked = check.classList.contains("checked");
    check.classList.toggle("checked", !isChecked);
    check.innerHTML = !isChecked ? `<i class="bi bi-check-lg" style="font-size:.7rem"></i>` : "";
    item.classList.toggle("checked", !isChecked);
  }
};


/* ======================== NUTRITION CIRCLES ======================== */
window.renderNutritionCircles = function (data, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const items = [
    { label: "Calories", value: data.calories || 0, max: 500,  color: "#0EA5E9", unit: "" },
    { label: "Protein",  value: data.protein  || 0, max: 60,   color: "#22C55E", unit: "g" },
    { label: "Fat",      value: data.fat      || 0, max: 70,   color: "#FFD93D", unit: "g" },
    { label: "Carbs",    value: data.carbs    || 0, max: 300,  color: "#A855F7", unit: "g" },
  ];

  const r = 28;
  const circ = 2 * Math.PI * r;

  container.innerHTML = items.map((item, i) => {
    const pct = Math.min(item.value / item.max, 1);
    const offset = circ * (1 - pct);
    return `
      <div class="nut-card">
        <div class="nut-circle">
          <svg class="nut-circle-svg" width="70" height="70" viewBox="0 0 70 70">
            <circle class="nut-circle-bg" cx="35" cy="35" r="${r}"/>
            <circle class="nut-circle-fill"
              cx="35" cy="35" r="${r}"
              stroke="${item.color}"
              stroke-dasharray="${circ}"
              stroke-dashoffset="${circ}"
              data-target-offset="${offset}"
              id="nut-fill-${i}"
              style="transition-delay:${i * 150}ms"/>
          </svg>
          <div class="nut-circle-val">${item.value}${item.unit}</div>
        </div>
        <div class="nut-card-label">${item.label}</div>
      </div>
    `;
  }).join("");

  // Animate after paint
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      items.forEach((_, i) => {
        const circle = document.getElementById(`nut-fill-${i}`);
        if (circle) {
          const targetOffset = parseFloat(circle.dataset.targetOffset);
          circle.style.strokeDashoffset = targetOffset;
        }
      });
    });
  });
};


/* ======================== BUTTON RIPPLE ======================== */
(function initRipples() {
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn-ai-search, .ai-search-submit-btn, .btn-cta-primary");
    if (!btn) return;
    const rect = btn.getBoundingClientRect();
    const ripple = document.createElement("span");
    ripple.className = "ripple";
    ripple.style.left = (e.clientX - rect.left) + "px";
    ripple.style.top  = (e.clientY - rect.top) + "px";
    btn.appendChild(ripple);
    ripple.addEventListener("animationend", () => ripple.remove());
  });
})();


/* ======================== AUTOCOMPLETE ======================== */
const COMMON_INGREDIENTS = [
  "rice", "egg", "eggs", "tomato", "tomatoes", "onion", "onions", "garlic",
  "chicken", "potato", "potatoes", "butter", "milk", "cheese", "flour",
  "carrot", "carrots", "spinach", "ginger", "cumin", "turmeric", "oil",
  "salt", "pepper", "lemon", "lime", "coriander", "chili", "broccoli",
  "pasta", "beef", "pork", "fish", "shrimp", "mushroom", "mushrooms",
  "celery", "bell pepper", "corn", "peas", "beans", "lentils",
  "soy sauce", "vinegar", "sugar", "honey", "yogurt", "cream",
  "parsley", "basil", "oregano", "thyme", "rosemary"
];

(function initAutocomplete() {
  // Slight delay to let DOM settle
  setTimeout(() => {
    const input = document.getElementById("ingredientInput");
    if (!input) return;

    let dropdown = document.getElementById("aiAutocomplete");
    if (!dropdown) {
      dropdown = document.createElement("div");
      dropdown.className = "ai-autocomplete";
      dropdown.id = "aiAutocomplete";
      const wrapper = input.closest(".ai-search-wrapper") || input.parentElement;
      if (wrapper) {
        wrapper.style.position = "relative";
        wrapper.appendChild(dropdown);
      }
    }

    input.addEventListener("input", () => {
      const val = input.value.trim().toLowerCase();
      if (val.length < 1) { dropdown.classList.remove("open"); return; }

      const matches = COMMON_INGREDIENTS.filter(i =>
        i.startsWith(val) && i !== val
      ).slice(0, 5);

      if (!matches.length) { dropdown.classList.remove("open"); return; }

      dropdown.innerHTML = matches.map(m => `
        <div class="ai-autocomplete-item" data-val="${m}">
          <i class="bi bi-basket2" style="font-size:.7rem;opacity:.5"></i>
          ${m.charAt(0).toUpperCase() + m.slice(1)}
        </div>
      `).join("");

      dropdown.querySelectorAll(".ai-autocomplete-item").forEach(item => {
        item.addEventListener("mousedown", (e) => {
          e.preventDefault();
          const v = item.dataset.val;
          if (typeof addIngredient === "function") {
            addIngredient(v);
            input.value = "";
          }
          dropdown.classList.remove("open");
        });
      });

      dropdown.classList.add("open");
    });

    input.addEventListener("blur", () => {
      setTimeout(() => dropdown.classList.remove("open"), 150);
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Escape") dropdown.classList.remove("open");
    });
  }, 300);
})();


/* ======================== UTILITY ======================== */
function capitalize2(str) {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
}
