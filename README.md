# Paper Translator

英語論文 PDF を、**図と表のレイアウトを保持したまま**日本語訳する Claude Code プラグイン。

「ChatGPT で文字翻訳はできるけど、図と一緒に日本語で読みたい」というニーズに応えます。

## 何ができるか

- PDF → 日本語訳 Markdown / HTML / PDF
- **原論文の Figure・Table のレイアウトを pixel-perfect で保持**
- 1 Figure = 1 合成画像（矢印・サブパネル間隔・キャプションも含めて原PDF領域を直接レンダリング）
- 翻訳完了後の図配置を 10 項目で自動検証（C1–C10）
- 閲覧方法を選択: HTML（ブラウザ）/ VSCode プレビュー / PDF

## デモ

入力: 44 ページの英語論文 PDF
出力（抜粋）:

```
.paper-translator/outputs/<slug>/
├── translated.md           # 日本語訳 (Markdown)
├── translated.html         # 単一HTML（図 base64 埋め込み、配布可）
├── review.md               # 翻訳検証ログ
├── figure_validation.md    # 配置検証レポート
├── original.pdf            # 原PDF
└── figures/
    ├── figure-01.png 〜 figure-NN.png   # Figure 単位の合成画像
    ├── table-NN.png                     # Table 単位の合成画像
    ├── fig-NN.png (個別パネル、検証用)
    └── page-NNN.png (ページ全体レンダー)
```

## クイックスタート

### 1. 依存関係をインストール

```bash
pip install pymupdf markdown pymdown-extensions
```

オプション（HTML/PDF 出力を高品質化）:
```bash
# Windows
winget install pandoc
# macOS
brew install pandoc

# PDF 出力するなら LaTeX も
# Windows: choco install miktex
# macOS:   brew install --cask mactex
```

### 2. プラグインをインストール

#### 方法 A: Claude Code Plugin マーケット経由（将来）

```
/plugin install paper-translator
```

#### 方法 B: ローカルディレクトリ配置

```bash
git clone https://github.com/ryotaro0213/paper-translator.git \
  ~/.claude/plugins/paper-translator
```

#### 方法 C: 手動コピー

このリポジトリの `plugins/paper-translator/` を `~/.claude/plugins/` にコピーする。

### 3. 使う

Claude Code 内で:

```
/translate-paper path/to/your-paper.pdf
```

または自然言語で:

```
この論文を翻訳して: ./papers/foo.pdf
```

完了後、閲覧方法を選択するダイアログが出ます（HTML / VSCode / PDF / 開かない）。

## ワークフロー

```
PDF 入力
  ↓
[1] extract.py        — 図・テキスト・ページレンダーを抽出
  ↓
[2] plan_figures.py   — bbox から reading-order を計算
  ↓
[3] compose_figures.py — Figure/Table を原PDFから領域切り出し
  ↓
[4] Claude 翻訳        — セクション単位で日本語訳
  ↓
[5] validate_figures.py — C1–C10 で配置を自動検証
  ↓
[6] to_html.py        — 単一HTMLを生成（pandoc 不要）
  ↓
閲覧方法を選択 → HTML / VSCode / PDF
```

## 配置検証チェック (C1–C10)

| ID | 内容 | エラー / 警告 |
|---|---|---|
| C1 | Figure N が抜けていないか | エラー |
| C2 | 出現順が原文と一致するか | エラー |
| C3 | 図の近くに「図 N」参照があるか | 警告 |
| C4 | 同じ画像の重複使用 | エラー |
| C5 | サブ図が連続配置されているか | エラー |
| C6 | 「図 N」参照に画像があるか | 情報 |
| C7 | 未知画像の使用 | エラー |
| C8 | 未使用画像（多パネル抜け検出） | 警告 |
| C9 | alt-text と plan の Figure 番号一致 | エラー |
| C10 | サブパネル順序が plan と一致 | エラー |

## ドキュメント

- [使い方詳細](docs/usage.md)
- [アーキテクチャ](docs/architecture.md)
- [トラブルシューティング](docs/troubleshooting.md)
- [インストール詳細](docs/installation.md)

## 動作要件

- Claude Code (latest)
- Python 3.10+
- PyMuPDF 1.24+
- 任意: pandoc, LaTeX

## ライセンス対応

対象論文のライセンスを冒頭から自動検出:

- **CC BY / CC0 / Open Access / MDPI** → 翻訳・再配布可（帰属明記のみ）
- **商用・購読制** → 個人利用の範囲を確認

翻訳文末尾に原典 DOI とライセンス表記を残します。

## ライセンス

MIT License — 詳細は [LICENSE](LICENSE) 参照。

## 貢献

Issues / PRs 歓迎。
