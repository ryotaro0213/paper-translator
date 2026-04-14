# インストール（Codex 版）

## 🎯 一番早い流れ（VS Code + Codex 拡張ユーザー向け）

VS Code に **Codex 拡張**が入っていれば、これだけで使えます:

```bash
# 1. リポジトリを好きな場所に clone（フォルダ名は自由）
git clone https://github.com/ryotaro0213/paper-translator.git
# → カレントに paper-translator/ が作られる

# 別名で置く例（どれでも OK）
#   git clone https://…/paper-translator.git tools/translator
#   git clone https://…/paper-translator.git ~/Downloads/my-translator
#   git clone https://…/paper-translator.git "C:/Users/you/whatever you like"

# 2. 使いたいプロジェクトに移動
cd ~/my-project/

# 3. プロジェクトに AGENTS.md を配置（clone した場所の install.sh を指す）
bash /path/to/clone/codex/install.sh project

# 4. Python の依存（初回のみ）
pip install pymupdf markdown pymdown-extensions
```

あとは **VS Code でプロジェクトフォルダを開き**、Codex 拡張のチャットで:

```
translate ./papers/foo.pdf
```

と言うだけ。`AGENTS.md` に**絶対パスが直接書き込まれている**ので、環境変数の設定は不要です。

> ℹ️ **Clone 先フォルダ名・場所は任意です**。`install.sh` は自分のファイルパスから相対的にルートを計算するので、どこに置いても正しい絶対パスを埋め込んだ `AGENTS.md` が生成されます。
>
> ℹ️ VS Code 拡張は開いているワークスペースの `AGENTS.md` を自動で読みます。プロジェクトモードで入れておけば「開く → 使う」の 2 ステップで完了します。

### 「`/path/to/clone/codex/install.sh`」って何を書くの？

「リポジトリを clone した先の `codex/install.sh`」です。具体例:

| clone 先 | 実行するコマンド |
|---|---|
| `git clone … paper-translator` （デフォルト） | `bash paper-translator/codex/install.sh project` |
| `git clone … ~/Tools/translator` | `bash ~/Tools/translator/codex/install.sh project` |
| `git clone … /opt/paper-translator` | `bash /opt/paper-translator/codex/install.sh project` |
| Windows: `C:/Users/you/tools/pt` | `bash C:/Users/you/tools/pt/codex/install.sh project` |

シェルの Tab 補完を使えば確実に書けます。

---

## 自分の Codex はどれ？

| Codex の種類 | 検出方法 | このプラグインの使い方 |
|---|---|---|
| **Codex CLI**（ターミナル）| `codex --version` が通る | CLI ／ VS Code 拡張と同じ手順で OK |
| **VS Code Codex 拡張** | 拡張マーケットで "Codex" を確認 | 🎯 一番早い流れ を参照 |
| **Codex IDE 拡張（他エディタ）** | JetBrains / Cursor などの拡張 | 同じく AGENTS.md が読まれるので project モードで動く |
| **ChatGPT の Codex（Web）** | chatgpt.com/codex | ❌ ローカルファイル操作ができないため非対応 |
| **GitHub Copilot** | 別製品（Codex モデル非依存） | ❌ AGENTS.md を読まないため非対応 |

> 🔎 **判定のコツ**: "AGENTS.md を読んでシェルコマンドを実行できる" なら対応。"ブラウザ内で完結する" なら非対応。

---

## 📦 インストール 2 モードの選び方

### モード比較

| | **project モード** ⭐ 推奨 | **global モード** |
|---|---|---|
| AGENTS.md の場所 | プロジェクト直下 | `~/.codex/` |
| 有効範囲 | そのプロジェクトだけ | 全プロジェクト |
| 他の AGENTS.md との衝突 | なし（プロジェクト毎） | 他の指示と混ざる可能性あり |
| 初期設定 | `bash install.sh project` | `bash install.sh global` |
| VS Code 拡張との相性 | ◎（開けば自動で読まれる）| △（プロジェクトの AGENTS.md が優先される可能性あり） |

