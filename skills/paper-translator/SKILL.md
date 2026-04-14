---
name: paper-translator
description: Translate English research papers (PDF) into Japanese while preserving the original figure and table layout. Triggered when the user provides a PDF path and asks to translate it, or says things like "この論文翻訳して" / "論文を日本語訳して" / "translate this paper".
---

# Paper Translator Skill

## いつ使うか

- ユーザーが `.pdf` ファイルを指して「翻訳して」「日本語訳して」と言った場合
- `/translate-paper <path>` スラッシュコマンドが呼ばれた場合
- 英語論文の日本語版を作りたいと相談された場合

## 主要成果物

1 論文あたり以下を生成:

```
<out_dir>/
├── original.pdf          # 原PDF のコピー
├── translated.md         # 日本語訳（図は合成画像で参照）
├── translated.html       # 単一HTML（図を base64 埋め込み、配布可能）
├── review.md             # 翻訳検証ログ
├── figure_plan.json      # 図の挿入計画（reading-order 整列済み）
├── figure_validation.md  # 配置検証レポート
├── figures_composed.json # 合成画像の情報
├── extracted_text.md     # 抽出生テキスト（参考）
├── figures_index.json    # 個別パネルのメタデータ
└── figures/
    ├── figure-NN.png     # Figure N 単位の合成画像（主に参照）
    ├── table-NN.png      # Table N 単位の合成画像
    ├── fig-NN.png        # 個別パネル（検証・フォールバック用）
    └── page-NNN.png      # ページ全体レンダー（視覚確認用）
```

## ワークフロー

`commands/translate-paper.md` に詳細があるが、要点は以下:

1. **抽出**: `scripts/extract.py` で PyMuPDF により図・テキストを取得
2. **計画**: `scripts/plan_figures.py` で bbox から reading-order を計算
3. **合成**: `scripts/compose_figures.py` で **各 Figure/Table を原PDFページから領域切り出しして 1 枚の PNG に**する（レイアウトを pixel-perfect 保持）
4. **翻訳**: セクション単位で `translated.md` に追記。各図は単一の合成画像で参照
5. **検証**: `scripts/validate_figures.py` で C1–C10 の 10 項目を自動チェック
6. **閲覧**: HTML / VSCode / PDF をユーザに選ばせる

## 翻訳の品質ルール

- 固有名詞・モデル名・ソフトウェア名・関数名 → 原語保持
- 専門用語 → 初出時「訳語 (English)」、以降は訳語のみ
- 数値・数式・SI 単位 → 原文保持、数式は LaTeX
- 図 / 表 参照 → 「図 N」「表 N」に統一、初出時に原文併記
- References リスト → 原則未訳（本文中の `[N]` 引用は保持）

## 図の捕捉方針（重要）

個別パネル抽出だけでは原論文のレイアウト（矢印・配置比率・サブパネル間隔）が失われる問題があるため、**Figure / Table 単位で原PDFページから切り出した合成画像を主要な参照とする**。これにより:

- CSS/HTML 側でのレイアウト再現が不要になる
- サブパネルを接続する矢印・線・注釈がそのまま保持される
- 1 Figure = 1 画像となり、Markdown が単純化される

## ライセンス配慮

対象論文のライセンスを `extracted_text.md` の冒頭（著作権表記部分）から確認する:

- **CC BY / CC0 / Open Access / MDPI** → 翻訳・再配布可（帰属明記のみ）
- **商用・購読誌** → 個人利用の範囲に留まるようユーザに確認

翻訳文末尾に原典 DOI とライセンス表記を必ず残す。

## Python パッケージ要件

- `pymupdf >= 1.24` (`fitz`)
- `markdown >= 3.5`（`to_html.py` フォールバック用）
- `pymdown-extensions >= 10`（目次・コード表示強化）

オプション:
- `pandoc`（HTML/PDF 変換が高品質）
- `lualatex`（PDF 出力）

## Windows での注意

- Python 実行時に `PYTHONIOENCODING=utf-8` を必ず設定（cp932 で UnicodeEncodeError を起こすため）
- パスは `C:/Users/...` または `C:\\Users\\...`
- Bash (Git Bash/WSL) 上では Unix 形式パスが使える

## 参考

詳細手順: `../commands/translate-paper.md`
アーキテクチャ: `../docs/architecture.md`
トラブルシュート: `../docs/troubleshooting.md`
