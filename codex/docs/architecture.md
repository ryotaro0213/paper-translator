# アーキテクチャ（Codex 版）

基本的な設計は Claude Code 版と完全に同一です。スクリプト（`scripts/` 配下）は共有されています。差分は **エントリポイント** のみ。

## 全体像

```
┌─────────────────────────────────────────────────────────────┐
│            Codex (OpenAI CLI)                                │
│            "translate paper.pdf"                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ reads
                           ▼
┌─────────────────────────────────────────────────────────────┐
│        AGENTS.md (project or ~/.codex/)                      │
│        — pipeline orchestration steps                        │
└──────────────────────────┬──────────────────────────────────┘
                           │ invokes
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│  Python      │  │  Codex       │  │  User Q&A        │
│  scripts/    │  │  (翻訳本体)  │  │  (閲覧選択など)  │
│  (共有)      │  │              │  │                  │
└──────────────┘  └──────────────┘  └──────────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│           .paper-translator/outputs/<slug>/                  │
└─────────────────────────────────────────────────────────────┘
```

## 共通スクリプト（`scripts/`）

Claude Code 版と全く同じものを使用:

| スクリプト | 役割 |
|---|---|
| `extract.py` | PDF から図・テキスト・ページレンダーを取得 |
| `plan_figures.py` | bbox から reading-order を計算 |
| `compose_figures.py` | Figure / Table を原PDFから領域切り出し |
| `apply_composed.py` | 個別パネル参照を合成画像に集約 |
| `validate_figures.py` | C1–C10 の配置検証 |
| `to_html.py` | 単一HTML 生成（pandoc フォールバック） |
| `view.sh` | 閲覧方法ディスパッチ |
| `paper.css` | HTML スタイル |

詳細は [../../docs/architecture.md](../../docs/architecture.md) を参照。

## Codex 固有の部分

### AGENTS.md の読み込み

Codex は以下の順序で指示ファイルを探します:

1. 現在のディレクトリの `AGENTS.md`
2. 親ディレクトリを順次遡って `AGENTS.md` を探す
3. `~/.codex/config.toml` の `[[instructions]]` で指定された追加ファイル

`codex/install.sh project` はこの `1` を、`codex/install.sh global` は `3` を利用します。

### スクリプトへのパス解決

Claude Code 版は `${CLAUDE_PLUGIN_ROOT}` を使いますが、Codex では環境変数 `$PAPER_TRANSLATOR_ROOT` を使用します。インストーラが shell rc または `.paper-translator.env` に設定します。

### ユーザーへの質問

Claude Code の `AskUserQuestion` に相当する Codex 固有 UI は無いため、AGENTS.md では **通常のプロンプト質問** として記述しています。Codex は自然に質問 → ユーザー回答を待つ → 次のステップへ進むという流れで処理します。

## データフロー（Claude Code 版と同じ）

```
原PDF
  │
  ├─→ extract.py            → extracted_text.md
  │                            figures_index.json
  │                            figures/fig-NN.png
  │                            figures/page-NNN.png
  │
  ├─→ plan_figures.py       → figure_plan.json
  │
  ├─→ compose_figures.py    → figures/figure-NN.png
  │                            figures/table-NN.png
  │                            figures_composed.json
  │
  ├─→ Codex (翻訳)          → translated.md
  │
  ├─→ validate_figures.py   → figure_validation.md
  │                            exit 0 / 1 / 2
  │
  ├─→ Codex (review)        → review.md
  │
  └─→ view.sh (html/vscode/pdf)
        └─→ to_html.py       → translated.html
```

## 拡張ポイント

Claude Code 版と同じで、`scripts/` 側を拡張すれば両方のエントリから利用できます:

- **OCR 対応**: `extract.py` に `pytesseract` を統合
- **別言語**: AGENTS.md（Codex 版）と `commands/translate-paper.md`（Claude Code 版）の翻訳ルール節を書き換える
- **キャプション原文取り込み**: `compose_figures.py` で caption 全文を JSON に格納し、両エントリで参照

ただし、Claude Code / Codex 固有の挙動（`AskUserQuestion` vs 自然質問、env var 名など）はそれぞれ個別にメンテが必要です。
