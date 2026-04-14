# Paper Translator — Codex edition

OpenAI **Codex** integration of the Paper Translator pipeline. Same core
scripts as the Claude Code plugin; only the entry point differs.

## What Codex users get

- Translate any English research-paper PDF into Japanese with a single
  natural-language prompt (`translate paper.pdf`)
- Figures and tables keep their original layout — each is cropped
  directly from the source PDF page as a single image
- Automatic placement validation (10 checks) before the HTML is built
- Choice of viewer afterwards: HTML in browser / VSCode preview / PDF

## 🎯 一番早い流れ（VS Code + Codex 拡張）

```bash
# 1. リポジトリを好きな場所に取得（フォルダ名は任意）
git clone https://github.com/ryotaro0213/paper-translator.git
# 例: カレントディレクトリに paper-translator/ が作られる
# 別名で置きたい場合:
#   git clone https://github.com/ryotaro0213/paper-translator.git my-tools/translator

# 2. Python 依存を入れる（初回のみ）
pip install pymupdf markdown pymdown-extensions

# 3. 使いたいプロジェクトに AGENTS.md を配置
cd ~/my-project/
bash /path/to/wherever/you/cloned/codex/install.sh project
#    ↑ clone 先の codex/install.sh を呼ぶだけでよい
```

あとは **VS Code でこのプロジェクトを開き**、Codex 拡張のチャットで:

```
translate ./papers/sample.pdf
```

と言うだけ。`AGENTS.md` に**絶対パスが直接書き込まれている**ので、環境変数の設定は不要です。

> ℹ️ **Clone 先フォルダ名は自由です**。`install.sh` は自分自身の場所から相対的にパスを解決するので、どこに clone しても正しく AGENTS.md が生成されます。
>
> ℹ️ Codex CLI 派の人も手順は同じ。`codex` コマンドをプロジェクトディレクトリで起動してください。

Codex は以下を自動で行います:

1. PDF を読み取り、slug 候補を提示 → 確認
2. 図・テキストを抽出し、配置を計画
3. Figure / Table を原 PDF から領域切り出しして合成
4. セクション単位で翻訳を `.paper-translator/outputs/<slug>/translated.md` に追記
5. 配置検証（10 項目）
6. HTML 生成 → 選んだ方法で閲覧

## インストールモード

| モード | AGENTS.md の場所 | 有効範囲 | VS Code 拡張との相性 |
|---|---|---|---|
| **project** ⭐ 推奨 | プロジェクト直下 | そのプロジェクトだけ | ◎ |
| **global** | `~/.codex/` | 全プロジェクト | △ |

迷ったら `project` を選んでください。詳細: [docs/installation.md](docs/installation.md)

## Directory layout once installed

```
your-project/
├── AGENTS.md                           # (copied here in 'project' mode)
├── .paper-translator/
│   └── outputs/
│       └── <slug>/
│           ├── original.pdf
│           ├── translated.md
│           ├── translated.html
│           ├── review.md
│           ├── figure_validation.md
│           ├── figure_plan.json
│           └── figures/
│               ├── figure-NN.png       # composed (main references)
│               ├── table-NN.png
│               ├── fig-NN.png          # individual panels (fallback)
│               └── page-NNN.png        # per-page renders
└── …your own files
```

The scripts themselves stay in `$PAPER_TRANSLATOR_ROOT/scripts/` and are
shared between the Claude Code and Codex editions.

## Environment variables

| Variable                | Purpose                                      |
| ----------------------- | -------------------------------------------- |
| `PAPER_TRANSLATOR_ROOT` | absolute path to the paper-translator root   |
| `PYTHONIOENCODING`      | must be `utf-8` on Windows to avoid cp932    |

`install.sh` writes a small `.env` snippet and prints export instructions.

## Documentation

- [docs/installation.md](docs/installation.md) — full installation paths
- [docs/usage.md](docs/usage.md) — command examples, part-only translation,
  re-runs, custom terminology
- [docs/architecture.md](docs/architecture.md) — pipeline overview
  (shared with the Claude Code edition)
- [../docs/troubleshooting.md](../docs/troubleshooting.md) — common issues
- [AGENTS.md](AGENTS.md) — the actual instruction file Codex reads

## Parity with the Claude Code edition

Both editions run the same Python pipeline. Differences:

| Aspect             | Claude Code                        | Codex                                  |
| ------------------ | ---------------------------------- | -------------------------------------- |
| Entry point        | `/translate-paper <pdf>` slash command | natural language trigger via AGENTS.md |
| Plugin manifest    | `.claude-plugin/plugin.json`       | `AGENTS.md` in project or global config |
| Installation       | `~/.claude/plugins/`               | copy AGENTS.md + set env var           |
| User prompts       | `AskUserQuestion` tool             | Codex's native question mechanism      |
| Script location    | `${CLAUDE_PLUGIN_ROOT}/scripts/`   | `$PAPER_TRANSLATOR_ROOT/scripts/`      |

Output format, validation logic, and figure-capture strategy are identical.

## License

MIT — see [../LICENSE](../LICENSE).
