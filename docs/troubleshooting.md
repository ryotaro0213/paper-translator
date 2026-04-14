# トラブルシューティング

## インストール系

### `pip install pymupdf` が失敗する
- Python のバージョンを確認: `python --version`（3.10 以上必要）
- 古い `pip` を更新: `python -m pip install --upgrade pip`
- Windows で wheels ビルドエラーが出る場合: `pip install --prefer-binary pymupdf`

### `code` コマンドが見つからない（VSCode 閲覧が失敗）
- VSCode を開き `Ctrl+Shift+P` → `Shell Command: Install 'code' command in PATH`

### pandoc が見つからない
- 自動で Python フォールバック (`to_html.py`) に切り替わるので実害なし
- 高品質な HTML が欲しい場合は `winget install pandoc` / `brew install pandoc`

## 翻訳系

### `UnicodeEncodeError: 'cp932' codec can't encode character`
Windows の Python が日本語を扱えていません。

```bash
PYTHONIOENCODING=utf-8 python script.py
```

`/translate-paper` 内のスクリプト呼び出しは既に付与されていますが、手動で実行する時は必ず指定してください。

### 論文が 40 ページ超で context が足りない
大規模論文は章単位で分割翻訳されます。途中で中断された場合:
1. `translated.md` に既に訳された章を確認
2. Claude に「続きから翻訳して」と伝える
3. `translated.md` に追記されていく

### 用語の訳が気に入らない
1. `review.md` の用語対訳表を確認
2. 希望する訳語を Claude に伝える（例:「`embedding` は『ベクトル表現』じゃなく『埋め込み』にして」）
3. `translated.md` を Claude に一括置換してもらう

## 図の抽出・配置系

### 図が抽出されない（fig-NN.png が生成されない）
- ベクター図の可能性。`page-NNN.png` を確認
- `compose_figures.py` が原PDFから直接切り出すので、このケースでも `figure-NN.png` は正常生成される

### 図の順序が原論文と違う
`validate_figures.py` で検出されるはず（C10）。それでも疑いがある場合:
```bash
PYTHONIOENCODING=utf-8 python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_figures.py" <out_dir>
```
→ `figure_validation.md` に不一致レポートが出ます。

### サブパネルが抜けている
C8 警告で検出されます。`plan_figures.py` の page-dominant 帰属で解決しない場合:
- `figures_index.json` を手動確認
- 翻訳の当該 Figure ブロックに画像を追加

### 合成画像 (figure-NN.png) のクロップが小さすぎる / 大きすぎる
`compose_figures.py` の `pad = 6` を調整。または:
- 小さすぎる: `pad = 12` に増やす
- 大きすぎる（隣の Figure を含む）: キャプション検出が失敗している可能性。`find_caption_bbox` のパターンを確認

### Table が合成されない
- 「Table N.」という見出し行が `extracted_text.md` から検出できない可能性
- `compose_figures.py` の `find_table_header_bbox` でパターン調整
- または個別パネル参照のまま残して OK（検証を通れば問題なし）

## HTML / PDF 出力系

### HTML が巨大（100MB 超）
- 原PDFに高解像度画像が多い可能性
- `compose_figures.py` の `dpi=180` を `dpi=120` に下げる
- または、個別パネル(`fig-NN.png`)を削除して composed のみ残す

### PDF 出力で日本語が□になる
- LaTeX の日本語フォントが未導入
- MiKTeX: `initexmf --admin --update-fndb` 後に `lualatex` で `Yu Gothic` を使う
- または pandoc 引数で `-V CJKmainfont="Noto Sans JP"` を試す

### ブラウザで図が表示されない
- `translated.html` が `--embed-resources` モードで生成されているか確認
- `to_html.py` は常に base64 埋め込みなので問題ないはず

## 検証系

### validator が exit 2 で毎回失敗する
1. `figure_validation.md` を読む
2. エラーカテゴリ（C1–C10）を確認
3. `translated.md` を修正:
   - C1/C5/C10: 画像の追加・並び替え
   - C9: alt-text を正しい Figure 番号に修正
4. 再実行: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_figures.py" <out_dir>`

### 警告だけでも続行したい
翻訳 Claude 側で `AskUserQuestion` が出るので「警告を受け入れて続行」を選択。あるいは `validate_figures.py` を手動実行し、内容を確認してから手で修正。

## その他

### 出力先を変えたい
スラッシュコマンド内で `OUT=".paper-translator/outputs/<slug>"` としています。変更したい場合は `plugins/paper-translator/commands/translate-paper.md` を編集するか、Claude に「出力先は `~/Documents/papers/` にして」と指示。

### 既存の翻訳を別プロジェクトに持っていきたい
`.paper-translator/outputs/<slug>/` 一式をコピーすれば OK。`original.pdf` と `figures/` が相対パス参照なので移動後も機能します。