**迷ったら project モード**を選んでください。VS Code 拡張を使う人には特にこちらが向いています。

### project モード（推奨）

```bash
cd ~/my-project                                  # 翻訳結果を置きたいプロジェクト
bash <CLONE_PATH>/codex/install.sh project       # <CLONE_PATH> は clone した場所
```

何が起こるか:

1. `./AGENTS.md` が作成される（絶対パスが**直接埋め込み済み**）
2. `./.paper-translator.env`（任意・ターミナル用）が作成される
3. Python 依存パッケージの有無を自動チェックして報告

VS Code でこのフォルダを開けば、Codex 拡張が `AGENTS.md` を読んですぐ使えます。

### global モード（上級者向け）

```bash
bash <CLONE_PATH>/codex/install.sh global
```

何が起こるか:

1. `~/.codex/paper-translator-AGENTS.md` が作成される（絶対パス埋め込み済み）
2. `~/.codex/config.toml` に下記が自動追記される:
   ```toml
   [[instructions]]
   path = "~/.codex/paper-translator-AGENTS.md"
   ```
3. `~/.zshrc` or `~/.bashrc` に `PAPER_TRANSLATOR_ROOT` の export が追記される

これで、どのプロジェクトからでも Codex に `translate foo.pdf` と言えば動きます。

**注意**: 他の AGENTS.md や Codex 指示と共存する時、優先順位や衝突に気をつけてください。

### インタラクティブ選択

モードを後から選びたいときは引数なし実行:

```bash
bash <CLONE_PATH>/codex/install.sh
```

`[1] project / [2] global` のメニューが出ます。

### 💡 毎回フルパスを書くのが面倒な場合

エイリアスを `~/.bashrc` / `~/.zshrc` に追加しておくと楽です:

```bash
alias pt-install='bash /path/to/your/paper-translator/codex/install.sh'
```

以降は:
```bash
pt-install project   # or: pt-install global
```

---

## 🐍 Python 依存

必須:

```bash
pip install pymupdf markdown pymdown-extensions
```

インストーラが自動でチェックし、足りないパッケージを表示します。

任意（出力品質を上げたい場合）:

| ツール | Windows | macOS | Linux | 役割 |
|---|---|---|---|---|
| `pandoc` | `winget install pandoc` | `brew install pandoc` | `apt install pandoc` | 高品質な HTML 生成 |
| `lualatex` | MiKTeX | MacTeX | `apt install texlive-luatex texlive-lang-japanese` | PDF 直接出力 |

これらが無くても動きます:
- **pandoc なし** → Python フォールバック (`to_html.py`) で HTML を生成
- **LaTeX なし** → HTML 生成後に「ブラウザで PDF 保存」を案内

---

## ✅ 動作確認

インストール後、以下で確認:

### 1. AGENTS.md の内容確認

```bash
head -20 AGENTS.md
```

冒頭に次のようなブロックがあれば成功:

```markdown
## Configuration
- **PAPER_TRANSLATOR_ROOT**: `/Users/you/paper-translator`
- **Scripts directory**: `/Users/you/paper-translator/scripts`
```

絶対パスが書き込まれていればパス解決は完了。

### 2. Python パイプラインの dry run

```bash
python -c "import fitz, markdown, pymdownx" && echo "OK: all deps present"
```

### 3. 実際の翻訳

Codex を起動して:

```
translate sample.pdf
```

出力:

- slug 候補が提示される
- 確認後、`.paper-translator/outputs/<slug>/` に抽出・翻訳・検証が流れる
- 最後に閲覧方法（HTML / VSCode / PDF / 開かない）を聞かれる

---

## 🪟 Windows 固有の注意

### Git for Windows（必須）

`install.sh` は Bash スクリプトなので、以下のいずれかが必要です:

- **Git for Windows**（推奨）: https://git-scm.com/ — `git bash` がついてくる
- **WSL**: `wsl --install`

`install.bat` は Git Bash を呼ぶラッパーなので、PowerShell や CMD からでも:

```bat
install.bat project
```

