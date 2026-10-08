(() => {
  /* La liste complète est rendue côté serveur (fonctionne sans JS).
     Avec JS : filtres X / LinkedIn et affichage 5 par 5, par filtre. */
  const PAGE = 5;
  document.documentElement.classList.add("js");
  const listEl = document.getElementById("posts-archive");
  const btn = document.getElementById("btn-load");
  if (!listEl) return;

  const items = Array.from(listEl.children);
  let filter = "all";
  let pages = 1;

  function render() {
    const matching = items.filter((li) => filter === "all" || li.dataset.source === filter);
    const limit = pages * PAGE;
    items.forEach((li) => {
      li.hidden = true;
    });
    matching.slice(0, limit).forEach((li) => {
      li.hidden = false;
    });
    const rest = matching.length - Math.min(limit, matching.length);
    if (btn) {
      btn.hidden = rest <= 0;
      btn.setAttribute("aria-label", `Voir ${Math.min(PAGE, rest)} posts de plus`);
    }
  }

  document.querySelectorAll("[data-c]").forEach((s) => {
    const f = s.dataset.c;
    s.textContent = items.filter((li) => f === "all" || li.dataset.source === f).length;
  });

  document.querySelectorAll(".filters button").forEach((b) => {
    b.onclick = () => {
      document.querySelectorAll(".filters button").forEach((x) => x.setAttribute("aria-pressed", x === b));
      filter = b.dataset.f;
      pages = 1;
      render();
    };
  });

  if (btn) {
    btn.onclick = () => {
      pages += 1;
      render();
    };
  }

  render();
})();
