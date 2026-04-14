# アーキテクチャ

## 全体像

```
┌─────────────────────────────────────────────────────────────┐
│                  /translate-paper <PDF>                      │
│                  (slash command, Claude が解釈)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│  Python      │  │  Claude      │  │  AskUserQuestion │
│  scripts     │  │  (翻訳本体)  │  │  (閲覧選択)      │
└──────────────┘  └──────────────┘  └──────────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│             .paper-translator/outputs/<slug>/               │
└─────────────────────────────────────────────────────────────┘
```

## モジュール分担

| モジュール | 言語 | 役割 |
|---|---|---|
| `plugins/paper-translator/commands/translate-paper.md` | Markdown (Claude 命令) | 全体オーケストレーション |
| `plugins/paper-translator/skills/paper-translator/SKILL.md` | Markdown (Claude 命令) | 自然言語トリガと方針 |
| `plugins/paper-translator/scripts/extract.py` | Python | PyMuPDF で PDF→図・テキスト・ページ画像 |
| `plugins/paper-translator/scripts/plan_figures.py` | Python | bbox から reading-order を計算、anchor_text 付与 |
| `plugins/paper-translator/scripts/compose_figures.py` | Python | 各 Figure/Table を原PDFページから領域切り出し |
| `plugins/paper-translator/scripts/apply_composed.py` | Python | 個別パネル参照を合成画像参照に集約 |
| `plugins/paper-translator/scripts/validate_figures.py` | Python | C1–C10 の配置検証 |
| `plugins/paper-translator/scripts/to_html.py` | Python | 単一HTML 生成（pandoc フォールバック） |
| `plugins/paper-translator/scripts/view.sh` | Bash | 閲覧方法ディスパッチ |
| `plugins/paper-translator/scripts/paper.css` | CSS | HTML スタイル |

## 設計の核心

### 1. 図の捕捉戦略

**個別パネル抽出だけでは原論文のレイアウト情報が失われる**ことが分かった（PDFオブジェクト順≠空間順、矢印・サブパネル間隔も別オブジェクト）。

解決:
1. `extract.py` で **個別パネル + ページ全体レンダー** の両方を保存
2. `plan_figures.py` で bbox から reading-order を再構築し、同一ページの単一 Figure に未キャプション画像を自動帰属（inheritance）
3. `compose_figures.py` で **各 Figure/Table の領域を原PDFから直接切り出して合成画像化**
4. 翻訳時はこの合成画像を 1 図 1 画像で参照する

これにより:
- 矢印・線・配置比率がそのまま保持
- CSS Grid のような複雑な再レイアウトが不要
- HTML サイズも縮小（個別 50 点 → 合成 17 点で 60% 減）

### 2. 配置検証 (C1–C10)

翻訳完了後、`validate_figures.py` が機械的に検査:

| ID | 内容 | レベル |
|---|---|---|
| C1 | Figure N が抜けていないか | エラー |
| C2 | 出現順が原文と一致 | エラー |
| C3 | 「図 N」参照が画像近傍にある | 警告 |
| C4 | 画像の重複使用なし | エラー |
| C5 | サブ図が連続配置 | エラー |
| C6 | 「図 N」参照に対応画像あり | 情報 |
| C7 | 未知画像なし | エラー |
| C8 | 未使用画像なし（多パネル抜け検出） | 警告 |
| C9 | alt-text と plan の Figure 番号一致 | エラー |
| C10 | サブパネル順序が plan と一致 | エラー |

エラー検出時は `/translate-paper` がブロックして翻訳を修正させる。

### 3. プラットフォーム独立性

- すべて Python (cross-platform) と Bash (Git Bash 経由で Windows 動作)
- pandoc / LaTeX は **オプション**（無くても動く）
- `to_html.py` が pandoc 不在時のフォールバック（`markdown` パッケージで HTML 生成、図を base64 で内包）

### 4. ユーザー対話

`AskUserQuestion` を要所で使う:
- slug の確認
- 大規模論文のサンプル翻訳承認
- 検証エラー時の対応選択
- 閲覧方法の選択

## データフロー詳細

```
原PDF
  │
  ├─→ extract.py
  │     ├─→ extracted_text.md      (テキスト、ページ区切り)
  │     ├─→ figures_index.json     (個別パネル: file, page, bbox, caption_hint)
  │     ├─→ figures/fig-NN.png     (個別パネル画像)
  │     └─→ figures/page-NNN.png   (各ページ全体レンダー)
  │
  ├─→ plan_figures.py
  │     └─→ figure_plan.json
  │           ├─ figure_num
  │           ├─ files (reading-order ソート済み)
  │           ├─ inherited_files (page-dominant 帰属)
  │           ├─ page
  │           ├─ caption_hint
  │           └─ anchor_text (原文段落の末尾 160 文字)
  │
  ├─→ compose_figures.py
  │     ├─→ figures/figure-NN.png  (Figure 単位の合成画像)
  │     ├─→ figures/table-NN.png   (Table 単位の合成画像)
  │     └─→ figures_composed.json  (合成情報)
  │
  ├─→ Claude (翻訳)
  │     └─→ translated.md          (日本語訳, 図は figure-NN.png 参照)
  │
  ├─→ validate_figures.py
  │     ├─→ figure_validation.md   (検証レポート)
  │     └─→ exit 0 / 1 / 2
  │
  ├─→ Claude (review.md 作成)
  │     └─→ review.md              (用語表・数値確認)
  │
  └─→ view.sh (HTML / VSCode / PDF)
        └─→ to_html.py (pandoc フォールバック)
              └─→ translated.html  (単一HTML、図 base64)
```

## 拡張ポイント

### 別言語への翻訳
`plugins/paper-translator/skills/paper-translator/SKILL.md` の翻訳ルールを別言語向けに書き換える。スクリプト側は言語非依存。

### OCR 対応（スキャン PDF）
`extract.py` に `pytesseract` を組み込む。

### 図のキャプション原文取り込み
`compose_figures.py` の `find_caption_bbox` を拡張し、キャプション全文を `figures_composed.json` に格納 → 翻訳時にそのまま訳す。

### 別 LMS への配信
`translated.html` を SCORM パッケージに変換するスクリプトを `scripts/` に追加。

### 数式の MathJax レンダリング
`to_html.py` の HTML テンプレートに MathJax CDN を追加し、`$$...$$` を render させる。
