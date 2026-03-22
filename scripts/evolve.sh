#!/usr/bin/env bash
# evolve.sh — Lance le cycle d'auto-amélioration Homunculus complet
#
# Usage:
#   bash scripts/evolve.sh            # cluster + show-candidates + generate-proposal
#   bash scripts/evolve.sh --show-only  # cluster + show-candidates uniquement

set -euo pipefail

SHOW_ONLY="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTINCT_LOOP="$PROJECT_ROOT/scripts/instinct-loop.py"

if [ ! -f "$INSTINCT_LOOP" ]; then
    echo "[evolve] Erreur : instinct-loop.py introuvable à $INSTINCT_LOOP"
    exit 1
fi

echo "claudekit -- Cycle d'evolution Homunculus"
echo "=========================================="
echo ""

# 1. Recalculer les clusters
echo "--- Etape 1 : Recalcul des clusters ---"
python3 "$INSTINCT_LOOP" --cluster
echo ""

# 2. Afficher les candidats
echo "--- Etape 2 : Candidats a promotion ---"
python3 "$INSTINCT_LOOP" --show-candidates

# 3. Si pas --show-only, generer les propositions
if [ -z "$SHOW_ONLY" ]; then
    echo ""
    echo "--- Etape 3 : Propositions generees ---"
    python3 "$INSTINCT_LOOP" --generate-proposal
    echo ""
    echo "=========================================="
    echo "Instructions :"
    echo "  1. Lis les propositions ci-dessus"
    echo "  2. Copie le contenu skill dans .claude/skills/ si pertinent"
    echo "  3. Insere la regle CLAUDE.md dans la section appropriee si pertinent"
    echo "  4. Aucune modification automatique n'a ete effectuee"
    echo "=========================================="
else
    echo ""
    echo "  Mode --show-only : propositions non generees."
    echo "  Lance sans --show-only pour generer les propositions."
fi
