// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------
const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".panel");

tabs.forEach((t) =>
  t.addEventListener("click", () => {
    const id = t.dataset.tab;
    tabs.forEach((x) => x.classList.toggle("active", x === t));
    panels.forEach((p) => p.classList.toggle("active", p.dataset.panel === id));
    if (id === "ai") renderSuggestionsOnce();
  })
);

// ---------------------------------------------------------------------------
// AI panel
// ---------------------------------------------------------------------------
const PROPERTY_ID = "kerala-house-stay";
const suggestionsEl = document.getElementById("suggestions");
const chatEl = document.getElementById("chat");
const composer = document.getElementById("composer");
const promptInput = document.getElementById("prompt-input");
const sendBtn = document.getElementById("send-btn");

// Each suggestion is bound to a `scene` id. The scene id matches the
// `data-scene` attribute on a gallery <img>, so we render the visualization
// using the property's actual photo of that room.
// Each prompt describes ONLY the people. Atmosphere words like "fairy
// lights", "festive", "warm overhead lights" are intentionally absent —
// Flux Kontext will add those exact things to the rendered scene if it
// sees them in the prompt, breaking the "this is the actual property"
// illusion.
const SUGGESTIONS = [
  { scene: "pool",     emoji: "🏊", label: "Pool day with friends",
    prompt: "12 friends standing in the pool, smiling" },
  { scene: "bedroom",  emoji: "🛏",  label: "Morning in the bedroom",
    prompt: "a couple sitting on the bed having coffee" },
  { scene: "hall",     emoji: "🛋",  label: "Hanging out in the hall",
    prompt: "a group of friends sitting on the sofa" },
  { scene: "dining",   emoji: "🍽",  label: "Family dinner",
    prompt: "a family of 12 sitting around the dining table eating" },
  { scene: "patio",    emoji: "🪑", label: "On the patio",
    prompt: "two couples sitting at the patio table chatting" },
  { scene: "garden",   emoji: "🌳",  label: "On the lawn",
    prompt: "a group of friends standing on the lawn" },
];

// Used for free-text input only (chip clicks bypass this — see below).
// Patio is checked BEFORE dining because "patio table" should not
// match dining's "table"… and "table" is excluded from dining for the
// same reason.
const SCENE_KEYWORDS = {
  pool:    ["pool", "swim", "splash"],
  bedroom: ["bedroom", "bed", "sleep"],
  hall:    ["hall", "living", "sofa", "couch", "movie", "lounge"],
  patio:   ["patio", "balcony", "veranda", "terrace"],
  dining:  ["dining", "dinner", "lunch", "feast", "eat", "kitchen", "cook"],
  garden:  ["lawn", "garden", "outdoor", "outside", "bbq", "barbecue"],
};

let suggestionsRendered = false;

function renderSuggestionsOnce() {
  if (suggestionsRendered) return;
  suggestionsRendered = true;

  suggestionsEl.innerHTML = SUGGESTIONS.map((s) => `
    <button class="chip-suggestion" type="button"
            data-scene="${s.scene}"
            data-prompt="${escapeAttr(s.prompt)}">
      ${s.emoji} ${escape(s.label)}
    </button>
  `).join("");

  suggestionsEl.querySelectorAll(".chip-suggestion").forEach((el) => {
    el.addEventListener("click", () => {
      promptInput.value = el.dataset.prompt;
      // Skip keyword matching on chip click — we already know the scene.
      composer.dataset.forcedScene = el.dataset.scene;
      composer.requestSubmit();
    });
  });
}

function getImageForScene(scene) {
  const img = document.querySelector(`img[data-scene="${scene}"]`);
  return img ? img.src : null;
}

function matchScene(prompt) {
  const p = prompt.toLowerCase();
  for (const [scene, keys] of Object.entries(SCENE_KEYWORDS)) {
    if (keys.some((k) => p.includes(k))) return scene;
  }
  return "pool"; // hero is the fallback reference
}

// ---------------------------------------------------------------------------
// Chat rendering
// ---------------------------------------------------------------------------
function addUserMessage(text) {
  const wrap = document.createElement("div");
  wrap.className = "msg msg-user";
  wrap.innerHTML = `<div class="bubble">${escape(text)}</div>`;
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function addThinking() {
  const wrap = document.createElement("div");
  wrap.className = "msg msg-bot";
  wrap.innerHTML = `<div class="bubble"><span class="thinking">imagining your scene</span></div>`;
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
  return wrap;
}

function addBotImage(imageUrl, caption) {
  const wrap = document.createElement("div");
  wrap.className = "msg msg-bot";
  wrap.innerHTML = `
    <div class="bubble">
      <img src="${imageUrl}" alt="${escape(caption || "AI generated scene")}" />
      ${caption ? `<div class="caption">${escape(caption)}</div>` : ""}
    </div>
  `;
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function addBotError(text) {
  const wrap = document.createElement("div");
  wrap.className = "msg msg-bot";
  wrap.innerHTML = `<div class="bubble">${escape(text)}</div>`;
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function escape(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}
function escapeAttr(s) { return escape(s); }

// ---------------------------------------------------------------------------
// Submit
// ---------------------------------------------------------------------------
composer.addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) return;

  // Decide which gallery image to use as the Flux Kontext reference.
  // Chip clicks set `composer.dataset.forcedScene` so the matcher is
  // bypassed; free-text prompts go through keyword matching.
  const forced = composer.dataset.forcedScene;
  delete composer.dataset.forcedScene;
  const scene = forced || matchScene(prompt);
  const referenceUrl = getImageForScene(scene) || getImageForScene("pool");

  addUserMessage(prompt);
  promptInput.value = "";
  sendBtn.disabled = true;

  const thinking = addThinking();

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        property_id: PROPERTY_ID,
        prompt,
        guests: 12,
        image_url: referenceUrl,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    thinking.remove();
    addBotImage(data.image_url, data.caption);
  } catch (err) {
    thinking.remove();
    addBotError("Hmm, I couldn't generate that scene. Try another description?");
    console.error(err);
  } finally {
    sendBtn.disabled = false;
    promptInput.focus();
  }
});
