---
description: 英語論文 PDF を、図と表のレイアウトを保持したまま日本語訳し、VSCode/HTML/PDF で閲覧
argument-hint: <PDFパス>
---

# 論文翻訳（図保持）ワークフロー

引数で渡された英語論文 PDF (`$ARGUMENTS`) を、原論文のページレイアウトを保持したまま日本語訳し、完了後にユーザーが閲覧方法を選択できるようにする。

スクリプトは plugin の `scripts/` ディレクトリにある。`${CLAUDE_PLUGIN_ROOT}/scripts/` で参照する。

## 前提チェック

最初に以下を確認:
1. `$ARGUMENTS` が空でないこと（空なら使い方を表示して終了）
2. PDF が存在すること（`ls` で確認）
3. Python と PyMuPDF が利用可能か（`python -c "import fitz"`）
   - 未導入なら `pip install pymupdf markdown pymdown-extensions` を案内して中断

## 出力先

ユーザーのプロジェクト直下に作る:
```
.paper-translator/outputs/<slug>/
```

`<slug>` は `著者姓-年-短縮タイトル` 形式（kebab-case）。AskUserQuestion で確認してから決定する。

## ステップ 1: メタ情報取得と slug 決定

```bash
PYTHONIOENCODING=utf-8 python -c "
import fitz, sys
doc = fitz.open(sys.argv[1])
print(doc.metadata.get('title',''))
print(doc.metadata.get('author','')[:80])
print(doc.page_count)
" "$ARGUMENTS"
```

slug 候補を 1–3 個提示し `AskUserQuestion` で選ばせる（カスタム入力も許可）。

## ステップ 2: 出力フォルダ作成

```bash
OUT=".paper-translator/outputs/<slug>"
mkdir -p "$OUT/figures"
cp "$ARGUMENTS" "$OUT/original.pdf"
```

## ステップ 3: 図・テキスト抽出

```bash
PYTHONIOENCODING=utf-8 python "${CLAUDE_PLUGIN_ROOT}/scripts/extract.py" \
  "$ARGUMENTS" "$OUT"
```

## ステップ 4: ライセンス確認

`extracted_text.md` の冒頭を読み:
- CC BY / CC0 / Open Access / MDPI → 翻訳・再配布 OK
- それ以外（商用・購読制） → ユーザに個人利用の範囲であることを確認

## ステップ 5: 図の挿入計画と Figure 単位の合成画像を作成（必須）

```bash
PYTHONIOENCODING=utf-8 python "${CLAUDE_PLUGIN_ROOT}/scripts/plan_figures.py" "$OUT"
PYTHONIOENCODING=utf-8 python "${CLAUDE_PLUGIN_ROOT}/scripts/compose_figures.py" "$OUT"
```

`plan_figures.py` → `figure_plan.json`（reading-order に整列されたサブパネル一覧 + anchor_text）
`compose_figures.py` → `figures/figure-NN.png` と `table-NN.png`（各 Figure/Table を原PDFページから領域切り出ししてレンダリング）

## ステップ 6: 構造把握

`extracted_text.md` を読み、セクション見出しを特定。長大な論文（30 ページ超）は最初に Abstract + Introduction のサンプル翻訳を出してユーザに確認。

## ステップ 7: セクション単位で翻訳

`translated.md` にセクション単位で追記する。**翻訳ルール**:

- **固有名詞・モデル名・データセット名・ソフトウェア名・関数名**: 原語保持
- **専門用語**: 初出時「日本語訳 (English)」、以降は日本語
- **数値・数式・単位・SI 表記**: そのまま保持（数式は LaTeX `$$...$$` 可）
- **Figure N / Table N の参照**: 「図 N」「表 N」に統一、初出時に原文併記
- **図の埋め込み**: `figure_plan.json` の `anchor_text` に対応する段落直後に
  ```markdown
  ![Figure N. キャプション](figures/figure-NN.png)
  ```
  を 1 行で挿入。**個別パネル `fig-NN.png` は使わない**（合成画像の方がレイアウトを保持する）
- **References セクション**: 原則として未訳。本文中の `[N]` 引用は保持

## ステップ 7.5: 図配置を正規化（必須・検証前に必ず実行）

翻訳が一段落したら、検証の**前に**必ず以下を実行する:

