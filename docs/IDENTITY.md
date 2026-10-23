# Identité visuelle — Sébastien Mot (sebastienmot.com)

Document reconstitué à partir de l’historique Git (`accb9c7`, `f8e9796`, `83fbff7`, `13252ca`, `44592a0`), de `template.html` / `maquette.html` et des visuels LinkedIn du propriétaire (fonds noirs, typo blanche, halos bleu électrique + magenta).

## Positionnement

- **Qui** : entrepreneur belge, Bruxelles, 25 ans face aux dirigeants de PME.
- **Ton** : direct, terrain, « d’entrepreneur à entrepreneur » — pas une agence corporate ni un blog WordPress générique.
- **Format** : **affiche / poster digital** — comme les carrousels LinkedIn (« De toute façon, c’est déductible », chiffres en très grand, fond noir).

## Palette

| Rôle | Valeur | Usage |
|------|--------|--------|
| Fond affiche | `#000` / `#05080f` / `#0a0d14` | Hero, cartes éditoriales, pied de page |
| Bleu électrique | `#2f6fe0` (`--brand-blue`) | Accents titres (`em.accent`), halo bas-gauche, liens actifs |
| Magenta / rose | `#e0338f` / `#ff4fa3` (`--brand-pink`) | Accents secondaires, halo bas-droite |
| Navy profond | `#0b1424` → `#1e3e62` | Panneaux latéraux « À la une », projet Nezo |
| Texte sur fond sombre | `#ffffff`, `rgba(255,255,255,.78)` corps | Lisibilité poster |
| Texte sur fond clair | `#030d1b` (`--ink`), `#37465f` (`--slate`) | Bloc « 25 ans » (contraste volontaire) |

**Dégradés signature** (coins bas, radiaux) :

```css
radial-gradient(45% 75% at 0% 100%, rgba(47,111,224,.55–.6), transparent 70%),
radial-gradient(42% 70% at 100% 100%, rgba(190,30,110,.45–.55), transparent 70%),
#000
```

## Typographie

| Usage | Police | Traitement |
|-------|--------|------------|
| Marque, kickers, titres de section | **Montserrat** (woff2 local) | `font-weight: 700–800`, **MAJUSCULES**, tracking serré sur gros titres |
| Corps, UI | **Manrope** | 16–18px, line-height ~1.6 |
| Méta (dates, sources) | **DM Mono** | 11–12px, uppercase, letter-spacing |

Titres de section : classe `.h2` — Montserrat 800, caps, mots en `em.accent` bleu ou `.pink`.

## Motifs récurrents

1. **Lignes verticales** bleue / rose aux bords du hero et du contact (parfois terminées par un point).
2. **Carte hero** : rectangle noir arrondi (~28px), portrait à droite, copy à gauche.
3. **Cartes « poster »** : fond noir + halos ; pas de cartes blanches type CMS dans la grille de posts.
4. **Signature footer** : `SÉBASTIEN MOT • ENTREPRENEUR` (Montserrat, point bleu).
5. **Nav** : barre flottante glass sombre, CTA Contact blanc sur noir.

## Posts LinkedIn (grille éditoriale)

- **Chaque post avec image** : visuel **toujours visible** — cadre **16:10**, fond **noir / halo**, `object-fit: contain` (visuel entier, comme sur LinkedIn), pas de recadrage agressif qui « mange » le texte du carrousel.
- **Sans image** : fallback **affiche** (dégradé bleu/rose + chiffre ou titre du `cover` si présent), jamais une carte texte vide.
- Grille **2 colonnes** desktop, rangées alignées ; pas de carte « wide » pleine largeur dans la grille.
- Extraits : 3–4 lignes max, ellipse propre.

## Sections site

| Section | Fond | Style |
|---------|------|--------|
| Hero | Affiche noire | Poster + portrait |
| 25 ans | Panneau clair | Contraste, chiffres XXL |
| Posts | **Sombre** | Grille éditoriale + images |
| Mes idées | Halos sur noir | 2 cartes poster |
| Projets | Carte Nezo navy/halo | Mock produit |
| Contact | Affiche noire | Colonne liens glass |
| Footer | `#000` | Pilules liens |

## Ce qu’il faut éviter

- Cartes blanches uniformes, ombres grises « Bootstrap / WordPress ».
- Remplacer les visuels LinkedIn par de simples icônes ou fonds gris clair.
- `object-fit: cover` sur les visuels texte des posts.
- Typo titre en minuscules longues (corporate blog).

## Fichiers de référence dans le repo

- `assets/css/site.css` — base + couches « affiche » (v3/v4 hero).
- `assets/css/brand-2026.css` — couche premium oct. 2026 (à charger en dernier).
- `template.html` / `maquette.html` — maquette validée.
- Commits clés : `accb9c7`, `f8e9796`, `13252ca`.

## Motion (2026)

- Entrées douces au scroll (`reveal`), hover carte : léger lift + lueur bleue.
- Respect `prefers-reduced-motion`.
