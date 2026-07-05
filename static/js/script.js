/**
 * =============================================================
 * Recipe Preparation Agent — Main JavaScript
 * Handles: ingredient chips, search, results rendering,
 *          dark mode, favorites, toasts, and animations
 * =============================================================
 */

"use strict";

// ======================== STATE ========================
const state = {
  ingredients: [],
  currentRecipes: [],
  sortMode: "match",
  darkMode: false
};
console.log("PocketChef AI script loaded");

// ======================== DOM READY ========================
document.addEventListener("DOMContentLoaded", () => {
  initDarkMode();
  initIngredientInput();
  initSearchForm();
  initQuickChips();
  initPasteModal();
  initNavbarScroll();
  initTooltips();
  initCountUpStats();
  initCookModeBar();
  initResponseActions();
  initShoppingListActions();

  // Animate elements on scroll
  observeAnimations();
  initSectionReveal();
  initRippleButtons();
});

// ======================== DARK MODE ========================
function initDarkMode() {
  const toggle = document.getElementById("darkModeToggle");
  const icon = document.getElementById("darkModeIcon");
  const html = document.documentElement;

  // Load saved preference
  const saved = localStorage.getItem("theme");
  if (saved === "dark" || (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    setDark(true);
  }

  if (toggle) {
    toggle.addEventListener("click", () => {
      setDark(html.getAttribute("data-theme") !== "dark");
    });
  }

  function setDark(isDark) {
    html.setAttribute("data-theme", isDark ? "dark" : "light");
    localStorage.setItem("theme", isDark ? "dark" : "light");
    state.darkMode = isDark;
    if (icon) {
      icon.className = isDark ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
    }
  }
}

// ======================== NAVBAR SCROLL ========================
function initNavbarScroll() {
  const navbar = document.getElementById("mainNavbar");
  if (!navbar) return;
  window.addEventListener("scroll", () => {
    if (window.scrollY > 60) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
  }, { passive: true });
}

// ======================== INGREDIENT CHIPS ========================
function initIngredientInput() {
  const input = document.getElementById("ingredientInput");
  const addBtn = document.getElementById("addIngredientBtn");
  if (!input) return;

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addIngredientFromInput();
    }
    if (e.key === "Backspace" && input.value === "" && state.ingredients.length > 0) {
      removeIngredient(state.ingredients[state.ingredients.length - 1]);
    }
  });

  if (addBtn) {
    addBtn.addEventListener("click", addIngredientFromInput);
  }
}

function addIngredientFromInput() {
  const input = document.getElementById("ingredientInput");
  if (!input) return;
  const value = input.value.trim().toLowerCase();
  if (value) {
    addIngredient(value);
    input.value = "";
    input.focus();
  }
}

// ======================== INGREDIENT COUNT BADGE ========================
function updateIngCountBadge() {
  const badge = document.getElementById("ingCountBadge");
  if (!badge) return;
  const count = state.ingredients.length;
  badge.textContent = count;
  badge.classList.toggle("has-items", count > 0);
  badge.style.display = count > 0 ? "inline-flex" : "none";
}

function addIngredient(name) {
  name = name.replace(/[^a-zA-Z0-9\s\-]/g, "").trim().toLowerCase();
  if (!name || name.length < 2 || name.length > 50) return;
  if (state.ingredients.includes(name)) {
    showToast("Already Added", `"${name}" is already in your list.`);
    return;
  }
  if (state.ingredients.length >= 20) {
    showToast("Limit Reached", "Maximum 20 ingredients allowed.");
    return;
  }
  state.ingredients.push(name);
  renderChips();
  updateIngCountBadge();
}

function removeIngredient(name) {
  state.ingredients = state.ingredients.filter(i => i !== name);
  renderChips();
  updateIngCountBadge();
}

function renderChips() {
  const container = document.getElementById("chipContainer");
  if (!container) return;
  container.innerHTML = "";
  state.ingredients.forEach(ing => {
    const chip = document.createElement("div");
    chip.className = "ingredient-chip";
    chip.innerHTML = `
      <i class="bi bi-basket2-fill" style="font-size:0.75rem"></i>
      ${capitalize(ing)}
      <span class="remove-chip" onclick="removeIngredient('${ing}')">&times;</span>
    `;
    container.appendChild(chip);
  });
}

// ======================== QUICK CHIPS ========================
function initQuickChips() {
  document.querySelectorAll(".quick-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const ing = chip.dataset.ing;
      if (ing) addIngredient(ing);
    });
  });
}

// ======================== PASTE MODAL ========================
function initPasteModal() {
  const pasteBtn = document.getElementById("pasteIngredientsBtn");
  const parsePasteBtn = document.getElementById("parsePasteBtn");
  const textarea = document.getElementById("pasteTextarea");

  if (pasteBtn) {
    pasteBtn.addEventListener("click", () => {
      const modal = new bootstrap.Modal(document.getElementById("pasteModal"));
      modal.show();
    });
  }

  if (parsePasteBtn) {
    parsePasteBtn.addEventListener("click", async () => {
      const text = textarea.value.trim();
      if (!text) return;

      try {
        const res = await fetch("/api/parse-ingredients", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text })
        });
        const data = await res.json();
        if (data.success && data.data.ingredients) {
          data.data.ingredients.forEach(ing => addIngredient(ing));
          bootstrap.Modal.getInstance(document.getElementById("pasteModal")).hide();
          textarea.value = "";
          showToast("Ingredients Added", `Added ${data.data.ingredients.length} ingredients.`);
        }
      } catch (err) {
        // Fallback: parse locally
        const items = text.split(/[,\n;]+/).map(s => s.trim()).filter(s => s.length >= 2);
        items.forEach(ing => addIngredient(ing));
        bootstrap.Modal.getInstance(document.getElementById("pasteModal")).hide();
        textarea.value = "";
      }
    });
  }
}

