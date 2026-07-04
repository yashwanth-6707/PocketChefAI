/**
 * =============================================================
 * PocketChef AI — AI Thinking Overlay
 * Animated multi-step status animation during recipe search
 * =============================================================
 */

"use strict";

(function () {
  const STEPS = [
    { id: "parse",    icon: "�", label: "Understanding ingredients", duration: 700 },
    { id: "search",   icon: "🔎", label: "Searching recipe database", duration: 1200 },
    { id: "rank",     icon: "⚡", label: "Consulting IBM Granite AI", duration: 1100 },
    { id: "generate", icon: "🍳", label: "Preparing your recipe", duration: 1400 },
    { id: "polish",   icon: "✨", label: "Polishing the final result", duration: 500 },
  ];

  const STATUS_MESSAGES = [
    "Understanding ingredients...",
    "Searching recipe database...",
    "Consulting IBM Granite AI...",
    "Preparing your recipe...",
    "Almost ready for you...",
  ];

  let overlay = null;
  let progressInterval = null;
  let currentStepIdx = 0;
  let msgInterval = null;
  let progressValue = 0;

  // ---- Build DOM ----
  function buildOverlay() {
    const el = document.createElement("div");
    el.className = "ai-thinking-overlay";
    el.id = "aiThinkingOverlay";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-label", "AI is thinking");

    const stepsHTML = STEPS.map(s => `
      <span class="ai-thinking-step" id="ai-step-${s.id}">
        <span>${s.icon}</span> ${s.label}
      </span>
    `).join("");

    el.innerHTML = `
      <div class="ai-thinking-card">
        <div class="ai-thinking-visual" aria-hidden="true">
          <div class="chef-hat"></div>
          <div class="ai-thinking-icon">👨‍🍳</div>
          <div class="spoon-spin">🥄</div>
        </div>
        <div class="ai-thinking-title">Pocket Chef Intelligence</div>
        <div class="ai-thinking-status" id="aiThinkingStatus">
          <span class="ai-dots">
            <span></span><span></span><span></span>
          </span>
          &nbsp; Starting...
        </div>
        <div class="ai-thinking-steps" id="aiThinkingSteps">
          ${stepsHTML}
        </div>
        <div class="ai-progress-bar-wrap">
          <div class="ai-progress-bar-fill" id="aiProgressFill"></div>
        </div>
      </div>
    `;
    return el;
  }

  // ---- Show ----
  window.showAIThinkingOverlay = function () {
    if (overlay) return;
    overlay = buildOverlay();
    document.body.appendChild(overlay);
    currentStepIdx = 0;
    progressValue = 0;

    // Trigger fade in after one frame
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        overlay.classList.add("visible");
      });
    });

    // Status message cycling
    let msgIdx = 0;
    const statusEl = document.getElementById("aiThinkingStatus");
    if (statusEl) {
      statusEl.innerHTML = `
        <span class="ai-dots">
          <span></span><span></span><span></span>
        </span>
        &nbsp; ${STATUS_MESSAGES[0]}
      `;
    }
    msgInterval = setInterval(() => {
      msgIdx = (msgIdx + 1) % STATUS_MESSAGES.length;
      if (statusEl) {
        statusEl.style.opacity = "0";
        setTimeout(() => {
          statusEl.innerHTML = `
            <span class="ai-dots">
              <span></span><span></span><span></span>
            </span>
            &nbsp; ${STATUS_MESSAGES[msgIdx]}
          `;
          statusEl.style.opacity = "1";
        }, 200);
      }
    }, 1200);

    // Step progression
    runSteps();
  };

  function runSteps() {
    if (currentStepIdx >= STEPS.length) return;
    const step = STEPS[currentStepIdx];
    markStep(step.id, "active");
    progressValue = Math.round(((currentStepIdx + 0.5) / STEPS.length) * 100);
    updateProgress(progressValue);

    setTimeout(() => {
      markStep(step.id, "done");
      progressValue = Math.round(((currentStepIdx + 1) / STEPS.length) * 100);
      updateProgress(progressValue);
      currentStepIdx++;
      if (currentStepIdx < STEPS.length) {
        setTimeout(runSteps, 120);
      }
    }, step.duration);
  }

  function markStep(id, state) {
    const el = document.getElementById(`ai-step-${id}`);
    if (!el) return;
    el.classList.remove("active", "done");
    el.classList.add(state);
  }

  function updateProgress(pct) {
    const fill = document.getElementById("aiProgressFill");
    if (fill) fill.style.width = pct + "%";
  }

  // ---- Hide ----
  window.hideAIThinkingOverlay = function () {
    if (!overlay) return;
    clearInterval(msgInterval);
    clearInterval(progressInterval);

    // Complete progress bar
    updateProgress(100);

    overlay.classList.remove("visible");
    const el = overlay;
    setTimeout(() => {
      if (el && el.parentNode) el.parentNode.removeChild(el);
      if (overlay === el) overlay = null;
    }, 350);
  };

})();
