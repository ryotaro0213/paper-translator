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

## Quick start

### 1. Install Python dependencies

```bash
pip install pymupdf markdown pymdown-extensions
```

Optional (higher-quality HTML/PDF output):

```bash
# Windows
winget install pandoc
# macOS
brew install pandoc
# For PDF output, also install LaTeX (MiKTeX / TeX Live / MacTeX)
```

### 2. Install the paper-translator files

```bash
git clone https://github.com/ryotaro0213/paper-translator.git ~/paper-translator
cd ~/paper-translator/codex
bash install.sh           # copy AGENTS.md to current project + set PAPER_TRANSLATOR_ROOT
```

`install.sh` takes two modes:

- `bash install.sh project`  — copy `AGENTS.md` into the current project
- `bash install.sh global`   — append `AGENTS.md` path to `~/.codex/config.toml`

Without arguments it asks interactively.

### 3. Use it

Start Codex in your project directory and say:

```
translate ./papers/sample.pdf
```

Codex will:

1. Inspect the PDF, propose a slug, ask for confirmation
2. Extract figures / text, plan the layout, compose per-Figure images
3. Translate section by section into `.paper-translator/outputs/<slug>/translated.md`
4. Run the placement validator
5. Build the final HTML
6. Open it the way you asked

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
