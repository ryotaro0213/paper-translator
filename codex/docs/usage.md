# 使い方（Codex 版）

## 基本

Codex 起動後、自然言語で:

```
translate ./papers/foo.pdf
```

または日本語で:
```
この論文を翻訳して: ./papers/foo.pdf
```

AGENTS.md が読み込まれていれば、Codex は自動で以下のパイプラインに入ります:

1. PDF メタデータを確認 → slug 候補を提示
2. 出力ディレクトリ `.paper-translator/outputs/<slug>/` を作成
3. `extract.py` で図・テキスト抽出
4. ライセンス確認（CC BY / Open Access / その他）
5. `plan_figures.py` + `compose_figures.py` で図の計画と合成画像作成
6. セクション単位で翻訳 → `translated.md` に追記
7. `validate_figures.py` で配置検証（ブロッキング）
8. `review.md` に検証ログ作成
9. 閲覧方法を質問 → HTML / VSCode / PDF から選択

## 長い論文の扱い

30 ページを超える論文は、まず **Abstract + Introduction** のサンプル翻訳を出して確認を求めます。OK なら続きを順次追記します。

## 部分翻訳

```
Section 3 と 4 だけ翻訳して: paper.pdf
```

Codex は `extracted_text.md` を読んで構造把握後、対象章のみ処理します。

## 既存翻訳の修正

```
translated.md の attention を「注意機構」に統一して
```

Codex が `translated.md` を編集 → `to_html.py` で HTML を再生成。

## 用語カスタマイズ

翻訳前に指示:
```
LLM は「大規模言語モデル」じゃなく「LLM」のままにして。あとは通常通り翻訳して。
```

AGENTS.md のルールより個別指示が優先されます（Codex の通常挙動）。

## 閲覧方法の指定

プロンプト内で明示すれば質問をスキップ:
```
translate paper.pdf and open HTML
```

選択肢:
- `open HTML` / `html` → ブラウザで HTML
- `open in VSCode` / `vscode` → VSCode プレビュー
- `PDF` / `pdf` → PDF 生成（pandoc + LaTeX 要）
- `no open` / `just save` → 開かずにパスだけ表示

## 複数論文のバッチ

```
translate the following papers in order:
- ./papers/a.pdf
- ./papers/b.pdf
- ./papers/c.pdf
```

論文ごとに `.paper-translator/outputs/<slug>/` が別フォルダで作られます。

## 出力ファイル一覧

| ファイル | 用途 |
|---|---|
| `translated.md` | 日本語訳（主成果物） |
| `translated.html` | 単一HTML（図 base64 埋め込み、配布可） |
| `translated.pdf` | PDF を選んだ場合 |
| `review.md` | 翻訳検証ログ（用語・数値確認） |
| `figure_validation.md` | 配置検証レポート |
| `figure_plan.json` | 図の挿入計画 |
| `figures_composed.json` | 合成画像情報 |
| `figures_index.json` | 個別パネル情報 |
| `extracted_text.md` | 抽出原文（参考） |
| `original.pdf` | 原PDF コピー |
| `figures/figure-NN.png` | Figure 単位の合成画像（主に参照） |
| `figures/table-NN.png` | Table 単位の合成画像 |
| `figures/fig-NN.png` | 個別パネル（フォールバック・検証） |
| `figures/page-NNN.png` | ページ全体レンダー（視覚検証） |

## 再翻訳時の注意

既存の `translated.md` がある場合、Codex は確認を取ります:

- **追記**: 新しい章だけ足す
- **別バージョン作成**: `translated.v2.md` として保存
- **上書き**: 破壊的なので基本選ばない

## 配布

誰かに渡すのは `translated.html` 単体で OK です（図・CSS・目次がすべて内包されています）。

## トラブル時

- 図の位置がおかしい → `figure_validation.md` を読む、`page-NNN.png` を目視
- 用語・訳が気に入らない → Codex に個別指示して再生成
- パイプラインが途中で止まった → `.paper-translator/outputs/<slug>/` は残るので続きから再開できる

詳細: [../../docs/troubleshooting.md](../../docs/troubleshooting.md)