```bash
PYTHONIOENCODING=utf-8 python "${CLAUDE_PLUGIN_ROOT}/scripts/apply_composed.py" "$OUT"
PYTHONIOENCODING=utf-8 python "${CLAUDE_PLUGIN_ROOT}/scripts/append_missing_composed_figures.py" "$OUT"
```

`apply_composed.py` の役割:
- 既存の composed 画像参照を一度除去してから再配置（冪等・再実行で同結果）
- 残存する個別パネル (`fig-NN.png`) の連続ブロックを合成画像 (`figure-NN.png`) 1 行に集約
- 本文中で `図 N` / `Figure N` が最初に現れる段落の直後に、対応する合成画像を挿入
- 本文に参照が無い図は `## 図版一覧（自動補完）` セクションへ末尾にまとめて配置
- `$OUT/figure_placement.json` が存在すれば、そこで指定された見出し直後への明示ピン留めを優先

`append_missing_composed_figures.py` は安全網:
- `apply_composed.py` 実行後に translated.md を走査し
- `figures/figure-NN.png` / `figures/table-NN.png` のうち本文にまだ登場しないものを検出
- 欠落があれば `## 図版一覧（自動補完）` セクションへ追記（重複なし）

### 手動ピン留め (`figure_placement.json`, 任意)

明示的に「Figure 3 は `## 3.2 手法` 直後に置く」と固定したい場合:

```json
{
  "3": {"after_heading": "## 3.2 手法"},
  "7": {"after_heading": "### 実験結果"}
}
```

このファイルが `$OUT/figure_placement.json` にあれば、`apply_composed.py` は本文参照よりもそちらを優先する。

## ステップ 8: 図配置の自動検証（必須・ブロッキング）

ステップ 7.5 の実行後にのみ、この検証を走らせる:

```bash
PYTHONIOENCODING=utf-8 python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_figures.py" "$OUT"
```

検証項目:
- C1 カバレッジ / C2 順序 / C3 キャプション一致 / C4 重複 / C5 サブ図クラスタリング
- C6 孤立参照 / C7 未知画像 / C8 未使用画像 / C9 alt-text と plan の Figure 番号一致
- C10 サブパネル順序

終了コード:
- `0` クリーン → 次へ
- `1` 警告のみ → 警告内容を提示し続行可否を `AskUserQuestion`
- `2` エラー → translated.md を修正してステップ 7.5 から再実行

修正時、疑わしい箇所は `figures/page-NNN.png`（全ページレンダー）を `Read` で視覚確認する。

## ステップ 9: 検証ログ作成

`$OUT/review.md` に以下を記録:
- 翻訳済みセクション一覧
- 用語対訳表（この論文固有）
- 数値・固有名詞の保持確認
- 残課題

## ステップ 10: 閲覧方法の選択

`AskUserQuestion` で選ばせる:

1. **HTML（ブラウザ）** ← 推奨。図込み単一ファイル
2. **VSCode プレビュー** ← 編集もしやすい
3. **PDF** ← 印刷・配布向け
4. **開かない**

選ばれた方法に応じてヘルパを呼ぶ:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/view.sh" "$OUT" html      # or vscode | pdf
```

`view.sh` は内部で:
- HTML: pandoc → 無ければ Python (`to_html.py`) フォールバック
- PDF: pandoc + lualatex → 無ければ HTML 経由を案内
- VSCode: `code` コマンドで開く

## ステップ 11: 完了報告

- 出力フォルダのパス
- 翻訳セクション数 / 図数 / 表数
- 検証結果サマリ
- 閲覧で開いたファイル

## エラーハンドリング

| 症状 | 対処 |
|------|------|
| PDF が読めない | スキャン PDF の可能性。OCR (`pytesseract`) の導入を案内 |
| 図が抽出できない | ベクター図の可能性。`page-NNN.png` から領域切り出しを提案 |
| 文字化け（cp932 系） | `PYTHONIOENCODING=utf-8` を必ず指定する |
| context 圧迫 | 章単位で分割翻訳。`translated.md` への追記方式を維持 |
| pandoc 未導入 | `to_html.py` フォールバックで HTML 生成 |
| LaTeX 未導入 | HTML 生成して「ブラウザの印刷→PDF で保存」を案内 |

## 注意事項

- 既存の `translated.md` がある場合は確認してから追記または `translated.v2.md` を作成
- 既存ファイルは上書きしない（追記のみ）
- 大規模論文は最初に Abstract + Introduction のサンプル翻訳で品質確認を取ってから続行
