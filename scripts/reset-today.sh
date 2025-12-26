#!/bin/bash
# Reset today's articles for testing purposes
# Usage: ./scripts/reset-today.sh

set -euo pipefail

CONTAINER="ai-news-postgres"
DB_USER="ainews"
DB_NAME="ainews"

echo "🧹 Nettoyage des données du jour pour tests..."
echo ""

# Count before
ARTICLES_COUNT=$(docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -t -c \
  "SELECT COUNT(*) FROM articles WHERE created_at >= CURRENT_DATE;")
DIGESTS_COUNT=$(docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -t -c \
  "SELECT COUNT(*) FROM daily_digests WHERE date = CURRENT_DATE;")

echo "📊 Données à supprimer:"
echo "   - Articles: $ARTICLES_COUNT"
echo "   - Digests:  $DIGESTS_COUNT"
echo ""

if [[ "${1:-}" != "-y" ]]; then
  read -p "Confirmer la suppression? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Annulé"
    exit 1
  fi
fi

# Delete articles first (foreign key)
docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c \
  "DELETE FROM articles WHERE created_at >= CURRENT_DATE;"

# Delete today's digest
docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c \
  "DELETE FROM daily_digests WHERE date = CURRENT_DATE;"

echo ""
echo "✅ Nettoyage terminé!"
echo ""
echo "Tu peux maintenant relancer le workflow pour un test complet."
