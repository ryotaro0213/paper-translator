# Paper Translator — Codex Instructions

This file tells OpenAI **Codex** how to translate English research-paper
PDFs into Japanese while preserving the original figure and table layout.

When active, Codex will respond to prompts like:

- `translate paper.pdf`
- `この論文を翻訳して: ./papers/foo.pdf`
- `Translate the attached PDF, preserving figures`

by running the pipeline described below.

## Environment variables

The scripts live under a known directory. One of the following must be set:

- `PAPER_TRANSLATOR_ROOT` — absolute path to the paper-translator checkout
  (contains `scripts/`)
- Fallback: if this file sits at `${PAPER_TRANSLATOR_ROOT}/codex/AGENTS.md`,
  Codex can infer the root from the AGENTS.md path

All shell commands must prefix Python calls with `PYTHONIOENCODING=utf-8`
on Windows to avoid `cp932` encode errors.

## Output location

```
<current working dir>/.paper-translator/outputs/<slug>/
```

`<slug>` follows `author-year-short-title` (kebab-case). Confirm with the
user before creating directories.

## Pipeline steps (execute in order)

### Step 1 — Prerequisite check

```bash
python -c "import fitz, markdown" \
  || echo "Missing: run 'pip install pymupdf markdown pymdown-extensions'"
```

Abort with a friendly message if dependencies are missing.

### Step 2 — Inspect PDF and pick a slug

```bash
PYTHONIOENCODING=utf-8 python - <<'PY' "$PDF"
import fitz, sys
d = fitz.open(sys.argv[1])
print("title:", d.metadata.get("title",""))
print("author:", d.metadata.get("author","")[:80])
print("pages:", d.page_count)
PY
```

Propose 1–3 slug candidates and ask the user to pick (or supply their own).

### Step 3 — Create output directory and copy the source PDF

```bash
OUT=".paper-translator/outputs/<slug>"
mkdir -p "$OUT/figures"
cp "$PDF" "$OUT/original.pdf"
```

### Step 4 — Extract figures and text

```bash
PYTHONIOENCODING=utf-8 python "$PAPER_TRANSLATOR_ROOT/scripts/extract.py" \
  "$PDF" "$OUT"
```

Produces:

- `extracted_text.md` — paginated text dump
- `figures_index.json` — per-panel metadata (page, bbox, caption hint)
- `figures/fig-NN.png` — individual embedded images
- `figures/page-NNN.png` — full-page renders for visual cross-check

### Step 5 — License check

Read the first ~1500 characters of `extracted_text.md` and look for:

- `CC BY` / `Creative Commons` / `open access` / `MDPI` →
  translation and redistribution OK (attribution required)
- Anything else → ask the user to confirm personal-use scope

Record the verdict in `review.md` later.

### Step 6 — Build figure plan and compose Figure/Table images

```bash
PYTHONIOENCODING=utf-8 python "$PAPER_TRANSLATOR_ROOT/scripts/plan_figures.py" "$OUT"
PYTHONIOENCODING=utf-8 python "$PAPER_TRANSLATOR_ROOT/scripts/compose_figures.py" "$OUT"
```

Outputs:

- `figure_plan.json` — reading-order-sorted panels with anchor paragraphs
- `figures/figure-NN.png` — one image per captioned Figure, cropped
  directly from the source PDF page
- `figures/table-NN.png` — same for Tables that consist of an image grid

**Use these composed images for layout fidelity.** Do not reassemble
sub-panels with CSS — that path is abandoned in favour of PDF cropping.

### Step 7 — Structure overview

Read `extracted_text.md` and enumerate section headings (`1. Introduction`,
`2. Related Work`, …). For long papers (>30 pages) first produce a sample
translation of the Abstract + Introduction and ask the user to confirm
tone/terminology before continuing.

### Step 8 — Translate section by section

Append to `<OUT>/translated.md`. Rules:

- Technical terms: first occurrence as `日本語訳 (English)`, then Japanese only
- Proper nouns / model names / software names / function names: keep as-is
- Numbers, SI units, equations: keep verbatim (LaTeX `$$...$$` OK for math)
- Figure / Table references: `図 N` / `表 N`, original in parentheses at first mention
- Insert each figure as a single composed image at the anchor paragraph:

  ```markdown
  ![Figure N. caption](figures/figure-NN.png)
  ```

  **Do not** embed the per-panel `fig-NN.png` files — layout is preserved
  by the composed images only.
- References list: leave as English; preserve `[N]` citations in the body.

### Step 9 — Validate figure placement (blocking)

```bash
PYTHONIOENCODING=utf-8 python "$PAPER_TRANSLATOR_ROOT/scripts/validate_figures.py" "$OUT"
```

Checks C1–C10 (coverage, order, caption match, duplication, sub-panel
clustering, orphan refs, unknown/unused images, alt-text mismatch,
sub-panel order). Exit codes:

- `0` → clean, proceed
- `1` → warnings only; show them and ask the user whether to continue
- `2` → errors; fix `translated.md` and re-run. For unclear cases, read
  the relevant `page-NNN.png` with the image-read tool to cross-check.

### Step 10 — Review log

Write `<OUT>/review.md` with:

- Completed sections
- Glossary table (English → Japanese) used for this paper
- Numeric / proper-noun retention spot-check
- Any judgement calls (paraphrasing, term choices)
- Open questions for the user

### Step 11 — Pick a viewer

Ask the user (via whatever UI mechanism Codex offers) to pick:

1. **HTML (browser)** — recommended; single portable file
2. **VSCode preview** — for editing afterwards
3. **PDF** — pandoc + LaTeX required
4. **Do not open** — just print the output path

Dispatch via:

```bash
bash "$PAPER_TRANSLATOR_ROOT/scripts/view.sh" "$OUT" html     # vscode | pdf
```

`view.sh` falls back to a Python HTML builder when pandoc is absent,
and degrades gracefully when LaTeX is unavailable.

### Step 12 — Final report

Summarize:

- output directory path
- sections translated / figure count / table count
- validator result
- viewer that was opened (or path to open manually)

## Error handling cheat-sheet

| Symptom                               | Likely cause          | Action                                             |
| ------------------------------------- | --------------------- | -------------------------------------------------- |
| `FileNotFoundError` in compose step   | PDF not copied to OUT | Copy `original.pdf` into `$OUT` (step 3)           |
| Empty text extraction                 | Scanned PDF           | Suggest `pytesseract`; abort gracefully            |
| `UnicodeEncodeError: cp932`           | Windows Python        | Prefix with `PYTHONIOENCODING=utf-8`               |
| Figure panels missing (C8 warning)    | Page-dominant logic   | Inspect `figures_index.json`, add panels manually  |
| `code` not found                      | VSCode CLI not in PATH | Fall back to opening `.md` with the default editor |
| `pandoc` not found                    | pandoc missing        | `to_html.py` fallback activates automatically      |
| Validator exit 2 after repeated fixes | Genuine mismatch      | Read the relevant `page-NNN.png` to settle by sight |

## Conventions

- Never overwrite existing `translated.md`. Append, or create `translated.v2.md`.
- Always keep `original.pdf` untouched.
- Record all decisions in `review.md`; future sessions should be able to
  reconstruct reasoning from the logs alone.
- Do not skip the validator. Figure-placement regressions are the single
  most common failure mode for this pipeline.

## Reference material

- Architecture diagram: `../docs/architecture.md`
- Troubleshooting: `../docs/troubleshooting.md`
- Claude Code equivalent: `../commands/translate-paper.md`
  (for cross-checking parity between the two flavours)
