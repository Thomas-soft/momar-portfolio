# Portfolio de Momar Gaye

Site portfolio de Momar Gaye, filmmaker, monteur vidéo et étalonneur.
Adresse : https://thomas-soft.github.io/momar-portfolio/

## Comment c'est fait

- Un site statique : HTML, CSS et JavaScript, **sans framework et sans compilation**.
  On modifie un fichier, on recharge la page, c'est tout.
- Hébergement gratuit sur **GitHub Pages**.
- Les médias du site sont produits par deux scripts Python (avec ffmpeg) à partir des vidéos originales.
  Les originaux ne sont jamais modifiés et ne sont **pas** publiés : ils restent dans `originaux/`, à part.

```
site/                  le site publié
  index.html           la page
  content.js           TOUT le contenu (textes, projets, comparateurs, galerie, contact)
  assets/style.css     la mise en forme
  assets/app.js        le fonctionnement (lecteur vidéo, comparateurs, langues…)
  media/               vidéos et images prêtes pour le web
scripts/
  medias_projets.py    médias des projets, vidéo de fond, images de l'À propos et de partage,
                       galerie d'étalonnage des projets sans version LOG
  medias_etalonnage.py comparateurs LOG / GRADED et galerie d'étalonnage de Maroc et Training
originaux/             vidéos d'origine (jamais publiées)
deploy.sh              mise en ligne
```

## Voir le site sur son ordinateur

Il suffit d'ouvrir `site/index.html` dans un navigateur.
Pour que l'avance rapide dans les vidéos marche aussi, lancer plutôt un petit serveur :

```
npx --yes http-server site -p 8765 -c-1
```

puis ouvrir http://localhost:8765 (arrêter avec Ctrl+C).

## Modifier un texte ou une information

Tout se passe dans **`site/content.js`**, qui est commenté en français :

- un texte traduit s'écrit `{ fr: "…", en: "…" }` ;
- un champ laissé vide (`""`) n'est pas affiché sur le site, sans trou visible ;
- `// À COMPLÉTER` signale une information encore inconnue (description, rôle, catégorie, caméra, profil LOG, Instagram, Vimeo, YouTube…) ;
- pour réordonner les projets, déplacer un bloc `{ … }` dans la liste `projets` ; pour en retirer un, effacer son bloc.

Exemples : l'Instagram se met dans `contact.instagram` (une adresse, ou une liste d'adresses
`["https://…", "https://…"]` pour plusieurs comptes ; pareil pour `vimeo` et `youtube`),
la description d'un projet dans `description`,
sa catégorie dans `categorie` (`"filmmaking"`, `"editing"` ou `"color"`).

## Ajouter un projet