// ======================== SEARCH FORM ========================
function initSearchForm() {
  const form = document.getElementById("recipeSearchForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    await performSearch();
  });

  // Sort buttons
  const sortMatch = document.getElementById("sortByMatch");
  const sortTime = document.getElementById("sortByTime");
  if (sortMatch) sortMatch.addEventListener("click", () => { state.sortMode = "match"; renderResults(state.currentRecipes); });
  if (sortTime) sortTime.addEventListener("click", () => { state.sortMode = "time"; renderResults(state.currentRecipes); });

  // Copy AI response
  const copyBtn = document.getElementById("copyAiResponse");
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      const text = document.getElementById("aiInstructionsText")?.innerText;
      if (text) {
        navigator.clipboard.writeText(text).then(() => showToast("Copied!", "AI response copied to clipboard."));
      }
    });
  }
}

async function performSearch() {
  if (state.ingredients.length === 0) {
    showToast("No Ingredients", "Please add at least one ingredient first.", "warning");
    document.getElementById("ingredientInput")?.focus();
    // Shake the search button to draw attention
    const btn = document.getElementById("searchBtn");
    if (btn) {
      btn.classList.add("btn-shake");
      btn.addEventListener("animationend", () => btn.classList.remove("btn-shake"), { once: true });
    }
    return;
  }

  const cuisine = document.getElementById("cuisineSelect")?.value || "any";
  const diet = document.getElementById("dietSelect")?.value || "any";
  const difficulty = document.getElementById("difficultySelect")?.value || "any";
  const leftoverMode = document.getElementById("leftoverMode")?.checked || false;

  // Show premium AI thinking state
  setSearchLoading(true);
  if (typeof window.showAIThinkingOverlay === "function") {
    window.showAIThinkingOverlay();
  } else {
    showLoadingOverlay("🤖 IBM Granite is cooking up your recipe...");
  }
  showSkeletonCards();
  showAITypingIndicator();

  try {
    const endpoint = leftoverMode ? "/api/leftovers" : "/search";
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ingredients: state.ingredients,
        cuisine, diet, difficulty
      })
    });

    const json = await res.json();

    if (!res.ok || !json.success) {
      showToast("Error", json.error || "Search failed. Please try again.", "error");
      hideSkeletonCards();
      return;
    }

    const data = json.data;
    state.currentRecipes = data.recipes || (leftoverMode ? data.recipes : []);

    // Render results
    hideSkeletonCards();
    renderAIInstructions(data.ai_instructions || data.ai_suggestions || "");
    renderResults(state.currentRecipes);
    renderHealthyTips(data.healthy_tips || []);
    renderSubstitutions(data.substitutions || {});

    // Show results section
    document.getElementById("resultsSection")?.classList.remove("d-none");
    document.getElementById("noResultsSection")?.classList.add("d-none");

    if (state.currentRecipes.length === 0 && !data.ai_instructions) {
      document.getElementById("resultsSection")?.classList.add("d-none");
      document.getElementById("noResultsSection")?.classList.remove("d-none");
    }

    // Scroll to results
    setTimeout(() => {
      document.getElementById("resultsSection")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 200);

    showToast("Found!", `${state.currentRecipes.length} recipe(s) found for your ingredients.`, "success");

  } catch (err) {
    console.error("Search error:", err);
    showToast("Network Error", "Could not connect to the server. Please try again.", "error");
    hideSkeletonCards();
  } finally {
    setSearchLoading(false);
    if (typeof window.hideAIThinkingOverlay === "function") {
      window.hideAIThinkingOverlay();
    } else {
      hideLoadingOverlay();
    }
  }
}

function setSearchLoading(isLoading) {
  const btn = document.getElementById("searchBtn");
  const spinner = document.getElementById("searchSpinner");
  const text = btn?.querySelector(".btn-text");
  if (!btn) return;
  btn.disabled = isLoading;
  spinner?.classList.toggle("d-none", !isLoading);
  if (text) text.textContent = isLoading ? "Searching..." : "Find Recipes with AI";
  btn.classList.toggle("opacity-75", isLoading);
}

// ======================== SKELETON CARDS ========================
function showSkeletonCards() {
  const grid = document.getElementById("recipeCardsGrid");
  const section = document.getElementById("resultsSection");
  if (!grid || !section) return;
  section.classList.remove("d-none");
  document.getElementById("aiInstructionsPanel")?.classList.add("d-none");
  grid.innerHTML = [1, 2, 3].map(() => `
    <div class="col-xl-4 col-md-6">
      <div class="recipe-card-skeleton">
        <div class="skeleton-image"></div>
        <div class="skeleton-body">
          <div class="skeleton-line h-20 w-80 mb-3"></div>
          <div class="skeleton-line w-60"></div>
          <div class="skeleton-line w-40"></div>
          <div class="skeleton-line w-80 mt-3" style="height:48px;border-radius:8px"></div>
        </div>
      </div>
    </div>
  `).join("");
}

