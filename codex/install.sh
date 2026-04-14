#!/usr/bin/env bash
# Paper Translator — Codex installer
#
# Modes:
#   project  Copy AGENTS.md into the current working directory (project-scoped)
#   global   Add instruction file to ~/.codex/config.toml (user-wide)
#
# Also writes a .env snippet exporting PAPER_TRANSLATOR_ROOT.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
AGENTS_SRC="${SCRIPT_DIR}/AGENTS.md"

MODE="${1:-}"
if [ -z "${MODE}" ]; then
  echo "Paper Translator (Codex) — install mode?"
  echo "  [1] project  — copy AGENTS.md into $(pwd)"
  echo "  [2] global   — register with ~/.codex/config.toml"
  read -r -p "choose [1/2]: " choice
  case "${choice}" in
    1|project) MODE=project ;;
    2|global)  MODE=global ;;
    *) echo "[abort] unknown choice: ${choice}"; exit 2 ;;
  esac
fi

echo "[install] source root   : ${ROOT_DIR}"
echo "[install] AGENTS.md from: ${AGENTS_SRC}"
echo "[install] mode          : ${MODE}"

install_project() {
  local target="$(pwd)/AGENTS.md"
  if [ -e "${target}" ]; then
    echo "[warn] ${target} already exists"
    read -r -p "  overwrite? [y/N] " ans
    case "${ans}" in
      y|Y|yes|YES) ;;
      *) echo "[abort] keeping existing AGENTS.md"; return 1 ;;
    esac
  fi
  cp "${AGENTS_SRC}" "${target}"
  echo "[ok] copied AGENTS.md -> ${target}"

  local env_file="$(pwd)/.paper-translator.env"
  cat > "${env_file}" <<EOF
# Source this file (or copy exports into your shell rc) before running codex.
export PAPER_TRANSLATOR_ROOT="${ROOT_DIR}"
export PYTHONIOENCODING=utf-8
EOF
  echo "[ok] wrote env snippet -> ${env_file}"
  echo
  echo "[next] activate env in this shell:"
  echo "        source \"${env_file}\""
  echo "       then run codex and say: 'translate <path-to-pdf>'"
}

install_global() {
  local codex_dir="${HOME}/.codex"
  local cfg="${codex_dir}/config.toml"
  local instr="${codex_dir}/paper-translator-AGENTS.md"
  mkdir -p "${codex_dir}"

  cp "${AGENTS_SRC}" "${instr}"
  echo "[ok] copied AGENTS.md -> ${instr}"

  local snippet="# --- paper-translator (auto-added) ---
# Additional instructions file loaded globally by Codex.
[[instructions]]
path = \"${instr}\"
# --- /paper-translator ---"

  if [ -f "${cfg}" ] && grep -q "paper-translator (auto-added)" "${cfg}"; then
    echo "[info] already registered in ${cfg}, skipping append"
  else
    printf "\n%s\n" "${snippet}" >> "${cfg}"
    echo "[ok] appended registration to ${cfg}"
  fi

  local shell_rc
  case "${SHELL:-}" in
    *zsh)  shell_rc="${HOME}/.zshrc" ;;
    *bash) shell_rc="${HOME}/.bashrc" ;;
    *)     shell_rc="${HOME}/.profile" ;;
  esac
  local env_line="export PAPER_TRANSLATOR_ROOT=\"${ROOT_DIR}\""
  if [ -f "${shell_rc}" ] && grep -Fq "PAPER_TRANSLATOR_ROOT" "${shell_rc}"; then
    echo "[info] PAPER_TRANSLATOR_ROOT already present in ${shell_rc}"
  else
    printf "\n# paper-translator\n%s\nexport PYTHONIOENCODING=utf-8\n" \
      "${env_line}" >> "${shell_rc}"
    echo "[ok] appended env vars to ${shell_rc}"
  fi

  echo
  echo "[next] reload your shell or run:"
  echo "        ${env_line}"
  echo "        export PYTHONIOENCODING=utf-8"
}

case "${MODE}" in
  project) install_project ;;
  global)  install_global ;;
  *) echo "[error] unknown mode: ${MODE} (use 'project' or 'global')"; exit 2 ;;
esac

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
command -v pandoc   >/dev/null 2>&1 && echo "  ✓ pandoc"   || echo "  ○ pandoc   (optional, fallback exists)"
command -v lualatex >/dev/null 2>&1 && echo "  ✓ lualatex" || echo "  ○ lualatex (optional, only for PDF output)"
command -v code     >/dev/null 2>&1 && echo "  ✓ code"     || echo "  ○ code     (optional, for VSCode preview)"

echo
echo "[done] Paper Translator (Codex) installed."