1. Mettre la vidéo (.mov ou .mp4) dans `originaux/`.
2. Ouvrir `scripts/medias_projets.py` et, en haut du fichier :
   - ajouter une ligne dans `PROJETS` : un identifiant court sans espace (ex. `"mon-projet"`), le chemin du fichier et le titre ;
   - ajouter ses moments dans `MOMENTS`, en secondes dans la vidéo d'origine :
     `"extrait"` (le passage de 20 à 30 s, ou `None` si la vidéo dure 30 s ou moins : l'extrait est alors la vidéo entière),
     `"apercu"` (6 à 10 s muettes pour le survol de la carte), `"poster"` et `"miniature"` (l'instant de chaque image) ;
   - ajouter l'identifiant à sa place dans `ORDRE`.
3. Lancer, depuis le dossier du projet :
   ```
   python3 -I scripts/medias_projets.py analyse
   python3 -I scripts/medias_projets.py projets mon-projet
   python3 -I scripts/medias_projets.py verifier
   ```
   Cela crée `site/media/projets/mon-projet/` : `apercu.mp4`, `extrait.mp4`, `integrale.mp4`
   (seulement si la vidéo dure plus de 30 s), `poster.jpg` et `miniature.jpg`.
   `planches` produit en plus des planches d'images pour choisir les moments.
4. Dans `site/content.js`, copier le bloc d'un projet existant dans `projets`, changer `id`, `titre`,
   les chemins des médias, et remplir ce qu'on sait. Mettre `integrale: ""` si la vidéo n'en a pas
   (le bouton « Version intégrale » disparaît) et `audio: false` si elle n'a pas de son.

Autres commandes du script : `fond` (vidéo de fond de l'accueil, plans dans `FOND`),
`images` (images de l'À propos et de partage, dans `APROPOS` et `OG`), `tout` (tout refaire dans l'ordre).

## Remplacer un média

- Le plus simple : changer les moments en haut du script, puis relancer la commande avec `--force`, par exemple
  `python3 -I scripts/medias_projets.py projets disney --force`.
  **Sans `--force`, un média déjà produit n'est jamais refait** (les médias sont figés).
- On peut aussi remplacer un fichier de `site/media/` à la main, en gardant le même nom
  (vidéo MP4 H.264, image JPEG en sRGB), ou mettre un autre chemin dans `content.js`.

## Ajouter un comparateur LOG / GRADED ou une image de la galerie

Les comparateurs ont besoin des deux versions du même plan : la version LOG et la version étalonnée.

1. Mettre les deux vidéos dans `originaux/`.
2. Dans `scripts/medias_etalonnage.py`, ajouter le projet dans `PROJETS` (sur le modèle de `maroc`) :
   les deux fichiers, le décalage entre les versions, les numéros d'images des comparateurs (`comparateurs`),
   le passage du comparateur vidéo (`video`) et les images de la galerie (`galerie`).
3. Lancer `python3 -I scripts/medias_etalonnage.py` (ou seulement certaines étapes :
   `analyse planches images videos verif manifeste` ; ajouter `--force` pour refaire un média existant).
4. Dans `site/content.js`, ajouter les lignes correspondantes dans `comparateurs.images`,
   `comparateurs.videos` et `galerie`.

Image de galerie d'un projet sans version LOG : ajouter `(id, instant, position verticale)` dans
`GALERIE` en haut de `scripts/medias_projets.py`, lancer `python3 -I scripts/medias_projets.py galerie`
(image 16:9 `site/media/galerie/<id>-<n>.jpg`), puis l'ajouter dans `galerie` de `site/content.js`.

Règle couleur, essentielle pour un étalonneur : aucun LUT, aucun filtre, aucune correction automatique.
Les vidéos sont étiquetées BT.709 et les images gardent les valeurs de la vidéo avec le profil sRGB
incorporé. Le site n'applique aucun filtre CSS sur les images et les vidéos.

## Brancher un vrai service de formulaire (plus tard)

Aujourd'hui, le formulaire de contact ouvre la messagerie du visiteur avec le message prérempli
(il le dit clairement, et n'affiche aucune fausse confirmation).

Pour recevoir les messages directement :

1. Créer un formulaire gratuit sur **Formspree** (https://formspree.io) ou **FormSubmit** (https://formsubmit.co)
   avec l'adresse de réception (momar.95@live.fr).
2. Copier l'adresse d'envoi donnée par le service (par exemple `https://formspree.io/f/xxxxxxx`).
3. La coller dans `site/content.js`, champ `contact.formEndpoint`, puis publier.

Le site affiche alors « Merci, votre message a bien été envoyé » seulement si le service répond que l'envoi a réussi.

## Publier

```
./deploy.sh
```

Le script vérifie la taille des fichiers, envoie le site sur GitHub et lance la publication.
Le site est en ligne une à deux minutes plus tard, à la même adresse.

## Limites

- GitHub Pages : **moins de 100 Mo par fichier** (le script refuse au-delà de 95 Mo) et **environ 1 Go pour tout le site**.
  Les médias actuels font environ 465 Mo.
- **Chaque média republié reste pour toujours dans l'historique du dépôt** et compte dans sa taille :
  éviter de réencoder et republier les vidéos plusieurs fois.
- Environ 100 Go de trafic par mois : largement suffisant pour un portfolio.
- Le site est public, comme le dépôt GitHub.
