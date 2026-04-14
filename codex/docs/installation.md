# インストール（Codex 版）

## 前提

- OpenAI **Codex** CLI（最新版）
- Python 3.10 以上
- Git（リポジトリ clone 用）

## Step 1: Python パッケージ

### 必須
```bash
pip install pymupdf markdown pymdown-extensions
```

### 任意
- `pandoc`: HTML / PDF 出力の品質向上
- `lualatex`: PDF 直接出力

## Step 2: リポジトリ取得

```bash
git clone https://github.com/ryotaro0213/paper-translator.git ~/paper-translator
```

好きな場所に置いて構いません。以降 `~/paper-translator` を例とします。

## Step 3: インストールモードを選択

### モード A: project — 現在のプロジェクトに配置

プロジェクトルートで:
```bash
bash ~/paper-translator/codex/install.sh project
```

効果:
- `./AGENTS.md` をプロジェクトにコピー（Codex がこのファイルを読む）
- `./.paper-translator.env` に `PAPER_TRANSLATOR_ROOT` / `PYTHONIOENCODING` の export を記録

使う前にこのシェルで:
```bash
source ./.paper-translator.env
```

**利点**: プロジェクト単位で on/off でき、切り替えが明示的
**欠点**: 毎回 source する必要がある（shell rc に入れれば不要）

### モード B: global — ユーザー全体で有効化

```bash
bash ~/paper-translator/codex/install.sh global
```

効果:
- `~/.codex/paper-translator-AGENTS.md` に AGENTS.md をコピー
- `~/.codex/config.toml` に下記スニペットを追記:
  ```toml
  [[instructions]]
  path = "~/.codex/paper-translator-AGENTS.md"
  ```
- `~/.zshrc` / `~/.bashrc` / `~/.profile` に `PAPER_TRANSLATOR_ROOT` の export を追記

**利点**: どのプロジェクトでも `translate <pdf>` が動く
**欠点**: Codex 起動時に常に AGENTS.md が読まれる（他の指示と混ざる場合は project モード推奨）

### インタラクティブ選択

引数なしで実行するとメニューが出ます:
```bash
bash ~/paper-translator/codex/install.sh
```

## Step 4: 動作確認

```bash
# プロジェクトモードの場合
source ./.paper-translator.env

# Codex 起動
codex

# プロンプト例
> translate sample.pdf
```

Codex が PDF を開いて、slug 候補提示 → 翻訳開始 の流れに入れば成功です。

## Windows 固有の注意

### 文字化け（cp932 問題）
インストーラが自動で `PYTHONIOENCODING=utf-8` を env に含めますが、手動で Python を叩くときは必ず:
```bash
PYTHONIOENCODING=utf-8 python script.py
```

### Bash 必須
`install.bat` は Git Bash / WSL の `bash` を呼ぶラッパーです。どちらか必要:
- Git for Windows（推奨）: https://git-scm.com/
- WSL: `wsl --install`

### パス
`PAPER_TRANSLATOR_ROOT` は Unix スタイル（`C:/Users/...`）または絶対パスで設定します。install.sh が自動で解決します。

## アンインストール

### project モードで入れた場合
```bash
rm ./AGENTS.md ./.paper-translator.env
```

### global モードで入れた場合
```bash
# config.toml から paper-translator ブロックを手で削除
nano ~/.codex/config.toml

# 指示ファイル削除
rm ~/.codex/paper-translator-AGENTS.md

# shell rc から PAPER_TRANSLATOR_ROOT 行を手で削除
```

## アップデート

```bash
cd ~/paper-translator
git pull
# project モードの場合は AGENTS.md を再コピー
bash codex/install.sh project
# global モードの場合は再実行すれば自動で上書き
bash codex/install.sh global
```