function hideSkeletonCards() {
  const grid = document.getElementById("recipeCardsGrid");
  if (!grid) return;
  // Only clear if still showing skeletons
  if (grid.querySelector(".recipe-card-skeleton")) {
    grid.innerHTML = "";
  }
}

// ======================== AI TYPING INDICATOR ========================
function showAITypingIndicator() {
  const textEl = document.getElementById("aiInstructionsText");
  const panel = document.getElementById("aiInstructionsPanel");
  if (!textEl || !panel) return;
  textEl.innerHTML = `
    <div class="ai-typing-dots">
      <span></span><span></span><span></span>
    </div>
    <small class="text-muted ms-2" style="font-size:0.8rem">IBM Granite is thinking…</small>
  `;
  panel.classList.remove("d-none");
}

// ======================== RENDER FUNCTIONS ========================

function renderAIInstructions(text) {
  const panel = document.getElementById("aiInstructionsPanel");
  const textEl = document.getElementById("aiInstructionsText");
  if (!textEl) return;

  if (text && text.trim()) {
    textEl.innerHTML = buildAISectionCards(text);

    // Wire up collapsible toggles
    textEl.querySelectorAll(".ai-section-toggle").forEach(btn => {
      btn.addEventListener("click", () => {
        const card = btn.closest(".ai-section-card");
        const body = card.querySelector(".ai-section-body");
        const isOpen = card.classList.contains("open");
        card.classList.toggle("open", !isOpen);
        body.classList.toggle("open", !isOpen);
      });
    });

    // If buildAISectionCards produced zero .ai-section-card elements (pure fallback),
    // still show the panel — content is already rendered as plain HTML
    panel?.classList.remove("d-none");
  } else {
    panel?.classList.add("d-none");
  }
}

/* Build premium collapsible section cards from raw AI text.
 *
 * The Granite prompt uses this EXACT header format:
 *   🍽️ BEST RECIPE: ...
 *   📊 MATCH: ...
 *   📋 INGREDIENTS NEEDED:
 *   👨‍🍳 STEP-BY-STEP INSTRUCTIONS:
 *   💡 COOKING TIPS:
 *   🔄 INGREDIENT SUBSTITUTIONS:
 *   🥗 NUTRITION (per serving):
 *   🍽️ SERVING SUGGESTIONS:
 *   🫙 STORAGE TIPS:
 *   ♻️ LEFTOVER IDEAS:
 *
 * Detection strategy: strip emoji/symbols, then match keyword at start-of-line
 * or as the dominant content, with exact keyword anchoring. "YOU HAVE" and
 * "MISSING" are sub-content bullets, NOT section headers, so they are excluded.
 */
