#!/usr/bin/env bash
# Paper Translator — Claude Code manual installer
#
# Usage:
#   bash install.sh [copy|link]
#
# Installs the plugin into ~/.claude/plugins/paper-translator.
# The "copy" mode (default) copies files; "link" creates a symlink
# (useful for development).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_SRC="${SCRIPT_DIR}/plugins/paper-translator"
PLUGIN_NAME="paper-translator"

if [ -n "${CLAUDE_HOME:-}" ]; then
  TARGET_BASE="${CLAUDE_HOME}/plugins"
else
  TARGET_BASE="${HOME}/.claude/plugins"
fi
TARGET="${TARGET_BASE}/${PLUGIN_NAME}"

echo "[install] Paper Translator plugin (Claude Code)"
echo "  source: ${PLUGIN_SRC}"
echo "  target: ${TARGET}"

if [ ! -d "${PLUGIN_SRC}" ]; then
  echo "[error] plugin source not found: ${PLUGIN_SRC}"
  echo "        Make sure you are running this from the repository root."
  exit 1
fi

mkdir -p "${TARGET_BASE}"

if [ -e "${TARGET}" ] || [ -L "${TARGET}" ]; then
  echo "[warn] target already exists: ${TARGET}"
  read -r -p "  overwrite? [y/N] " ans
  case "${ans}" in
    y|Y|yes|YES) rm -rf "${TARGET}" ;;
    *) echo "[abort] keeping existing install"; exit 1 ;;
  esac
fi

MODE="${1:-copy}"
case "${MODE}" in
  copy)    cp -r "${PLUGIN_SRC}" "${TARGET}" ;;
  link)    ln -s "${PLUGIN_SRC}" "${TARGET}" ;;
  *) echo "[error] unknown mode: ${MODE} (use 'copy' or 'link')"; exit 2 ;;
esac
echo "[ok] installed (${MODE})"

echo
echo "[check] Python dependencies"
if python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
  echo "  Python: $(python --version)"
else
  echo "[error] Python 3.10+ required"
  exit 3
fi

MISSING=()
for pkg in fitz markdown pymdownx; do
  if python -c "import ${pkg}" 2>/dev/null; then
    echo "  ok ${pkg}"
  else
    echo "  !! ${pkg} (missing)"
    case "${pkg}" in
      fitz) MISSING+=("pymupdf") ;;
      pymdownx) MISSING+=("pymdown-extensions") ;;
      *) MISSING+=("${pkg}") ;;
    esac
  fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
  echo
  echo "[next] install missing packages:"
  echo "  pip install ${MISSING[*]}"
fi

echo
echo "[check] Optional tools"
command -v pandoc   >/dev/null 2>&1 && echo "  ok pandoc"   || echo "  -- pandoc (optional, fallback exists)"
command -v lualatex >/dev/null 2>&1 && echo "  ok lualatex" || echo "  -- lualatex (optional, only for PDF output)"
command -v code     >/dev/null 2>&1 && echo "  ok code"     || echo "  -- code (optional, for VSCode preview)"

echo
echo "[done] Paper Translator installed at ${TARGET}"
echo "       Use in Claude Code: /translate-paper <pdf-path>"
echo
echo "       Or install via plugin marketplace instead:"
echo "         /plugin marketplace add ryotaro0213/paper-translator"
echo "         /plugin install paper-translator@paper-translator"
