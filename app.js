const list = document.querySelector("#loop-list");

const catalog = await fetch("./catalog.json").then((response) => {
  if (!response.ok) {
    throw new Error("Could not load catalog.json");
  }
  return response.json();
});

list.replaceChildren(...catalog.loops.map(renderLoop));

function renderLoop(loop) {
  const card = document.createElement("a");
  card.className = "loop-card";
  card.href = `./loops/${loop.id}/LOOP.md`;

  card.innerHTML = `
    <div class="loop-meta">
      <span>${loop.category}</span>
      <span class="tag">${loop.artifact}</span>
    </div>
    <h3>${escapeHtml(loop.title)}</h3>
    <p>${escapeHtml(loop.summary)}</p>
    <p><code>${escapeHtml(loop.stop_condition)}</code></p>
  `;

  return card;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
