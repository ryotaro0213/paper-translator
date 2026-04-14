# インストール

## 前提条件

- Claude Code（最新版）
- Python 3.10 以上

## Step 1: Python パッケージ

### 必須
```bash
pip install pymupdf markdown pymdown-extensions
```

| パッケージ | 用途 |
|---|---|
| `pymupdf` (`fitz`) | PDF からテキスト・図・ページレンダーを抽出 |
| `markdown` | Python フォールバック HTML 生成（pandoc 不在時） |
| `pymdown-extensions` | 目次・コードブロック・テーブルの強化 |

### オプション（推奨）

#### pandoc（HTML/PDF 出力の品質向上）
- Windows: `winget install pandoc`
- macOS: `brew install pandoc`
- Linux: `apt install pandoc` または `dnf install pandoc`

#### LaTeX（PDF 直接出力）
- Windows: MiKTeX (`choco install miktex`) または TeX Live
- macOS: `brew install --cask mactex`
- Linux: `apt install texlive-luatex texlive-lang-japanese`

LaTeX 未導入でも、HTML を生成してブラウザで「PDF として保存」する代替経路が動きます。

## Step 2: プラグイン本体

### 方法 A: Plugin Marketplace（推奨）

Claude Code 内で以下を実行するだけ:

```
/plugin marketplace add ryotaro0213/paper-translator
/plugin install paper-translator@paper-translator
```

フォルダ名やインストール場所に依存しません。

### 方法 B: 手動インストール（install.sh）

```bash
git clone https://github.com/ryotaro0213/paper-translator.git
cd paper-translator
bash install.sh          # copy モード（デフォルト）
bash install.sh link     # symlink モード（開発用）
```

### 方法 C: 手動配置

1. このリポジトリの `plugins/paper-translator/` フォルダをダウンロード
2. `~/.claude/plugins/paper-translator/` に配置

## Step 3: 動作確認

Claude Code を起動し:

```
/translate-paper --help
```

または、サンプル PDF があれば:

```
/translate-paper sample.pdf
```

正常にインストールされていれば、`AskUserQuestion` で slug 候補を確認するダイアログが表示されます。

## Windows 固有の注意

### 文字化け対策

Python スクリプト実行時に必ず:
```bash
PYTHONIOENCODING=utf-8 python script.py
```

これがないと CP932 環境で `UnicodeEncodeError` が発生します。`/translate-paper` 内ではこれを自動で付けています。

### Bash の使用

`view.sh` は Bash スクリプトなので Git Bash / WSL で動作します。Windows ネイティブ cmd では Python スクリプトを直接呼んでください。

### パス区切り

スクリプトは `pathlib` を使うのでクロスプラットフォームですが、シェル上では:
- 推奨: `C:/Users/Nozawa/...`（フォワードスラッシュ）
- 可: `C:\Users\Nozawa\...`（バックスラッシュ、引用必須）

## アンインストール

```bash
rm -rf ~/.claude/plugins/paper-translator
```

`.paper-translator/` 配下の出力ファイルは各プロジェクトディレクトリにあるので、必要に応じて個別削除してください。
