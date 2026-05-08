// Tabs --------------------------------------------------------------
const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".panel");

tabs.forEach((t) =>
  t.addEventListener("click", () => {
    const id = t.dataset.tab;
    tabs.forEach((x) => x.classList.toggle("active", x === t));
    panels.forEach((p) => p.classList.toggle("active", p.dataset.panel === id));
    if (id === "ai") loadSuggestionsOnce();
  })
);

// AI panel -----------------------------------------------------------
const PROPERTY_ID = "kerala-house-stay";
const suggestionsEl = document.getElementById("suggestions");
const chatEl = document.getElementById("chat");
const composer = document.getElementById("composer");
const promptInput = document.getElementById("prompt-input");
const sendBtn = document.getElementById("send-btn");

let suggestionsLoaded = false;

async function loadSuggestionsOnce() {
  if (suggestionsLoaded) return;
  suggestionsLoaded = true;

  try {
    const res = await fetch(`/api/suggestions?property_id=${PROPERTY_ID}`);
    const data = await res.json();
    suggestionsEl.innerHTML = "";
    for (const s of data.suggestions) {
      const card = document.createElement("div");
      card.className = "suggestion";
      card.innerHTML = `
        <img src="${s.image_url}" alt="${s.label}" loading="lazy" />
        <div class="suggestion-label">${s.label}</div>
      `;
      card.addEventListener("click", () => {
        promptInput.value = s.prompt;
        composer.requestSubmit();
      });
      suggestionsEl.appendChild(card);
    }
  } catch (e) {
    suggestionsEl.innerHTML =
      '<p class="muted">Couldn\'t load suggestions. Try the chat below.</p>';
    console.error(e);
  }
}

// Chat ---------------------------------------------------------------
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

function addBotImage(text, imageUrl, caption) {
  const wrap = document.createElement("div");
  wrap.className = "msg msg-bot";
  wrap.innerHTML = `
    <div class="bubble">
      ${text ? escape(text) : ""}
      <img src="${imageUrl}" alt="${escape(caption || "AI generated scene")}" />
      ${caption ? `<div class="caption">${escape(caption)}</div>` : ""}
    </div>
  `;
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function escape(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function getHeroImageUrl() {
  // The property's hero photo — used as the Flux Kontext reference image.
  const img = document.querySelector(".gallery-hero img");
  return img ? img.src : null;
}

composer.addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) return;

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
        image_url: getHeroImageUrl(),
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    thinking.remove();
    addBotImage("", data.image_url, data.caption);
  } catch (err) {
    thinking.remove();
    addBotImage(
      "Hmm, I couldn't generate that scene. Try another description?",
      "",
      String(err)
    );
  } finally {
    sendBtn.disabled = false;
    promptInput.focus();
  }
});
