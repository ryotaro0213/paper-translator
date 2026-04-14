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

## Quick Start

```bash
# 1. Create a project folder and move into it (any name)
mkdir my-papers && cd my-papers

# 2. Clone the repo into the project folder
git clone https://github.com/ryotaro0213/paper-translator.git

# 3. Install Python dependencies
pip install pymupdf markdown pymdown-extensions

# 4. Install — copies AGENTS.md + scripts/ into current folder
bash paper-translator/codex/install.sh project
```

Open this folder in VS Code, and tell Codex:

```
translate ./papers/sample.pdf
```

That's it. Scripts are copied locally as `./scripts/`, so **no environment
variables or folder-name dependencies**.

> The clone location and folder name are arbitrary. `install.sh` copies
> everything needed into your working directory.

## Install modes

| Mode | What gets installed | Scope | VS Code compatibility |
|---|---|---|---|
| **project** (recommended) | `AGENTS.md` + `scripts/` in current dir | This project only | Best |
| **global** | Files in `~/.codex/` + config.toml entry | All projects | OK |

```bash
bash /path/to/paper-translator/codex/install.sh project   # recommended
bash /path/to/paper-translator/codex/install.sh global     # advanced
bash /path/to/paper-translator/codex/install.sh            # interactive
```

## Directory layout once installed (project mode)

```
your-project/                           # any folder name
├── AGENTS.md                           # Codex instructions
├── scripts/                            # copied pipeline scripts
│   ├── extract.py
│   ├── plan_figures.py
│   ├── compose_figures.py
│   ├── validate_figures.py
│   ├── to_html.py
│   ├── view.sh
│   └── paper.css
├── .paper-translator.env               # optional env snippet
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
└── ...your own files
```

## Documentation

- [docs/installation.md](docs/installation.md) — full installation guide
- [docs/usage.md](docs/usage.md) — command examples, partial translation, re-runs
- [docs/architecture.md](docs/architecture.md) — pipeline overview
- [../docs/troubleshooting.md](../docs/troubleshooting.md) — common issues
- [AGENTS.md](AGENTS.md) — the actual instruction file Codex reads

## Parity with the Claude Code edition

Both editions run the same Python pipeline. Differences:

| Aspect             | Claude Code                             | Codex                                  |
| ------------------ | --------------------------------------- | -------------------------------------- |
| Entry point        | `/translate-paper <pdf>` slash command  | natural language via AGENTS.md         |
| Installation       | `/plugin marketplace add` or manual     | `bash codex/install.sh project`        |
| Script location    | `${CLAUDE_PLUGIN_ROOT}/scripts/`        | `./scripts/` (copied locally)          |
| User prompts       | `AskUserQuestion` tool                  | Codex's native question mechanism      |

Output format, validation logic, and figure-capture strategy are identical.

## License

MIT — see [../LICENSE](../LICENSE).
