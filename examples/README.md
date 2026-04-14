# 使用例

## 例 1: MDPI Open Access 論文

```
/translate-paper papers/electronics-15-01294.pdf
```

結果（44 ページ論文、約 2 分）:
- Figure 16 点、Table 1 点（合成画像化）
- 翻訳セクション: Abstract + 1〜6（全章）
- References は原語保持
- `translated.html` 約 14MB（図 base64 埋め込み済）

## 例 2: 特定章のみ翻訳

```
Section 3 (Methodology) と Section 4 (Use Case) だけ訳して: paper.pdf
```

Claude は `extracted_text.md` を読んでから、該当章のみ処理します。

## 例 3: 既存翻訳の差し替え

```
translated.md の Section 2 の訳がおかしい。「attention」を「注意機構」にして全体を直して
```

Claude が `translated.md` を編集し、`to_html.py` で HTML を再生成します。

## 例 4: 検証エラーからの復旧

```
validator で C10 エラーが出たので Figure 10 の並び順を直して
```

Claude が `figure_plan.json` を参照して、`translated.md` の該当ブロックを修正。

## 例 5: 複数論文のバッチ翻訳

Claude に順次渡せば OK:

```
以下の 3 本を順に訳して:
- papers/paper-1.pdf
- papers/paper-2.pdf
- papers/paper-3.pdf
```

各論文ごとに `.paper-translator/outputs/<slug>/` が作成されます。

## 配布フォーマット

訳した HTML を他人に渡す場合、`translated.html` だけを送れば OK（図・CSS・目次すべて内包されています）。
