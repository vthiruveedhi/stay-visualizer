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
const SUGGESTIONS = [
  { scene: "pool",     emoji: "🏊", label: "Pool day with friends",
    prompt: "12 friends laughing by the pool, candid, golden-hour" },
  { scene: "bedroom",  emoji: "🛏",  label: "Lazy morning in the bedroom",
    prompt: "a couple having morning coffee in bed, warm light" },
  { scene: "hall",     emoji: "🛋",  label: "Movie night in the hall",
    prompt: "friends on a sofa watching a movie, popcorn, dim cozy lighting" },
  { scene: "dining",   emoji: "🍽",  label: "Family dinner",
    prompt: "a family eating dinner at a long wooden table, festive" },
  { scene: "kitchen",  emoji: "🍳",  label: "Cooking together",
    prompt: "two friends cooking together in the kitchen, candid" },
  { scene: "garden",   emoji: "🌳",  label: "Lawn party at dusk",
    prompt: "a group celebrating outdoors on a lawn at dusk, fairy lights" },
];

// Free-text prompts get matched to a scene by keyword so we still pick a
// room-specific reference image. Falls back to the hero (exterior) when
// nothing matches.
const SCENE_KEYWORDS = {
  pool:    ["pool", "swim", "splash", "water"],
  bedroom: ["bedroom", "bed", "sleep", "morning", "coffee in bed"],
  hall:    ["hall", "living", "sofa", "couch", "movie", "tv", "lounge"],
  dining:  ["dining", "dinner", "lunch", "table", "feast", "eat", "food"],
  kitchen: ["kitchen", "cook", "cooking", "chef"],
  garden:  ["lawn", "garden", "outdoor", "outside", "party", "bbq", "barbecue"],
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
  return "exterior"; // hero is the fallback reference
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
  // If the click came from a suggestion chip, it preset data-scene; otherwise
  // we keyword-match the free text.
  const scene = matchScene(prompt);
  const referenceUrl = getImageForScene(scene) || getImageForScene("exterior");

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
