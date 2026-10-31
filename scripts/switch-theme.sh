#!/usr/bin/env bash
# Usage: ./scripts/switch-theme.sh [theme]
# Sans argument, utilise le thème écrit dans active-theme.txt.
set -euo pipefail
cd "$(dirname "$0")/.."

THEME="${1:-$(tr -d '[:space:]' < active-theme.txt)}"
DIR="themes/$THEME"

[ -f "$DIR/README.template.md" ] || { echo "Thème introuvable : $THEME"; ls themes; exit 1; }
[ -f "$DIR/theme.env" ] && source "$DIR/theme.env"

sed -e "s#{{ASSETS}}#$DIR/assets#g" \
    -e "s#{{ACCENT}}#${ACCENT:-d60cfe}#g" \
    "$DIR/README.template.md" > README.md

echo "$THEME" > active-theme.txt
echo "✔ Thème actif : $THEME"
