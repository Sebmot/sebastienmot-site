(() => {
  if (!("IntersectionObserver" in window)) {
    document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
    return;
  }
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) {
    document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
    return;
  }
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        e.target.classList.add("is-visible");
        io.unobserve(e.target);
      });
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
  );
  const scan = () => {
    document.querySelectorAll(".reveal:not(.is-visible)").forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.top < window.innerHeight * 0.92 && r.bottom > 0) {
        el.classList.add("is-visible");
        return;
      }
      io.observe(el);
    });
  };
  scan();
  document.addEventListener("posts-rendered", scan);
})();
