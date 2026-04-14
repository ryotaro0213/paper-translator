# 使い方

## 基本

Claude Code 内で:
```
/translate-paper path/to/paper.pdf
```

または自然言語:
```
この論文を翻訳して: ./foo.pdf
```

## 処理の流れ

Claude が自動で以下を実行します:

1. PDF メタデータを読み、slug 候補を提示 → ユーザー確認
2. 出力フォルダ `.paper-translator/outputs/<slug>/` を作成、原PDFをコピー
3. `extract.py` で図・テキスト・ページレンダーを抽出
4. ライセンスを確認（冒頭の copyright 表記から）
5. `plan_figures.py` で図の挿入計画を生成
6. `compose_figures.py` で各 Figure/Table を原PDFページから切り出し
7. セクション単位で翻訳 → `translated.md` に追記
8. `validate_figures.py` で配置を 10 項目検証
9. `review.md` に検証ログを作成
10. 閲覧方法を `AskUserQuestion` で選択
11. 選んだ方法で開く（HTML / VSCode / PDF）

## 大規模論文（30 ページ超）の扱い

Claude は最初に **Abstract + Introduction** だけ訳してユーザーに品質確認を求めます。OK なら続く章を順次追記します。途中で止めたければ「ここまででよい」と伝えれば OK。

## 部分翻訳

特定章だけ訳したい場合:
```
Section 3 と Section 4 だけ translate-paper で訳して: paper.pdf
```

Claude は構造把握後、対象章のみ処理します。

## 再翻訳・差し替え

既存の `translated.md` があると Claude は確認を求めます:
- 追記（`## 3. 新しいセクション` を足す）
- 上書きではなく `translated.v2.md` に別保存

## 閲覧方法の選択肢

### HTML（推奨）
- 単一ファイル、図を base64 埋め込み
- そのままブラウザで開く・配布できる
- pandoc があれば高品質、なくても Python フォールバック (`to_html.py`) で動く

### VSCode プレビュー
- `code translated.md` で開き、`Ctrl+Shift+V` でプレビュー
- 翻訳を手直ししたいときに便利

### PDF
- pandoc + LaTeX が必要
- 無い環境では HTML 生成後に「ブラウザで PDF 保存」を案内

### 開かない
- 出力パスだけ教えてもらって後で自分で開く

## 出力ファイル

| ファイル | 用途 |
|---|---|
| `translated.md` | 日本語訳（図は合成画像で参照）。編集可能な原本 |
| `translated.html` | 単一HTML。誰かに渡したり別環境で閲覧 |
| `translated.pdf` | PDF 出力を選んだ場合 |
| `review.md` | 翻訳品質の検証ログ。用語対訳表・数値確認 |
| `figure_validation.md` | 配置検証レポート |
| `figure_plan.json` | 図の挿入計画（reading-order 整列済み） |
| `figures_composed.json` | 合成画像情報 |
| `figures_index.json` | 個別パネルのメタデータ |
| `extracted_text.md` | 抽出原文テキスト（参考用） |
| `original.pdf` | 原PDF コピー |
| `figures/figure-NN.png` | Figure 単位の合成画像（主な参照） |
| `figures/table-NN.png` | Table 単位の合成画像 |
| `figures/fig-NN.png` | 個別パネル（検証・フォールバック用） |
| `figures/page-NNN.png` | 各ページ全体レンダー（視覚確認用） |

## トラブル時

- 図の位置がおかしい → `figure_validation.md` を確認、`page-NNN.png` を目視
- 用語が気に入らない → `review.md` の用語対訳表を編集、Claude に「〜はこう訳して」と指示
- 翻訳の一部を直したい → VSCode で `translated.md` を直接編集し、`view.sh html` で再生成

詳細: [troubleshooting.md](troubleshooting.md)
