(() => {
const BASE = document.documentElement.dataset.basePath || "";
const bp = (path) => {
  if (!path.startsWith("/")) path = "/" + path;
  return `${BASE}${path}`;
};

document.documentElement.classList.add("js");
requestAnimationFrame(() => document.documentElement.classList.add("is-loaded"));

const ICON = {
  x:
    '<span class="ico" title="X"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.9 2H22l-6.8 7.8L23 22h-6.2l-4.8-6.3L6.4 22H3.3l7.3-8.3L1 2h6.3l4.4 5.8L18.9 2zm-1.1 18h1.7L6.3 3.9H4.5L17.8 20z"/></svg></span>',
  linkedin:
    '<span class="ico li" title="LinkedIn"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 11-.02 5 2.5 2.5 0 01.02-5zM3 9.75h4V21H3V9.75zM9.5 9.75h3.8v1.6h.06c.53-1 1.83-2.06 3.77-2.06 4.03 0 4.77 2.65 4.77 6.1V21h-4v-5.05c0-1.21-.02-2.77-1.69-2.77-1.69 0-1.95 1.32-1.95 2.68V21h-4V9.75z"/></svg></span>',
};
const NAME = { x: "X", linkedin: "LinkedIn" };
const PAGE = 5;

const dataEl = document.getElementById("posts-data");
if (!dataEl) return;

const rawPosts = JSON.parse(dataEl.textContent).posts.slice();
const all = window.sortSitePosts ? window.sortSitePosts(rawPosts) : rawPosts;

const esc = (s) =>
  s
    .replace(/[ \u00a0]+([:;?!»])/g, "\u00a0$1")
    .replace(/«[ \u00a0]+/g, "«\u00a0")
    .replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const link = (s) => esc(s).replace(/(https?:\/\/\S+)/g, '<a href="$1" target="_blank" rel="noreferrer">$1</a>');
const split = (p) => {
  const [t, ...r] = p.text.split("\n");
  return [t, r.join("\n").replace(/^\n+/, "")];
};

let filter = "all";
let pages = 1;

/* Extrait propre : lignes conservées, lignes vides retirées (le clamp CSS coupe à 4 lignes). */
const excerpt = (b) =>
  b
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l && !/^https?:\/\/\S+$/.test(l))
    .join("\n");

/* Un chiffre clé (cover contenant un nombre) devient un encart compact ; sinon rien. */
const hasFigure = (p) => !p.image && p.cover && /\d/.test(p.cover.big || "");

function postHref(p) {
  return p.slug ? bp(`/posts/${p.slug}/`) : p.url;
}

function renderFeat() {
  const box = document.getElementById("feat");
  if (!box) return;
  box.innerHTML = "";
  const p = all.find((x) => x.featured);
  if (!p || (filter !== "all" && filter !== p.source)) return;
  const [t, b] = split(p);
  box.innerHTML = `<article class="feat"><div class="feat-body">
   <div class="badge">${ICON[p.source]}<span>À la une</span><span class="d">${NAME[p.source]} · ${esc(p.dateLabel)}</span></div>
   <h3><a href="${postHref(p)}">${esc(t)}</a></h3><p class="txt">${esc(excerpt(b))}</p>
   <div class="actions"><a class="btn-more" href="${postHref(p)}">Lire la suite <span aria-hidden="true">→</span></a><a class="src-link" href="${p.url}" target="_blank" rel="noreferrer">Voir sur ${NAME[p.source]} ↗</a></div></div>
   <div class="feat-side"><div><div class="big">${esc(p.cover.big)}</div><div class="cap">${esc(p.cover.small)}</div></div>
   <ul><li>Devis établi avec un carburant à 1,70 €/L</li><li>Quelques mois plus tard&nbsp;: 1,90 €/L</li><li>Sans mécanisme d'indexation&nbsp;: la hausse est pour toi.</li></ul>
   <q>Et toi&nbsp;: tu les répercutes, ou tu les absorbes&nbsp;?</q></div></article>`;
}

function mediaHtml(p) {
  if (!p.image) return "";
  const imgPath = bp(p.image.startsWith("/") ? p.image : `/${p.image}`);
  return `<figure class="media"><img src="${imgPath}" alt="" loading="lazy" decoding="async"></figure>`;
}

function card(p, i) {
  const [t, b] = split(p);
  const el = document.createElement("article");
  el.className = "post" + (p.image ? "" : " noimg");
  el.style.animationDelay = (i % PAGE) * 50 + "ms";
  const href = postHref(p);
  const ex = excerpt(b);
  const fig = hasFigure(p)
    ? `<p class="figure"><b>${esc(p.cover.big)}</b><span>${esc(p.cover.small)}</span></p>`
    : "";
  el.innerHTML =
    mediaHtml(p) +
    `<div class="post-body"><div class="meta">${ICON[p.source]}<span>${NAME[p.source]} · ${esc(p.dateLabel)}</span>${p.pinned ? '<span class="pin">Épinglé</span>' : ""}</div>
    ${fig}<h3><a href="${href}">${esc(t)}</a></h3>${ex ? `<p class="txt">${esc(ex)}</p>` : ""}
    <div class="actions"><a class="btn-more" href="${href}">Lire la suite <span aria-hidden="true">→</span></a><a class="src-link" href="${p.url}" target="_blank" rel="noreferrer">Voir sur ${NAME[p.source]} ↗</a></div></div>`;
  return el;
}

function render() {
  renderFeat();
  const featShown = !!document.querySelector("#feat .feat");
  const list = all
    .filter((p) => !p.featured)
    .filter((p) => filter === "all" || p.source === filter);
  const g = document.getElementById("post-grid");
  if (!g) return;
  g.innerHTML = "";
  const limit = Math.max(0, pages * PAGE - (featShown ? 1 : 0));
  const visible = list.slice(0, limit);
  visible.forEach((p, i) => g.appendChild(card(p, i)));
  if (visible.length % 2 === 1 && g.lastElementChild) g.lastElementChild.classList.add("wide");
  const rest = list.length - visible.length;
  const btnLoad = document.getElementById("btn-load");
  if (btnLoad) {
    btnLoad.hidden = rest <= 0;
    btnLoad.textContent = "Voir plus";
    btnLoad.setAttribute("aria-label", `Voir ${Math.min(PAGE, rest)} posts de plus`);
  }
}

const btnLoad = document.getElementById("btn-load");
if (btnLoad) btnLoad.onclick = () => {
  pages += 1;
  render();
};

document.querySelectorAll("[data-c]").forEach((s) => {
  const f = s.dataset.c;
  s.textContent = all.filter((p) => f === "all" || p.source === f).length;
});

document.querySelectorAll(".filters button").forEach((b) => {
  b.onclick = () => {
    document.querySelectorAll(".filters button").forEach((x) => x.setAttribute("aria-pressed", x === b));
    filter = b.dataset.f;
    pages = 1;
    render();
  };
});

render();
})();
