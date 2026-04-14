#!/usr/bin/env bash
# 翻訳済み translated.md を閲覧する。
# 使用: bash view.sh <output_dir> <mode: vscode|html|pdf>
set -euo pipefail

OUT="${1:?output dir required}"
MODE="${2:?mode required: vscode|html|pdf}"
MD="$OUT/translated.md"
CSS="$(dirname "$0")/paper.css"

if [ ! -f "$MD" ]; then
  echo "[error] not found: $MD" >&2
  exit 1
fi

TITLE=$(grep -m1 '^# ' "$MD" | sed 's/^# //')

case "$MODE" in
  vscode)
    if command -v code >/dev/null 2>&1; then
      code "$MD"
      echo "[ok] VSCode で開きました。Ctrl+Shift+V でプレビュー表示可。"
    else
      echo "[warn] 'code' コマンドが見つかりません。VSCode のコマンドパレットで 'Shell Command: Install code command in PATH' を実行してください。"
      exit 2
    fi
    ;;
  html)
    if command -v pandoc >/dev/null 2>&1; then
      CSS_OPT=()
      [ -f "$CSS" ] && CSS_OPT=(--css "$CSS")
      pandoc "$MD" -o "$OUT/translated.html" \
        --standalone --toc --toc-depth=3 --embed-resources \
        --metadata title="$TITLE" "${CSS_OPT[@]}"
    else
      echo "[info] pandoc 未検出。Python フォールバックで HTML を生成します。"
      PYTHONIOENCODING=utf-8 python "$(dirname "$0")/to_html.py" "$OUT"
    fi
    echo "[ok] $OUT/translated.html を生成しました。"
    # Windows/Mac/Linux で既定ブラウザ起動
    if command -v start >/dev/null 2>&1; then start "" "$OUT/translated.html"
    elif command -v open  >/dev/null 2>&1; then open "$OUT/translated.html"
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$OUT/translated.html"
    else echo "[info] 手動でブラウザから開いてください。"
    fi
    ;;
  pdf)
    if ! command -v pandoc >/dev/null 2>&1; then
      echo "[error] pandoc 未導入です。'winget install pandoc' を実行してください。" >&2
      exit 3
    fi
    # lualatex が使えない場合は weasyprint → wkhtmltopdf → HTML 経由フォールバック
    if command -v lualatex >/dev/null 2>&1; then
      pandoc "$MD" -o "$OUT/translated.pdf" \
        --toc --toc-depth=3 \
        --pdf-engine=lualatex \
        -V CJKmainfont="Yu Gothic" -V mainfont="Yu Gothic" \
        -V geometry:margin=2cm \
        --metadata title="$TITLE"
    elif command -v weasyprint >/dev/null 2>&1; then
      pandoc "$MD" -o "$OUT/translated.pdf" \
        --toc --toc-depth=3 --pdf-engine=weasyprint \
        --metadata title="$TITLE"
    else
      echo "[warn] LaTeX/weasyprint が見つかりません。HTMLを生成してブラウザで「PDFとして保存」してください。" >&2
      bash "$0" "$OUT" html
      exit 0
    fi
    echo "[ok] $OUT/translated.pdf を生成しました。"
    if command -v start >/dev/null 2>&1; then start "" "$OUT/translated.pdf"
    elif command -v open  >/dev/null 2>&1; then open "$OUT/translated.pdf"
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$OUT/translated.pdf"
    fi
    ;;
  *)
    echo "[error] unknown mode: $MODE (use vscode|html|pdf)" >&2
    exit 1
    ;;
esac
