#!/bin/zsh
# Met le portfolio de Momar en ligne sur GitHub Pages (gratuit, compte Thomas-soft).
# Adresse : https://thomas-soft.github.io/momar-portfolio/
# Usage : ./deploy.sh > travail/deploy.log 2>&1   (puis lire la fin du journal)
set -euo pipefail
cd "$(dirname "$0")"

OWNER=Thomas-soft
REPO=momar-portfolio
MAX_MO=95   # GitHub refuse les fichiers de plus de 100 Mo

# 1. Aucun fichier trop gros dans site/
big=$(find site -type f -size +${MAX_MO}M)
if [[ -n "$big" ]]; then echo "Fichiers trop gros (> ${MAX_MO} Mo) :"; echo "$big"; exit 1; fi
echo "Taille du site : $(du -sh site | cut -f1) (limite GitHub Pages : 1 Go)"

# 2. Dépôt git local
if [[ ! -d .git ]]; then
  git init -b main
  git config user.name "$OWNER"
  git config user.email "116298874+Thomas-soft@users.noreply.github.com"
fi

# 3. Dépôt GitHub (public : obligatoire pour Pages gratuit)
if ! gh api "repos/$OWNER/$REPO" >/dev/null 2>&1; then
  gh repo create "$OWNER/$REPO" --public --description "Portfolio de Momar"
fi
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$OWNER/$REPO.git"

# 4. Envoi
git add -A
echo "Fichiers suivis par git (hors site/) :"; git ls-files | grep -v "^site/" || true
echo "Nombre de fichiers dans site/ : $(git ls-files site | wc -l | tr -d " ")"
git commit -q -m "Mise à jour du portfolio" || echo "Rien de nouveau à envoyer."
git push -q -u origin main

# 5. Pages en mode « GitHub Actions » (une seule fois). Le premier envoi a eu lieu
#    avant l'activation : on relance alors la publication.
if ! gh api "repos/$OWNER/$REPO/pages" >/dev/null 2>&1; then
  gh api -X POST "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null
  sleep 5
  gh workflow run deploy-pages.yml -R "$OWNER/$REPO" --ref main
fi

sleep 5
echo "Dernier run : $(gh run list -R "$OWNER/$REPO" -L 1 --json databaseId,status,conclusion -q '.[0] | "\(.databaseId) \(.status) \(.conclusion)"')"
echo "Publication lancée : https://thomas-soft.github.io/$REPO/ (en ligne 1 à 2 min après)"
