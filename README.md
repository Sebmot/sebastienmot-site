# sebastienmot.com

Site statique personnel de **Sébastien Mot** ([sebastienmot.com](https://sebastienmot.com)).

## Développement

Prérequis : Python 3.10+.

```bash
pip install -r requirements.txt
python3 build.py
```

Le site généré se trouve dans `dist/`. Pour prévisualiser :

```bash
cd dist && python3 -m http.server 8080
```

Puis ouvrir [http://localhost:8080](http://localhost:8080).

## Ajouter un post

1. Éditer `posts.json` : dupliquer un objet dans le tableau `posts` et renseigner :
   - `source` : `x` ou `linkedin`
   - `date` : `AAAA-MM-JJ` (tri)
   - `dateLabel` : libellé affiché (ex. `17 mai 2026`)
   - `url` : lien vers le post d’origine
   - `image` : chemin sous `img/` ou `null`
   - `cover` : `null` ou `{ "big": "…", "small": "…" }` pour une carte typographique
   - `pinned` : `true` / `false`
   - `featured` : un seul post à la une (`true`)
   - `text` : texte intégral ; **la première ligne = le titre** ; `\n\n` = paragraphes
2. Ajouter les images éventuelles dans `img/`.
3. Lancer `python3 build.py`.

Le générateur crée :

- `dist/index.html` — accueil
- `dist/posts/` — liste de tous les posts
- `dist/posts/<slug>/index.html` — une page par post
- `dist/sitemap.xml`, `dist/robots.txt`, `dist/feed.xml`
- `dist/llms.txt` et `dist/llms-full.txt` (résumés pour moteurs IA)

## Structure

| Chemin | Rôle |
|--------|------|
| `posts.json` | Données des posts |
| `img/` | Images sources |
| `assets/css/` | Styles |
| `assets/js/home.js` | Filtres et grille sur l’accueil |
| `templates/` | Gabarits Jinja2 |
| `build.py` | Générateur |
| `template.html` | Maquette validée (référence design) |

## Déploiement

À chaque push sur `main`, GitHub Actions exécute `build.py` et publie `dist/` sur GitHub Pages. Le fichier `dist/CNAME` contient `sebastienmot.com` (DNS géré en dehors du dépôt).
