#!/usr/bin/env bash
# Paper Translator — installer
# Copies/links the plugin into ~/.claude/plugins/paper-translator and
# verifies Python dependencies.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_NAME="paper-translator"

if [ -n "${CLAUDE_HOME:-}" ]; then
  TARGET_BASE="${CLAUDE_HOME}/plugins"
else
  TARGET_BASE="${HOME}/.claude/plugins"
fi
TARGET="${TARGET_BASE}/${PLUGIN_NAME}"

echo "[install] Paper Translator plugin"
echo "  source: ${SCRIPT_DIR}"
echo "  target: ${TARGET}"

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
  copy)    cp -r "${SCRIPT_DIR}" "${TARGET}" ;;
  link)    ln -s "${SCRIPT_DIR}" "${TARGET}" ;;
  *) echo "[error] unknown mode: ${MODE} (use 'copy' or 'link')"; exit 2 ;;
esac
echo "[ok] installed (${MODE})"

echo
echo "[check] Python dependencies"
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" \
  || { echo "[error] Python 3.10+ required"; exit 3; }
echo "  Python: $(python --version)"

MISSING=()
for pkg in fitz markdown pymdownx; do
  if python -c "import ${pkg}" 2>/dev/null; then
    echo "  ✓ ${pkg}"
  else
    echo "  ✗ ${pkg} (missing)"
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
command -v pandoc   >/dev/null 2>&1 && echo "  ✓ pandoc"   || echo "  ○ pandoc (optional, fallback exists)"
command -v lualatex >/dev/null 2>&1 && echo "  ✓ lualatex" || echo "  ○ lualatex (optional, only for PDF output)"
command -v code     >/dev/null 2>&1 && echo "  ✓ code"     || echo "  ○ code (optional, for VSCode preview)"

echo
echo "[done] Paper Translator installed at ${TARGET}"
echo "       Use in Claude Code: /translate-paper <pdf-path>"
