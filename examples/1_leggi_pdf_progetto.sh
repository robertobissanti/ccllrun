#!/usr/bin/env bash
# =============================================================================
# EXAMPLE 1 — Read PDFs from a project folder without RAG.
#
# Rationale: a project folder with a few dozen files usually does not need a
# vector index. Claude Code opens PDFs through its tools (Read/Grep), and the
# ccllrun proxy converts them to text/images according to `pdf_mode`. The model
# sees whole documents rather than fragments, which is often more accurate than
# RAG on small corpora. No pre-indexing is required: new PDFs are immediately
# available.
#
# Usage:
#   ./examples/1_leggi_pdf_progetto.sh /percorso/cartella/progetto "la tua domanda"
#
# Requires: running stack (`ccllrun servers`) and `claude` in PATH.
# =============================================================================
set -euo pipefail

DIR="${1:?uso: $0 <cartella_progetto> [domanda]}"
DOMANDA="${2:-Elenca i PDF presenti, e per ogni datasheet riporta marca, modello e i dati elettrici principali (Voc, Isc, Vmp, Imp, Pmax).}"

[[ -d "$DIR" ]] || { echo "cartella non valida: $DIR" >&2; exit 1; }
command -v claude >/dev/null || { echo "claude non nel PATH" >&2; exit 1; }

echo "[esempio1] cartella: $DIR"
echo "[esempio1] PDF trovati:"
find "$DIR" -maxdepth 2 -iname '*.pdf' | sed 's/^/  - /' || true
echo

# -p is non-interactive print mode. ccllrun points Claude Code at the local
# model through ANTHROPIC_BASE_URL. Grant folder access with --add-dir and let
# Claude Code use its normal file/PDF tools.
#
# This example does not use the embedding model. Retrieval is handled by Claude
# Code reading files on demand, not by a precomputed vector index.
ccllrun -p --add-dir "$DIR" \
  "Nella cartella $DIR ci sono dei PDF di progetto fotovoltaico. $DOMANDA"
