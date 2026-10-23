(() => {
  const root = document.documentElement;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  root.classList.add("has-sig-motion");

  root.dataset.headerTone = "dark";

  /* Ne pas masquer des sections entières (grille posts invisible hors viewport). */
  const revealSelectors = [
    ".sig-page-hero",
    ".posts-archive > li",
    ".post-single-head",
    ".post-single-media",
    ".post-single-body",
    ".related",
    ".page-404 .nf-actions",
    ".idea",
    ".feat",
    ".proj.nezo",
    ".cta-row",
  ];

  const revealTargets = [];
  revealSelectors.forEach((sel) => {
    document.querySelectorAll(sel).forEach((el) => {
      if (el.classList.contains("sig-reveal")) return;
      el.classList.add("sig-reveal");
      revealTargets.push(el);
    });
  });

  revealTargets.forEach((el, i) => {
    el.style.setProperty("--sig-delay", `${Math.min(i % 6, 5) * 70}ms`);
    el.classList.add("is-in");
  });

  const markIn = (el) => el.classList.add("is-in");

  if (!reduced && "IntersectionObserver" in window && revealTargets.length) {
    const revealIo = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            markIn(entry.target);
            revealIo.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.06, rootMargin: "0px 0px 12% 0px" }
    );
    revealTargets.forEach((el) => revealIo.observe(el));
    const flushVisible = () => {
      const vh = window.innerHeight || 800;
      revealTargets.forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.top < vh * 0.92 && r.bottom > 0) markIn(el);
      });
    };
    requestAnimationFrame(flushVisible);
    window.addEventListener("load", flushVisible, { once: true });
  } else {
    revealTargets.forEach(markIn);
  }

  const grid = document.getElementById("post-grid");
  if (grid && "MutationObserver" in window) {
    const cardIo =
      !reduced && "IntersectionObserver" in window
        ? new IntersectionObserver(
            (entries) => {
              entries.forEach((entry) => {
                if (entry.isIntersecting) {
                  entry.target.classList.add("is-in");
                  cardIo.unobserve(entry.target);
                }
              });
            },
            { threshold: 0.08 }
          )
        : null;

    const observeCard = (node) => {
      if (!(node instanceof HTMLElement) || !node.classList.contains("post")) return;
      node.classList.add("sig-reveal", "is-in");
      if (cardIo) cardIo.observe(node);
    };
    grid.querySelectorAll(".post").forEach(observeCard);
    const mo = new MutationObserver((mutations) => {
      mutations.forEach((m) => m.addedNodes.forEach(observeCard));
    });
    mo.observe(grid, { childList: true });
  }
})();