function buildAISectionCards(text) {
  /*
   * SECTION_MAP: each entry has a `patterns` array of regex objects.
   * Each regex is anchored to the START of the stripped line (after emoji removal).
   * This prevents "INGREDIENTS" inside "MATCH: 40% of ingredients available" from firing.
   *
   * Patterns are listed most-specific FIRST to avoid e.g. "INGREDIENT" matching before
   * "INGREDIENT SUBSTITUTIONS".
   *
   * The model sometimes outputs typos (e.g. "INGREDIENTS NEEED") so we use fuzzy prefixes
   * like /^INGREDIENT/ to catch all variants.
   */
  const SECTION_MAP = [
    { re: /^BEST RECIPE/,                icon: "🍽️", color: "rgba(14,165,233,0.12)",  title: "Best Recipe Match" },
    { re: /^STEP.BY.STEP|^STEP BY STEP|^INSTRUCTIONS?:/,
                                         icon: "📋", color: "rgba(14,165,233,0.12)",  title: "Step-by-Step Instructions" },
    { re: /^INGREDIENT.SUBSTITUT|^SUBSTITUT/,
                                         icon: "🔄", color: "rgba(168,85,247,0.12)", title: "Substitutions" },
    // Fuzzy: catches INGREDIENTS NEEDED, INGREDIENTS NEEED, INGREDIENTS:, INGREDIENT LIST etc.
    { re: /^INGREDIENTS?(\s|:)/,         icon: "🧺", color: "rgba(251,191,36,0.12)",  title: "Ingredients Needed" },
    { re: /^COOKING\s+TIPS?/,            icon: "💡", color: "rgba(251,191,36,0.12)",  title: "Cooking Tips" },
    { re: /^SERVING\s+SUGGESTION/,       icon: "🍴", color: "rgba(34,197,94,0.12)",  title: "Serving Suggestions" },
    { re: /^STORAGE\s+TIPS?/,            icon: "📦", color: "rgba(14,165,233,0.12)", title: "Storage Tips" },
    { re: /^LEFTOVER/,                   icon: "♻️", color: "rgba(34,211,238,0.12)", title: "Leftover Ideas" },
    { re: /^NUTRITION/,                  icon: "📊", color: "rgba(34,211,238,0.12)", title: "Nutrition Info" },
    // MATCH only when it IS the header (short line starting with MATCH:)
    { re: /^MATCH:/,                     icon: "🎯", color: "rgba(34,197,94,0.12)",  title: "Match Analysis" },
  ];

  /* Remove ALL leading emoji, punctuation, and symbols to expose the keyword.
   * Handles: plain emoji (🍽️), ZWJ sequences (👨‍🍳), variation selectors (️),
   *          legacy symbols (♻ U+267B), bullets, dashes, hashes. */
  function stripLeading(s) {
    let prev = "";
    let cur  = s;
    // Loop until stable — needed because emoji + variation selector + space may need 2-3 passes
    while (cur !== prev) {
      prev = cur;
      cur = cur
        .replace(/^[\s\-•*#=>`]+/, "")
        .replace(/^```+\s*/g, "")
        .replace(/^[\u2600-\u27BF][\uFE0F]?\s*/g, "")              // Misc symbols ♻ ♨ etc
        .replace(/^[\u{1F000}-\u{1FFFF}][\uFE0F\u20D0-\u20FF]?(?:\u200D[\u{1F000}-\u{1FFFF}][\uFE0F]?)*\s*/gu, "") // emoji + ZWJ
        .replace(/^[\uFE00-\uFE0F\u200D\u20D0-\u20FF\s]+/, "");    // leftover selectors
    }
    return cur.trim();
  }

  function isHeaderLine(line) {
    const trimmed = line.trim();
    if (!trimmed) return null;

    // Exclude sub-content bullets: ✅ You have... / ❌ Missing...
    if (/^[✅❌]/.test(trimmed)) return null;

    // Numbered list items that are clearly steps, not headers (long lines with content)
    if (/^\d+[\.\)]\s/.test(trimmed) && trimmed.length > 50) return null;

    // Section header lines are usually short, but allow longer headers from AI
    if (trimmed.length > 200) return null;

    const stripped = stripLeading(trimmed).trim();
    const normalized = stripped.replace(/[:\-]+$/, "").toUpperCase();
    if (!normalized) return null;

    // Ignore instruction headings so they do not become fake steps.
    if (/^(STEP[- ]BY[- ]STEP(?:\s+INSTRUCTIONS?)?|INSTRUCTIONS?)$/i.test(stripped)) {
      return {
        entry: {
          re: /^INSTRUCTIONS?:/,
          icon: "📋",
          color: "rgba(14,165,233,0.12)",
          title: "Step-by-Step Instructions"
        },
        remainder: ""
      };
    }

    for (const entry of SECTION_MAP) {
      const match = entry.re.exec(normalized);
      if (match) {
        const remainder = normalized.slice(match[0].length).trim();
        return { entry, remainder };
      }
    }
    return null;
  }

  const lines = text.split("\n");
  const sections = [];
  let currentSection = null;
  const preambleLines = [];

  for (const line of lines) {
    const matched = isHeaderLine(line);
    if (matched) {
      if (currentSection) sections.push(currentSection);
      currentSection = {
        meta: matched.entry,
        lines: matched.remainder ? [matched.remainder] : []
      };
    } else if (currentSection) {
      currentSection.lines.push(line);
    } else {
      preambleLines.push(line);
    }
  }
  if (currentSection) sections.push(currentSection);

  console.log("AI parsed sections:", sections.map(s => ({ title: s.meta.title, lines: s.lines })));

  // If no sections detected, fall back to plain formatted text
  if (!sections.length) {
    const rawHTML = lines.map(l => {
      let f = l.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\*(.*?)\*/g, "<em>$1</em>");
      return f.trim() ? `<p style="margin:.25rem 0">${f}</p>` : "";
    }).join("");
    return `<div class="ai-section-content p-2" style="font-size:.87rem;line-height:1.75">${rawHTML || escapeHtml(text)}</div>`;
  }

  // Render preamble (content before first section header) if any
  const preambleHTML = preambleLines.filter(l => l.trim()).map(l => {
    const f = l.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    return `<p style="margin:.2rem 0;font-size:.88rem;color:var(--text-secondary)">${f}</p>`;
  }).join("");

  const cardsHTML = sections
    .filter(sec => sec.meta.title !== "Substitutions")
    .map((sec, idx) => {
    const contentLines = sec.lines.join("\n").trim();
    const contentHTML = formatSectionContent(contentLines, sec.meta.title);
    // Open first card by default (class added here; JS will also handle it)
    const openClass = idx === 0 ? " open" : "";
    return `
      <div class="ai-section-card${openClass}">
        <button class="ai-section-toggle" type="button">
          <span class="ai-section-icon" style="background:${sec.meta.color}">${sec.meta.icon}</span>
          <span>${sec.meta.title}</span>
          <i class="bi bi-chevron-down ai-section-chevron"></i>
        </button>
        <div class="ai-section-body${openClass}">
          <div class="ai-section-content">${contentHTML || '<p style="margin:.25rem 0;color:var(--text-muted);font-size:.88rem">(No extra text provided)</p>'}</div>
        </div>
      </div>
    `;
  }).join("");

  return (preambleHTML ? `<div class="px-1 pb-1">${preambleHTML}</div>` : "") + cardsHTML;
}

function formatSectionContent(text, sectionTitle) {
  const lines = text.split("\n").filter(l => l.trim());
  const isSteps = sectionTitle.toLowerCase().includes("step") || sectionTitle.toLowerCase().includes("instruction");

  const visibleLines = lines.filter(line => {
    const cleaned = line.trim();
    if (!cleaned) return false;
    const normalized = cleaned
      .replace(/^[\s\-•*#=>`]+/, "")
      .replace(/^```+\s*/g, "")
      .replace(/^[\u2600-\u27BF][\uFE0F]?\s*/g, "")
      .replace(/^[\u{1F000}-\u{1FFFF}][\uFE0F\u20D0-\u20FF]?(?:\u200D[\u{1F000}-\u{1FFFF}][\uFE0F]?)*\s*/gu, "")
      .replace(/^[\uFE00-\uFE0F\u200D\u20D0-\u20FF\s]+/, "")
      .trim()
      .replace(/[:\-]+$/, "")
      .toLowerCase();
    return !["instructions", "step-by-step instructions", "step by step instructions", "step-by-step", "step by step"].includes(normalized);
  });

  if (isSteps) {
    let stepNum = 0;
    return visibleLines.map(line => {
      const cleaned = line.replace(/^\d+[\.\)]\s*/, "").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
      if (!cleaned.trim()) return "";
      stepNum++;
      return `
        <div class="section-step">
          <span class="step-num">${stepNum}</span>
          <span>${cleaned}</span>
        </div>`;
    }).join("");
  }

  return visibleLines.map(line => {
    let f = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\*(.*?)\*/g, "<em>$1</em>");
    if (!f.trim()) return "";
    // Numbered or bulleted
    if (/^[-•\*]\s/.test(f)) {
      f = f.replace(/^[-•\*]\s/, "");
      return `<div style="display:flex;gap:.5rem;padding:.2rem 0"><span style="color:var(--blue-500);margin-top:2px">▸</span><span>${f}</span></div>`;
    }
    if (/^\d+[\.\)]\s/.test(f)) {
      const num = f.match(/^(\d+)/)[1];
      f = f.replace(/^\d+[\.\)]\s/, "");
      return `<div style="display:flex;gap:.5rem;padding:.2rem 0"><span class="step-num" style="width:20px;height:20px;font-size:.65rem">${num}</span><span>${f}</span></div>`;
    }
    return `<p style="margin:.25rem 0">${f}</p>`;
  }).join("");
}

function formatAIText(text) {
  // Legacy fallback
  return buildAISectionCards(text);
}

function renderResults(recipes) {
  const grid = document.getElementById("recipeCardsGrid");
  const title = document.getElementById("resultsTitle");
  if (!grid) return;

  // Sort
  const sorted = [...recipes];
  if (state.sortMode === "time") {
    sorted.sort((a, b) => (a.total_time || 0) - (b.total_time || 0));
  } else {
    sorted.sort((a, b) => (b.match_percentage || 0) - (a.match_percentage || 0));
  }

  if (title) title.innerHTML = `<i class="bi bi-collection me-2"></i>Matching Recipes <span class="badge ms-2" style="background:var(--blue-500)">${recipes.length}</span>`;

  grid.innerHTML = sorted.map((recipe, i) => createRecipeCard(recipe, i)).join("");

  // Build shopping list for top result's missing ingredients
  if (sorted.length > 0 && typeof buildShoppingList === "function") {
    const missing = sorted[0].missing_ingredients || [];
    buildShoppingList(missing, "shoppingListItems");
  }
}

function createRecipeCard(recipe, index = 0) {
  const diffColor = recipe.difficulty_color || getDifficultyColor(recipe.difficulty);
  const emoji = recipe.emoji || getCuisineEmoji(recipe.cuisine);
  const totalTime = recipe.total_time || ((recipe.prep_time || 0) + (recipe.cook_time || 0));
  const matchPct = recipe.match_percentage || 0;
  const diets = (recipe.diet || []).slice(0, 2);
  const id = recipe.id || "";
  const delay = index * 80;

  // Pill color for difficulty
  const diffPill = diffColor === "success" ? "green" : diffColor === "warning" ? "amber" : diffColor === "danger" ? "red" : "";

  return `
    <div class="col-xl-4 col-md-6">
      <div class="recipe-card-v2 recipe-card-enter" style="animation-delay:${delay}ms" onclick="window.location.href='/recipe/${id}'">
        <div class="recipe-card-v2-image">
          <span>${emoji}</span>
          <span class="cuisine-badge-v2">${escapeHtml(recipe.cuisine || "")}</span>
          ${matchPct > 0 ? `<span class="match-pct-badge">${matchPct}%</span>` : ""}
          <button class="fav-btn-v2 recipe-fav-btn" onclick="event.stopPropagation(); toggleFavorite('${id}', this)" data-recipe-id="${id}">
            <i class="bi bi-heart"></i>
          </button>
        </div>
        <div class="recipe-card-v2-body">
          <div class="recipe-card-v2-name">${escapeHtml(recipe.name)}</div>
          <div class="recipe-meta-v2">
            <span class="meta-pill blue"><i class="bi bi-clock"></i> ${totalTime} min</span>
            <span class="meta-pill ${diffPill}"><i class="bi bi-bar-chart"></i> ${escapeHtml(recipe.difficulty || "Easy")}</span>
            <span class="meta-pill"><i class="bi bi-fire"></i> ${recipe.calories || 0} cal</span>
          </div>
          <div class="d-flex flex-wrap gap-1 mb-2">
            ${diets.map(d => `<span class="diet-tag">${escapeHtml(d)}</span>`).join("")}
          </div>
          ${recipe.matched_ingredients && recipe.matched_ingredients.length > 0 ? `
          <div class="mb-1">
            <small style="color:var(--accent-green);font-size:.72rem;font-weight:500">
              <i class="bi bi-check-circle-fill me-1"></i>Have: ${recipe.matched_ingredients.slice(0, 3).map(i => capitalize(i)).join(", ")}${recipe.matched_ingredients.length > 3 ? ` +${recipe.matched_ingredients.length - 3}` : ""}
            </small>
          </div>` : ""}
          ${recipe.missing_ingredients && recipe.missing_ingredients.length > 0 ? `
          <div class="mb-1">
            <small style="color:var(--soft-red);font-size:.72rem;font-weight:500">
              <i class="bi bi-cart3 me-1"></i>Need: ${recipe.missing_ingredients.slice(0, 2).map(i => capitalize(i)).join(", ")}${recipe.missing_ingredients.length > 2 ? ` +${recipe.missing_ingredients.length - 2}` : ""}
            </small>
          </div>` : ""}
          <div class="d-flex justify-content-between mt-2 pt-2" style="border-top:1px solid var(--border)">
            <span style="font-size:.72rem;text-align:center;color:var(--text-muted)"><strong style="color:var(--text-primary);display:block;font-size:.85rem">${recipe.protein || 0}g</strong>Protein</span>
            <span style="font-size:.72rem;text-align:center;color:var(--text-muted)"><strong style="color:var(--text-primary);display:block;font-size:.85rem">${recipe.fat || 0}g</strong>Fat</span>
            <span style="font-size:.72rem;text-align:center;color:var(--text-muted)"><strong style="color:var(--text-primary);display:block;font-size:.85rem">${recipe.carbohydrates || 0}g</strong>Carbs</span>
          </div>
        </div>
        <div class="recipe-card-v2-footer">
          <a href="/recipe/${id}" class="btn btn-primary btn-sm flex-fill" onclick="event.stopPropagation()">
            <i class="bi bi-book me-1"></i>View Recipe
          </a>
          <button class="btn btn-sm btn-outline-secondary" onclick="event.stopPropagation(); toggleFavorite('${id}', this.previousElementSibling?.previousElementSibling || this)" title="Save">
            <i class="bi bi-bookmark"></i>
          </button>
        </div>
      </div>
    </div>`;
}

// ======================== COUNT-UP HERO STATS ========================
function initCountUpStats() {
  const stats = document.querySelectorAll(".hero-stat-number[data-target]");
  if (!stats.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const target = parseInt(el.dataset.target, 10);
      if (isNaN(target)) return;
      animateCountUp(el, target);
      observer.unobserve(el);
    });
  }, { threshold: 0.5 });

  stats.forEach(el => observer.observe(el));
}

function animateCountUp(el, target) {
  const duration = 1400;
  const start = performance.now();
  const easeOut = (t) => 1 - Math.pow(1 - t, 3);

  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const value = Math.round(easeOut(progress) * target);
    el.textContent = value;
    if (progress < 1) requestAnimationFrame(tick);
    else el.textContent = target;
  }
  requestAnimationFrame(tick);
}

// ======================== COOK MODE PROGRESS BAR ========================
function initCookModeBar() {
  const bar = document.getElementById("cookModeBar");
  const fill = document.getElementById("cookModeFill");
  const label = document.getElementById("cookModeLabel");
  const steps = document.querySelectorAll(".instruction-step");
  if (!steps.length || !bar) return;

  bar.classList.add("visible");

  function updateProgress() {
    const completed = document.querySelectorAll(".instruction-step.completed").length;
    const total = steps.length;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
    if (fill) fill.style.width = pct + "%";
    if (label) {
      label.textContent = pct === 100 ? "🎉 Done!" : `${completed}/${total} steps`;
      label.classList.toggle("visible", completed > 0);
    }
    // If all steps done, show celebration toast
    if (pct === 100) {
      showToast("🎉 Recipe Complete!", "Amazing! You've finished all the cooking steps.", "success");
    }
  }

  // Intercept clicks on steps — runs after the click toggles "completed"
  steps.forEach(step => {
    step.addEventListener("click", () => {
      requestAnimationFrame(() => {
        // Ping animation when newly completed
        const badge = step.querySelector(".step-number-badge");
        if (badge && step.classList.contains("completed")) {
          badge.classList.remove("step-done-ping");
          void badge.offsetWidth; // force reflow
          badge.classList.add("step-done-ping");
          setTimeout(() => badge.classList.remove("step-done-ping"), 600);
        }
        updateProgress();
      });
    });
  });
}

function initResponseActions() {
  const copyBtn = document.getElementById("copyAiResponse");
  const saveBtn = document.getElementById("downloadAiResponse");
  const shareBtn = document.getElementById("shareAiResponse");

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      const text = document.getElementById("aiInstructionsText")?.innerText;
      if (text) {
        navigator.clipboard.writeText(text).then(() => showToast("Copied!", "AI response copied to clipboard."));
      }
    });
  }

  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      const text = document.getElementById("aiInstructionsText")?.innerText;
      if (!text) return;
      const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pocketchef-ai-response.txt";
      a.click();
      URL.revokeObjectURL(url);
      showToast("Saved", "AI response downloaded.");
    });
  }

  if (shareBtn) {
    shareBtn.addEventListener("click", async () => {
      const text = document.getElementById("aiInstructionsText")?.innerText;
      if (!text) return;
      if (navigator.share) {
        try { await navigator.share({ title: "PocketChef AI Recipe", text }); }
        catch (err) { /* ignore */ }
      } else {
        await navigator.clipboard.writeText(text);
        showToast("Shared", "Recipe details copied for sharing.");
      }
    });
  }
}

function initShoppingListActions() {
  const downloadBtn = document.getElementById("downloadShoppingListBtn");
  const printBtn = document.getElementById("printShoppingListBtn");

  if (downloadBtn) {
    downloadBtn.addEventListener("click", () => {
      const items = Array.from(document.querySelectorAll("#shoppingListItems .shopping-item-name"))
        .map(el => el.textContent.trim());
      if (!items.length) return;
      const blob = new Blob([items.join("\n")], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pocketchef-shopping-list.txt";
      a.click();
      URL.revokeObjectURL(url);
      showToast("Downloaded", "Shopping list saved.");
    });
  }

  if (printBtn) {
    printBtn.addEventListener("click", () => window.print());
  }
}

function renderHealthyTips(tips) {
  const panel = document.getElementById("healthyTipsPanel");
  const list = document.getElementById("healthyTipsList");
  if (!panel || !list || !tips.length) {
    panel?.classList.add("d-none");
    return;
  }
  list.innerHTML = tips.map(tip =>
    `<div class="d-flex align-items-start gap-2 mb-2">
      <i class="bi bi-leaf text-success mt-1"></i>
      <span class="small text-muted">${escapeHtml(tip)}</span>
    </div>`
  ).join("");
  panel.classList.remove("d-none");
}

function renderSubstitutions(subs) {
  const panel = document.getElementById("substitutionsPanel");
  const list = document.getElementById("substitutionsList");
  if (!panel || !list || Object.keys(subs).length === 0) {
    panel?.classList.add("d-none");
    return;
  }
  list.innerHTML = Object.entries(subs).map(([ing, alternatives]) => {
    const alts = Array.isArray(alternatives) ? alternatives.join(", ") : alternatives;
    return `
      <div class="col-md-6 col-lg-4">
        <div class="sub-item d-flex align-items-center gap-2 p-2 rounded" style="background:var(--bg-surface);border:1px solid var(--border-color)">
          <span class="sub-from fw-semibold">${capitalize(ing)}</span>
          <i class="bi bi-arrow-right text-muted"></i>
          <span class="sub-to text-success">${escapeHtml(alts)}</span>
        </div>
      </div>`;
  }).join("");
  panel.classList.remove("d-none");
}

// ======================== CUISINE CATEGORY SEARCH ========================
function searchByCuisine(cuisine) {
  const select = document.getElementById("cuisineSelect");
  if (select) {
    const option = [...select.options].find(o => o.value === cuisine.toLowerCase());
    if (option) select.value = option.value;
  }
  document.getElementById("search-section")?.scrollIntoView({ behavior: "smooth" });
  document.getElementById("ingredientInput")?.focus();
}

// ======================== FAVORITES ========================
async function toggleFavorite(recipeId, btn) {
  if (!recipeId) return;
  const isActive = btn.classList.contains("active");
  const endpoint = isActive ? "/api/favorites/remove" : "/api/favorites/add";

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipe_id: recipeId })
    });
    const data = await res.json();

    if (data.status === "added" || data.status === "removed") {
      btn.classList.toggle("active");
      const icon = btn.querySelector("i");
      if (icon) icon.className = btn.classList.contains("active") ? "bi bi-heart-fill" : "bi bi-heart";
      showToast(data.status === "added" ? "Saved!" : "Removed", data.message);

      // Update recipe detail page button if it exists
      const favBtn = document.getElementById("favBtn");
      if (favBtn && favBtn.dataset.recipeId === recipeId) {
        favBtn.dataset.favorited = btn.classList.contains("active") ? "true" : "false";
        const favIcon = favBtn.querySelector("i");
        const favText = favBtn.querySelector("span");
        if (favIcon) favIcon.className = `bi bi-${btn.classList.contains("active") ? "heart-fill" : "heart"} me-1`;
        if (favText) favText.textContent = btn.classList.contains("active") ? "Saved" : "Save Recipe";
      }
    } else if (data.status === "exists") {
      showToast("Already Saved", data.message);
    } else {
      showToast("Error", data.message || "Could not update favorites.");
    }
  } catch (err) {
    showToast("Error", "Network error. Please try again.");
  }
}

// Handle recipe detail page favorite button
const favBtn = document.getElementById("favBtn");
if (favBtn) {
  const isFavorited = favBtn.dataset.favorited === "true";
  if (isFavorited) {
    favBtn.classList.add("active");
  }
  favBtn.addEventListener("click", function () {
    toggleFavorite(this.dataset.recipeId, this);
  });
}

// ======================== LOADING OVERLAY ========================
let loadingOverlay = null;

function showLoadingOverlay(message = "Loading...") {
  if (loadingOverlay) return;
  if (typeof window.showAIThinkingOverlay === "function") {
    window.showAIThinkingOverlay();
    return;
  }
  loadingOverlay = document.createElement("div");
  loadingOverlay.className = "loading-overlay";
  loadingOverlay.id = "loadingOverlay";
  loadingOverlay.innerHTML = `
    <div class="loading-spinner-large"></div>
    <div class="fw-semibold">${message}</div>
    <div class="text-muted small">Powered by IBM Granite AI</div>
  `;
  document.body.appendChild(loadingOverlay);
}

function hideLoadingOverlay() {
  if (typeof window.hideAIThinkingOverlay === "function") {
    window.hideAIThinkingOverlay();
    return;
  }
  const overlay = document.getElementById("loadingOverlay");
  if (overlay) {
    overlay.remove();
    loadingOverlay = null;
  }
}

// ======================== TOAST ========================
function showToast(title, body, type = "info") {
  const toastEl = document.getElementById("appToast");
  const titleEl = document.getElementById("toastTitle");
  const bodyEl = document.getElementById("toastBody");
  if (!toastEl) return;

  titleEl.textContent = title;
  bodyEl.textContent = body;

  // Update icon based on type
  const icon = toastEl.querySelector(".bi");
  if (icon) {
    icon.className = type === "success"
      ? "bi bi-check-circle-fill text-success me-2"
      : type === "error"
      ? "bi bi-exclamation-triangle-fill text-danger me-2"
      : "bi bi-info-circle text-primary me-2";
  }

  const toast = new bootstrap.Toast(toastEl, { delay: 3500 });
  toast.show();
}

// ======================== SCROLL ANIMATIONS ========================
function observeAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1";
        entry.target.style.transform = "translateY(0)";
      }
    });
  }, { threshold: 0.1 });

  // Skip recipe cards that use the recipe-card-enter animation
  document.querySelectorAll(".category-card, .step-card, .glass-card:not(.search-card)").forEach(el => {
    el.style.opacity = "0";
    el.style.transform = "translateY(20px)";
    el.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    observer.observe(el);
  });
}

// ======================== TOOLTIPS ========================
function initTooltips() {
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));
}

function initSectionReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('.section-title, .hero-content, .search-card, .ai-response-panel, .recipe-card-v2, .category-card, .step-card, .glass-card').forEach(el => {
    el.classList.add('reveal-on-scroll');
    observer.observe(el);
  });
}

function initRippleButtons() {
  document.addEventListener('click', (event) => {
    const trigger = event.target.closest('a, button, .btn, .voice-btn, .timeline-step-timer-btn');
    if (!trigger || trigger.classList.contains('navbar-toggler')) return;
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    const rect = trigger.getBoundingClientRect();
    ripple.style.left = `${event.clientX - rect.left}px`;
    ripple.style.top = `${event.clientY - rect.top}px`;
    trigger.appendChild(ripple);
    ripple.addEventListener('animationend', () => ripple.remove(), { once: true });
  });
}

// ======================== HISTORY PAGE FILTER ========================
(function initHistorySearch() {
  const input = document.getElementById("historySearchInput");
  if (!input) return;

  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    document.querySelectorAll(".history-filterable").forEach(card => {
      const text = card.textContent.toLowerCase();
      const col = card.closest("[class^='col']") || card.closest(".col-md-6");
      if (col) col.style.display = text.includes(query) ? "" : "none";
    });
  });
})();

// ======================== HERO PARTICLES ========================
(function initParticles() {
  const container = document.getElementById("heroParticles");
  if (!container) return;
  const emojis = ["🍅", "🧅", "🧄", "🌶️", "🫑", "🥕", "🧅", "🌿", "🥦", "🍋"];
  for (let i = 0; i < 15; i++) {
    const p = document.createElement("div");
    p.textContent = emojis[Math.floor(Math.random() * emojis.length)];
    p.style.cssText = `
      position:absolute;
      font-size:${16 + Math.random() * 20}px;
      left:${Math.random() * 100}%;
      top:${Math.random() * 100}%;
      opacity:${0.05 + Math.random() * 0.12};
      animation:float ${4 + Math.random() * 4}s ease-in-out infinite;
      animation-delay:${Math.random() * 4}s;
      pointer-events:none;
    `;
    container.appendChild(p);
  }
})();

// ======================== UTILITY FUNCTIONS ========================
function capitalize(str) {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getDifficultyColor(difficulty) {
  const map = { "Easy": "success", "Medium": "warning", "Hard": "danger" };
  return map[difficulty] || "secondary";
}

function getCuisineEmoji(cuisine) {
  const map = {
    "Indian": "🍛", "Italian": "🍝", "Chinese": "🥢",
    "Mexican": "🌮", "Thai": "🍜", "American": "🍔",
    "Japanese": "🍱", "Mediterranean": "🥗"
  };
  return map[cuisine] || "🍽️";
}

// Make functions globally accessible
window.searchByCuisine = searchByCuisine;
window.toggleFavorite = toggleFavorite;
window.removeIngredient = removeIngredient;
window.animateCountUp = animateCountUp;
window.showToast = showToast;