で動きます。

### 文字化け（cp932 問題）

インストーラが自動で `PYTHONIOENCODING=utf-8` を `.paper-translator.env` に書き込みます。手動で Python スクリプトを叩く時は必ず:

```bash
PYTHONIOENCODING=utf-8 python script.py
```

`AGENTS.md` には既に付加済みなので、Codex 経由なら気にする必要はありません。

### パス表記

AGENTS.md には **絶対パス**（例: `C:/Users/you/paper-translator`）がインストーラによって書き込まれます。フォワードスラッシュで統一されているので、Bash と PowerShell 両方で動きます。

---

## 🔧 トラブルシューティング

### 「AGENTS.md が見つからない」と Codex が言う

- **project モードの場合**: ファイルのあるフォルダで Codex を起動しているか確認（VS Code なら正しいワークスペースを開いているか）
- **global モードの場合**: `~/.codex/config.toml` に `[[instructions]]` エントリがあるか確認

```bash
cat ~/.codex/config.toml | grep -A2 paper-translator
```

### VS Code 拡張で反応しない

1. VS Code を一度再起動
2. `File > Open Folder...` で AGENTS.md があるフォルダを開く（サブフォルダからではなく、`AGENTS.md` がある階層を開く）
3. Codex 拡張のチャットで適当な質問をして、`AGENTS.md` を認識しているか確認

### 「PAPER_TRANSLATOR_ROOT が undefined」エラー

インストーラで書き込まれた AGENTS.md には絶対パスが埋め込み済みなので、このエラーは通常出ません。もし出る場合:

```bash
# AGENTS.md の Configuration ブロックを確認
head -20 AGENTS.md
```

`$PAPER_TRANSLATOR_ROOT` がそのまま残っていたら、`install.sh` を再実行してください。

### Python パッケージが見つからない

```bash
pip install --upgrade pymupdf markdown pymdown-extensions
```

仮想環境（venv）を使っている場合、その venv がアクティブな状態で install してください。

---

## 🔄 アップデート

```bash
# clone した場所で pull
cd <CLONE_PATH>
git pull

# project モードなら各プロジェクトで再実行
cd ~/my-project
bash <CLONE_PATH>/codex/install.sh project

# global モードなら 1 回だけ再実行
bash <CLONE_PATH>/codex/install.sh global
```

> 💡 clone 先を覚えておかなくても、AGENTS.md の冒頭 `Configuration` ブロックに絶対パスが書かれています:
> ```bash
> head -10 AGENTS.md | grep PAPER_TRANSLATOR_ROOT
> ```

---

## 🗑️ アンインストール

### project モードで入れた場合

```bash
cd ~/my-project
rm AGENTS.md .paper-translator.env
# 翻訳出力を消す場合
rm -rf .paper-translator
```

### global モードで入れた場合

```bash
# 1. AGENTS.md 本体を削除
rm ~/.codex/paper-translator-AGENTS.md

# 2. ~/.codex/config.toml から paper-translator ブロックを手動削除
#    (# --- paper-translator (auto-added) --- から # --- /paper-translator --- まで)
nano ~/.codex/config.toml

# 3. ~/.zshrc もしくは ~/.bashrc から PAPER_TRANSLATOR_ROOT 行を削除
nano ~/.bashrc
```

---

## 💡 Tips

### 複数のプロジェクトで使いたい

project モードを各プロジェクトで実行するのが簡単。`paper-translator` 本体は 1 箇所に置いておき、各 AGENTS.md は同じ絶対パスを指すので動作も同じ。

### チームで共有したい

チームリポジトリに `AGENTS.md` を commit すれば、他のメンバーも VS Code で開くだけで使えます。ただし `paper-translator` 本体のパスが環境ごとに違うので、チームメンバーに README で案内するか、各自 `install.sh project` を実行してもらうのがオススメ。

### Claude Code と併用したい

同じリポジトリに両対応の指示が入っているので、Claude Code には `commands/translate-paper.md`、Codex には `codex/AGENTS.md` が読まれます。衝突しません。
