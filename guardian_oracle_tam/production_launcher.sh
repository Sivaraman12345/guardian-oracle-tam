#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# Guardian Oracle TAM — Production Launcher
#
# Runs unit tests first. ONLY if they pass does it start the
# Edge Node application. Strict error handling throughout.
# ──────────────────────────────────────────────────────────────
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

echo "============================================================"
echo "  Guardian Oracle TAM v1.0 — Production Launcher"
echo "============================================================"
echo ""

# ── Step 1: Run unit tests ───────────────────────────────────
echo "[1/2] Running unit tests..."
echo ""

python -m pytest tests/test_twis.py tests/test_escape_reflex.py -v --tb=short

echo ""
echo "[PASS] All unit tests passed."
echo ""

# ── Step 2: Start the Edge Node ──────────────────────────────
echo "[2/2] Starting Guardian Oracle TAM Edge Node..."
echo ""

exec python main.py "$@"
