# Correctifs visuels & UX — grille posts + audit responsive

## Grille posts (accueil)

| Problème | Correction |
|----------|------------|
| Dernière carte « wide » en pleine largeur (2 colonnes image/texte) → trous dans la grille | Suppression de la classe `wide` ; toutes les cartes suivent le même gabarit vertical |
| Cartes sans image beaucoup plus hautes (clamp 11 lignes) | Clamp uniforme à 4 lignes ; `min-height` forcés retirés |
| Fonds noirs (`media.native`) à côté de cartes blanches | Bandeau média 16:10, dégradé clair, `object-fit: cover` pour toutes les vignettes |
| Pas de visuel pour les posts sans image | Placeholder avec icône source ou chiffre clé (`cover`) dans la zone média |
| Extraits coupés au milieu d’un mot / phrase | `excerptCard()` en une ligne côté JS ; `card_excerpt()` utilise `clip()` côté build |

## Page `/posts/`

| Problème | Correction |
|----------|------------|
| Liste étroite sur grand écran | Grille 2 colonnes ≥ 900px, cartes à hauteur égale |
| Extraits multilignes mal ellipsés | `white-space: normal` + `text-overflow: ellipsis` |

## Article & 404

| Page | Correction |
|------|------------|
| Post individuel | Image limitée en hauteur (`max-height: 72vh`) pour éviter les visuels disproportionnés |
| 404 | Contenu et actions centrés ; liste « Derniers posts » limitée en largeur |

## Pied de page

| Problème | Correction |
|----------|------------|
| Tagline en `nowrap` sur desktop → débordement possible | Retour à `white-space: normal` + `max-width` |

## Captures (avant / après)

Fichiers dans `docs/screenshots/` :

- `before-*` / `after-*` pour **accueil**, **liste posts**, **article exemple**, **404**
- Viewports : **1440**, **1280**, **430**, **360**

Script de régénération : `python3 scripts/capture_screenshots.py before|after` (serveur local sur `dist/` port 8765).
