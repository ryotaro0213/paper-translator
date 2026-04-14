# インストール（Codex 版）

## Quick Start（VS Code + Codex 拡張ユーザー向け）

```bash
# 1. リポジトリを好きな場所に clone（フォルダ名は自由）
git clone https://github.com/ryotaro0213/paper-translator.git

# 2. 使いたいプロジェクトフォルダに移動（フォルダ名は何でもOK）
cd ~/my-project/

# 3. AGENTS.md + scripts/ をプロジェクトにインストール
bash /path/to/paper-translator/codex/install.sh project

# 4. Python の依存（初回のみ）
pip install pymupdf markdown pymdown-extensions
```

VS Code でプロジェクトフォルダを開き、Codex 拡張のチャットで:

```
translate ./papers/foo.pdf
```

と言うだけ。`scripts/` がローカルにコピーされているので、環境変数の設定は不要です。

> Clone 先フォルダ名・場所は任意です。`install.sh` は必要なファイルをすべて
> カレントディレクトリにコピーするので、どこに clone しても問題ありません。

---

## 自分の Codex はどれ？

| Codex の種類 | 検出方法 | 対応 |
|---|---|---|
| **Codex CLI**（ターミナル）| `codex --version` が通る | OK |
| **VS Code Codex 拡張** | 拡張マーケットで "Codex" を確認 | OK |
| **Codex IDE 拡張（他エディタ）** | JetBrains / Cursor などの拡張 | OK |
| **ChatGPT の Codex（Web）** | chatgpt.com/codex | 非対応 |
| **GitHub Copilot** | 別製品 | 非対応 |

> "AGENTS.md を読んでシェルコマンドを実行できる" なら対応。"ブラウザ内で完結する" なら非対応。

---

## インストールモード

### モード比較

| | **project モード** (推奨) | **global モード** |
|---|---|---|
| インストール先 | プロジェクト直下 | `~/.codex/` |
| 有効範囲 | そのプロジェクトだけ | 全プロジェクト |
| scripts の場所 | `./scripts/`（ローカルコピー） | `~/.codex/paper-translator-scripts/` |
| 環境変数 | 不要 | 不要（パスはbake-in済み） |
| VS Code 拡張との相性 | 最適 | OK |

**迷ったら project モード**を選んでください。

### project モード（推奨）

```bash
cd ~/my-project
bash <CLONE_PATH>/codex/install.sh project
```

何が起こるか:

1. `./AGENTS.md` がコピーされる
2. `./scripts/` にパイプラインスクリプトがコピーされる
3. `./.paper-translator.env`（任意・ターミナル用）が作成される
4. Python 依存パッケージの有無を自動チェック

### global モード（上級者向け）

```bash
bash <CLONE_PATH>/codex/install.sh global
```

何が起こるか:

1. `~/.codex/paper-translator-AGENTS.md` が作成される（絶対パス埋め込み済み）
2. `~/.codex/paper-translator-scripts/` にスクリプトがコピーされる
3. `~/.codex/config.toml` に `[[instructions]]` エントリが追記される

### インタラクティブ選択

```bash
bash <CLONE_PATH>/codex/install.sh    # 引数なしで対話メニュー
```

---

## Python 依存

必須:

```bash
pip install pymupdf markdown pymdown-extensions
```

オプション:

| ツール | Windows | macOS | Linux | 役割 |
|---|---|---|---|---|
| `pandoc` | `winget install pandoc` | `brew install pandoc` | `apt install pandoc` | 高品質な HTML 生成 |
| `lualatex` | MiKTeX | MacTeX | `apt install texlive-luatex texlive-lang-japanese` | PDF 直接出力 |

なくても動きます（フォールバックあり）。

---

## 動作確認

### 1. インストール内容の確認

```bash
ls AGENTS.md scripts/
```

`AGENTS.md` と `scripts/` ディレクトリが存在すれば成功。

### 2. Python パイプラインの確認

```bash
python -c "import fitz, markdown, pymdownx" && echo "OK"
```

### 3. 実際の翻訳

Codex を起動して:

```
translate sample.pdf
```

---

## Windows 固有の注意

### Git for Windows（必須）

`install.sh` は Bash スクリプトなので以下のいずれかが必要:

- **Git for Windows**（推奨）: https://git-scm.com/
- **WSL**: `wsl --install`

`install.bat` は Git Bash を呼ぶラッパーなので、PowerShell や CMD からでも:

```bat
install.bat project
```

### 文字化け（cp932 問題）

`AGENTS.md` 内のコマンドには `PYTHONIOENCODING=utf-8` が付加済みです。

---

## アップデート

```bash
cd <CLONE_PATH>
git pull

# project モードなら各プロジェクトで再実行
cd ~/my-project
bash <CLONE_PATH>/codex/install.sh project
```

## アンインストール

### project モード

```bash
rm -rf AGENTS.md scripts/ .paper-translator.env .paper-translator/
```

### global モード

```bash
rm -rf ~/.codex/paper-translator-AGENTS.md ~/.codex/paper-translator-scripts/
# ~/.codex/config.toml から paper-translator ブロックを手動削除
```
