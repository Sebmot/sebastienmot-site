(() => {
  const BASE = document.documentElement.dataset.basePath || "";
  const bp = (path) => {
    if (!path.startsWith("/")) path = "/" + path;
    return `${BASE}${path}`;
  };

  const dataEl = document.getElementById("posts-data");
  const listEl = document.getElementById("posts-archive");
  if (!dataEl || !listEl) return;

  const all = window.sortSitePosts(JSON.parse(dataEl.textContent).posts.slice());
  let filter = "all";

  const esc = (s) =>
    s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function render() {
    const items = all.filter((p) => filter === "all" || p.source === filter);
    listEl.innerHTML = items
      .map((p) => {
        const pin = p.pinned ? ' · <span class="pin">Épinglé</span>' : "";
        const title = p.text.split("\n")[0];
        const body = p.text.split("\n").slice(1).join(" ").trim();
        const excerpt = esc(body.replace(/\s+/g, " ").slice(0, 180) + (body.length > 180 ? "…" : ""));
        return `<li><article>
          <p class="meta-line"><span class="src ${p.source}">${p.source === "x" ? "X" : "LinkedIn"}</span> · <time datetime="${esc(p.date.slice(0, 10))}">${esc(p.dateLabel)}</time>${pin}</p>
          <h2><a href="${bp(`/posts/${p.slug}/`)}">${esc(title)}</a></h2>
          <p class="excerpt">${excerpt}</p>
        </article></li>`;
      })
      .join("");
  }

  document.querySelectorAll("[data-c]").forEach((s) => {
    const f = s.dataset.c;
    s.textContent = all.filter((p) => f === "all" || p.source === f).length;
  });

  document.querySelectorAll(".filters button").forEach((b) => {
    b.onclick = () => {
      document.querySelectorAll(".filters button").forEach((x) => x.setAttribute("aria-pressed", x === b));
      filter = b.dataset.f;
      render();
    };
  });

  render();
})();
